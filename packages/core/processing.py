import uuid
import logging
from typing import List, Optional, Any

from packages.core.models import PromptDNA, CanonicalTemplate
from packages.dna_extractor import extract_dna, EmbeddingService
from packages.clustering import cluster_prompts, classify_new_prompt, detect_mutation_type
from packages.clustering.engine import compute_confidence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packages.storage.repositories import LineageRepository, PromptRepository, FamilyRepository
from packages.llm import MockLLMClient, LLMClient
# Import directly from module files to avoid circular import via packages.storage.__init__
from packages.storage.repositories import PromptRepository, FamilyRepository, LineageRepository
from packages.ingestion import normalize_text, compute_hash

logger = logging.getLogger(__name__)


def _model_to_dna(model: Any) -> PromptDNA:
    dna = extract_dna(model.original_text, model.metadata_ or {})
    dna.id = model.prompt_id
    dna.embedding = list(model.embedding_vector) if model.embedding_vector else []
    return dna


class ProcessingService:
    def __init__(
        self,
        prompt_repo: PromptRepository,
        family_repo: FamilyRepository,
        lineage_repo: Optional["LineageRepository"] = None,
        use_mock_llm: bool = False,
    ):
        self.prompt_repo = prompt_repo
        self.family_repo = family_repo
        self.lineage_repo = lineage_repo
        self.embedding_service = EmbeddingService()
        self.use_mock_llm = use_mock_llm
        
        if use_mock_llm:
            self.llm_client = MockLLMClient()
            self.fallback_client = None
        else:
            try:
                self.llm_client = LLMClient()
                self.fallback_client = MockLLMClient()
            except Exception as e:
                logger.warning(f"Failed to initialize LLMClient, using MockLLMClient: {e}")
                self.llm_client = MockLLMClient()
                self.fallback_client = None

    async def _extract_template_with_fallback(self, cluster_prompts: List[PromptDNA]) -> CanonicalTemplate:
        try:
            return await self.llm_client.extract_template(cluster_prompts)
        except Exception as e:
            logger.warning(f"LLM template extraction failed, using fallback: {e}")
            if self.fallback_client:
                return await self.fallback_client.extract_template(cluster_prompts)
            raise

    async def _generate_explanation_with_fallback(self, cluster_prompts: List[PromptDNA]) -> str:
        try:
            return await self.llm_client.generate_explanation(cluster_prompts)
        except Exception as e:
            logger.warning(f"LLM explanation generation failed, using fallback: {e}")
            if self.fallback_client:
                return await self.fallback_client.generate_explanation(cluster_prompts)
            return f"This family contains {len(cluster_prompts)} prompts with similar semantic structure."

    async def process_raw_prompt(
        self,
        raw_text: str,
        metadata: Optional[dict] = None,
    ) -> PromptDNA:
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
        saved_prompt = self.prompt_repo.create_from_dna(prompt_dna, original_text_override=raw_text)
        prompt_dna.id = saved_prompt.prompt_id
        
        if self.lineage_repo:
            classification, family_id, confidence = await self.classify_new_prompt(prompt_dna)
            if classification in ("exact_match", "variant") and family_id:
                self.prompt_repo.update_family(saved_prompt.prompt_id, family_id)
        
        return prompt_dna

    async def process_batch(self, limit: int = 100) -> dict:
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
            
            template = await self._extract_template_with_fallback(cluster_prompts)
            description = await self._generate_explanation_with_fallback(cluster_prompts)

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
        families = self.family_repo.get_all()
        if not families:
            return ("new_family", None, 0.0)

        family_data: List[tuple[str, List[PromptDNA]]] = []
        for fm in families:
            members = self.prompt_repo.get_by_family(fm.family_id)
            family_data.append((fm.family_id, [_model_to_dna(m) for m in members]))

        classification, family_id, confidence = classify_new_prompt(prompt_dna, family_data)
        
        if self.lineage_repo and classification in ("exact_match", "variant") and family_id:
            members = self.prompt_repo.get_by_family(family_id)
            if members:
                best_parent = None
                best_parent_confidence = 0.0
                
                for member in members:
                    if member.prompt_id == prompt_dna.id:
                        continue
                    member_dna = _model_to_dna(member)
                    if prompt_dna.embedding and member_dna.embedding:
                        member_confidence = compute_confidence(prompt_dna, [member_dna.embedding])
                    else:
                        member_confidence = 0.0
                    if member_confidence > best_parent_confidence:
                        best_parent_confidence = member_confidence
                        best_parent = member
                
                if best_parent:
                    mutation_type = detect_mutation_type(_model_to_dna(best_parent), prompt_dna)
                    self.lineage_repo.create_lineage(
                        parent_prompt_id=best_parent.prompt_id,
                        child_prompt_id=prompt_dna.id,
                        mutation_type=mutation_type,
                        confidence=confidence,
                    )
        
        return (classification, family_id, confidence)
