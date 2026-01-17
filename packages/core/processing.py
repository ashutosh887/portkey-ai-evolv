"""
Core processing service that orchestrates the pipeline
"""

import uuid
from typing import List, Optional, Any

from packages.core.models import PromptDNA, CanonicalTemplate
from packages.dna_extractor import extract_dna, EmbeddingService
from packages.clustering import cluster_prompts, classify_new_prompt
from packages.llm import MockLLMClient, LLMClient
from packages.storage import PromptRepository, FamilyRepository
from packages.ingestion import normalize_text, compute_hash


def _model_to_dna(model: Any) -> PromptDNA:
    """Build a PromptDNA from a PromptInstance ORM model (for batch and classify)."""
    dna = extract_dna(model.original_text, model.metadata_ or {})
    dna.id = model.prompt_id
    dna.embedding = list(model.embedding_vector) if model.embedding_vector else []
    return dna


class ProcessingService:
    """Orchestrates the prompt processing pipeline"""

    def __init__(
        self,
        prompt_repo: PromptRepository,
        family_repo: FamilyRepository,
        use_mock_llm: bool = True,
    ):
        self.prompt_repo = prompt_repo
        self.family_repo = family_repo
        self.embedding_service = EmbeddingService()
        self.llm_client = MockLLMClient() if use_mock_llm else LLMClient()

    async def process_raw_prompt(
        self,
        raw_text: str,
        metadata: Optional[dict] = None,
    ) -> PromptDNA:
        """
        Process a raw prompt: normalize, dedup by hash, extract DNA, embed, store.
        Preserves raw_text in DB when provided via original_text_override.
        """
        normalized = normalize_text(raw_text)
        prompt_hash = compute_hash(normalized)

        existing = self.prompt_repo.get_by_hash(prompt_hash)
        if existing:
            dna = extract_dna(existing.original_text, existing.metadata_ or {})
            dna.id = existing.prompt_id
            dna.embedding = list(existing.embedding_vector) if existing.embedding_vector else []
            return dna

        prompt_dna = extract_dna(normalized, metadata)
        embedding = await self.embedding_service.generate_embedding_async(normalized)
        prompt_dna.embedding = embedding
        self.prompt_repo.create_from_dna(prompt_dna, original_text_override=raw_text)
        return prompt_dna

    async def process_batch(self, limit: int = 100) -> dict:
        """
        Process pending prompts: fill missing embeddings, cluster, create families
        and templates, assign family_id to prompts.
        """
        pending = self.prompt_repo.get_pending(limit)
        if not pending:
            return {"processed": 0, "families_created": 0, "families_updated": 0}

        prompt_dnas: List[PromptDNA] = []
        for model in pending:
            if model.embedding_vector is None or (isinstance(model.embedding_vector, list) and len(model.embedding_vector) == 0):
                emb = await self.embedding_service.generate_embedding_async(model.original_text)
                self.prompt_repo.update_embedding(model.prompt_id, emb)
                model.embedding_vector = emb
            prompt_dnas.append(_model_to_dna(model))

        clusters = cluster_prompts(prompt_dnas)
        families_created = 0

        for cluster_id, prompt_ids in clusters.items():
            cluster_prompts = [p for p in prompt_dnas if p.id in prompt_ids]
            family_id = f"family-{uuid.uuid4().hex[:8]}"
            template: CanonicalTemplate = await self.llm_client.extract_template(cluster_prompts)
            description = await self.llm_client.generate_explanation(cluster_prompts)

            self.family_repo.create_family(
                family_id=family_id,
                family_name=f"Family {cluster_id}",
                description=description,
                member_count=len(prompt_ids),
                centroid_vector=None,
            )
            self.family_repo.create_template(
                family_id=family_id,
                template_text=template.text,
                slots={"variables": template.variables, "example_values": template.example_values},
                quality_score=None,
            )
            for prompt_id in prompt_ids:
                self.prompt_repo.update_family(prompt_id, family_id)
            families_created += 1

        return {
            "processed": len(pending),
            "families_created": families_created,
            "families_updated": 0,
        }

    async def classify_new_prompt(self, prompt_dna: PromptDNA) -> tuple[str, Optional[str], float]:
        """
        Classify a new prompt against existing families.
        Returns (classification, family_id, confidence).
        """
        families = self.family_repo.get_all()
        if not families:
            return ("new_family", None, 0.0)

        family_data: List[tuple[str, List[PromptDNA]]] = []
        for fm in families:
            members = self.prompt_repo.get_by_family(fm.family_id)
            family_data.append((fm.family_id, [_model_to_dna(m) for m in members]))

        classification, family_id, confidence = classify_new_prompt(prompt_dna, family_data)
        return (classification, family_id, confidence)
