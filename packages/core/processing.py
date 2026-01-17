"""
Core processing service that orchestrates the pipeline
"""

from typing import List, Optional
from packages.core.models import PromptDNA, PromptFamily, CanonicalTemplate
from packages.dna_extractor import extract_dna, EmbeddingService
from packages.clustering import cluster_prompts, classify_new_prompt
from packages.llm import MockLLMClient, LLMClient
from packages.storage import PromptRepository, FamilyRepository, LineageRepository
from packages.ingestion import normalize_text, compute_hash
import uuid
from datetime import datetime


class ProcessingService:
    """Orchestrates the prompt processing pipeline"""
    
    def __init__(
        self,
        prompt_repo: PromptRepository,
        family_repo: FamilyRepository,
        lineage_repo: LineageRepository,
        use_mock_llm: bool = True,
    ):
        self.prompt_repo = prompt_repo
        self.family_repo = family_repo
        self.lineage_repo = lineage_repo
        self.embedding_service = EmbeddingService()
        self.llm_client = MockLLMClient() if use_mock_llm else LLMClient()
    
    async def process_raw_prompt(
        self,
        raw_text: str,
        metadata: Optional[dict] = None,
    ) -> PromptDNA:
        """
        Process a raw prompt through the full pipeline
        
        Args:
            raw_text: Raw prompt text
            metadata: Optional metadata
        
        Returns:
            Processed PromptDNA
        """
        normalized = normalize_text(raw_text)
        prompt_hash = compute_hash(normalized)
        
        existing = self.prompt_repo.get_by_hash(prompt_hash)
        if existing:
            dna_dict = existing.dna_json
            return PromptDNA(**dna_dict)
        
        prompt_dna = extract_dna(normalized, metadata)
        embedding = await self.embedding_service.generate_embedding_async(normalized)
        prompt_dna.embedding = embedding
        self.prompt_repo.create(prompt_dna)
        
        return prompt_dna
    
    async def process_batch(self, limit: int = 100) -> dict:
        """
        Process a batch of pending prompts
        
        Args:
            limit: Maximum number of prompts to process
        
        Returns:
            Processing results
        """
        pending = self.prompt_repo.get_pending(limit)
        
        if not pending:
            return {"processed": 0, "families_created": 0, "families_updated": 0}
        
        prompt_dnas: List[PromptDNA] = []
        for model in pending:
            dna_dict = model.dna_json
            prompt_dna = PromptDNA(**dna_dict)
            prompt_dnas.append(prompt_dna)
        
        clusters = cluster_prompts(prompt_dnas)
        
        families_created = 0
        families_updated = 0
        
        for cluster_id, prompt_ids in clusters.items():
            cluster_prompts = [p for p in prompt_dnas if p.id in prompt_ids]
            family_id = f"family-{uuid.uuid4().hex[:8]}"
            template = await self.llm_client.extract_template(cluster_prompts)
            
            family = PromptFamily(
                id=family_id,
                name=f"Family {cluster_id}",
                description=await self.llm_client.generate_explanation(cluster_prompts),
                canonical_template=template,
                members=prompt_ids,
                member_count=len(prompt_ids),
                statistics={},
            )
            
            self.family_repo.create(family)
            families_created += 1
            
            for prompt_id in prompt_ids:
                self.prompt_repo.update_family(prompt_id, family_id)
        
        return {
            "processed": len(pending),
            "families_created": families_created,
            "families_updated": families_updated,
        }
    
    async def classify_new_prompt(self, prompt_dna: PromptDNA) -> tuple[str, Optional[str], float]:
        """
        Classify a new prompt against existing families
        
        Args:
            prompt_dna: The prompt to classify
        
        Returns:
            Tuple of (classification, family_id, confidence)
        """
        families = self.family_repo.get_all()
        
        if not families:
            return ("new_family", None, 0.0)
        
        family_data = []
        for family_model in families:
            family_prompts_models = self.prompt_repo.get_by_family(family_model.id)
            family_prompts = [
                PromptDNA(**model.dna_json) for model in family_prompts_models
            ]
            family_data.append((family_model.id, family_prompts))
        
        classification, family_id, confidence = classify_new_prompt(
            prompt_dna,
            family_data,
        )
        
        return (classification, family_id, confidence)
