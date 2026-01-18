"""
Repository pattern for database operations
"""

import uuid
from typing import Optional, List, TYPE_CHECKING, Dict
from sqlalchemy.orm import Session
from packages.storage.models import (
    PromptInstance as PromptInstanceModel,
    PromptFamily as PromptFamilyModel,
    Template as TemplateModel,
)
from packages.ingestion.normalizer import normalize_text
from datetime import datetime

if TYPE_CHECKING:
    from packages.core.models import PromptDNA, PromptInstance as PromptInstanceDomain


class PromptRepository:
    """Repository for prompt operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_from_instance(self, instance: "PromptInstanceDomain") -> PromptInstanceModel:
        """Create a new prompt record from a domain instance"""
        existing = self.get_by_id(instance.prompt_id)
        if existing:
            return existing
            
        prompt_model = PromptInstanceModel(
            prompt_id=instance.prompt_id,
            original_text=instance.original_text,
            normalized_text=getattr(instance, 'normalized_text', None) or instance.original_text.strip().lower(),
            dedup_hash=getattr(instance, 'dedup_hash', None),
            simhash=getattr(instance, 'simhash', None),
            metadata_=instance.metadata,
            created_at=instance.created_at
        )
        self.db.add(prompt_model)
        self.db.commit()
        self.db.refresh(prompt_model)
        return prompt_model

    def create_from_dna(
        self, dna: "PromptDNA", original_text_override: Optional[str] = None
    ) -> PromptInstanceModel:
        """
        Create a new prompt record from a PromptDNA (e.g. from process_raw_prompt).
        Uses original_text_override for original_text when provided (to preserve user's raw input).
        """
        existing = self.get_by_id(dna.id)
        if existing:
            return existing
        original = original_text_override if original_text_override is not None else dna.raw_text
        normalized = normalize_text(dna.raw_text)
        prompt_model = PromptInstanceModel(
            prompt_id=dna.id,
            original_text=original,
            normalized_text=normalized,
            dedup_hash=dna.hash,
            simhash=None,
            embedding_vector=dna.embedding or [],
            metadata_=dna.metadata or {},
        )
        self.db.add(prompt_model)
        self.db.commit()
        self.db.refresh(prompt_model)
        return prompt_model

    def update_embedding(self, prompt_id: str, embedding: List[float]) -> None:
        """Update the embedding vector for a prompt (e.g. when computing in batch)."""
        prompt = self.get_by_id(prompt_id)
        if prompt:
            prompt.embedding_vector = embedding
            self.db.commit()

    def get_by_id(self, prompt_id: str) -> Optional[PromptInstanceModel]:
        """Get prompt by ID"""
        return self.db.query(PromptInstanceModel).filter(PromptInstanceModel.prompt_id == prompt_id).first()
    
    def get_by_hash(self, prompt_hash: str) -> Optional[PromptInstanceModel]:
        """Get prompt by hash"""
        return self.db.query(PromptInstanceModel).filter(PromptInstanceModel.dedup_hash == prompt_hash).first()
    
    def get_all_simhashes(self) -> List[tuple]:
        """
        Get all prompt_id and simhash pairs for near-duplicate detection.
        Returns list of (prompt_id, simhash) tuples.
        """
        results = (
            self.db.query(PromptInstanceModel.prompt_id, PromptInstanceModel.simhash)
            .filter(PromptInstanceModel.simhash.isnot(None))
            .all()
        )
        return [(r.prompt_id, r.simhash) for r in results]
    
    def get_pending(self, limit: int = 100) -> List[PromptInstanceModel]:
        """Get pending (unprocessed) prompts."""
        return (
            self.db.query(PromptInstanceModel)
            .filter(PromptInstanceModel.embedding_vector == None)
            .limit(limit)
            .all()
        )

    def count_new_members_since(self, family_id: str, since: datetime) -> int:
        """Count members added to a family after a specific timestamp."""
        return (
            self.db.query(PromptInstanceModel)
            .filter(
                PromptInstanceModel.family_id == family_id,
                PromptInstanceModel.created_at > since
            )
            .count()
        )
    
    def update_family(self, prompt_id: str, family_id: str) -> None:
        """Assign prompt to a family"""
        prompt = self.get_by_id(prompt_id)
        if prompt:
            prompt.family_id = family_id
            self.db.commit()
    
    def get_by_family(self, family_id: str) -> List[PromptInstanceModel]:
        """Get all prompts in a family"""
        return (
            self.db.query(PromptInstanceModel)
            .filter(PromptInstanceModel.family_id == family_id)
            .all()
        )

    def get_latest(self, limit: int = 20) -> List[PromptInstanceModel]:
        """Get latest prompts"""
        return (
            self.db.query(PromptInstanceModel)
            .order_by(PromptInstanceModel.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def get_all(self) -> List[PromptInstanceModel]:
        """Get all prompts"""
        return self.db.query(PromptInstanceModel).all()
    
    def get_pending_count(self) -> int:
        """Count prompts that haven't been assigned to a family"""
        return (
            self.db.query(PromptInstanceModel)
            .filter(PromptInstanceModel.family_id.is_(None))
            .count()
        )
    
    def get_classified_count(self) -> int:
        """Count prompts that have been assigned to a family"""
        return (
            self.db.query(PromptInstanceModel)
            .filter(PromptInstanceModel.family_id.isnot(None))
            .count()
        )
    
    def update_embedding(self, prompt_id: str, embedding: List[float]) -> None:
        """Update prompt embedding vector"""
        prompt = self.get_by_id(prompt_id)
        if prompt:
            prompt.embedding_vector = embedding
            prompt.updated_at = datetime.utcnow()
            self.db.commit()
    
    def update_embedding_and_family(
        self, 
        prompt_id: str, 
        embedding: List[float], 
        family_id: Optional[str]
    ) -> None:
        """Update prompt embedding and family assignment"""
        prompt = self.get_by_id(prompt_id)
        if prompt:
            prompt.embedding_vector = embedding
            prompt.family_id = family_id
            prompt.updated_at = datetime.utcnow()
            self.db.commit()

    def count_all(self) -> int:
        """Get total count of prompts."""
        return self.db.query(PromptInstanceModel).count()
    
    def clear_all_embeddings(self) -> int:
        """Clear all embedding vectors (use when switching embedding models)."""
        count = self.db.query(PromptInstanceModel).filter(
            PromptInstanceModel.embedding_vector != None,
            PromptInstanceModel.embedding_vector != []
        ).update({PromptInstanceModel.embedding_vector: []})
        self.db.commit()
        return count
    
    def count_pending(self) -> int:
        """Get count of prompts without family assignment."""
        return (
            self.db.query(PromptInstanceModel)
            .filter(PromptInstanceModel.family_id.is_(None))
            .count()
        )
    
    def get_paginated(
        self,
        family_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[PromptInstanceModel]:
        """Get prompts with pagination and optional family filter."""
        query = self.db.query(PromptInstanceModel)
        if family_id:
            query = query.filter(PromptInstanceModel.family_id == family_id)
        return query.order_by(PromptInstanceModel.created_at.desc()).offset(offset).limit(limit).all()


class FamilyRepository:
    """Repository for family operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, family_id: str) -> Optional[PromptFamilyModel]:
        """Get family by ID"""
        return self.db.query(PromptFamilyModel).filter(PromptFamilyModel.family_id == family_id).first()
    
    def get_all(self) -> List[PromptFamilyModel]:
        """Get all families"""
        return self.db.query(PromptFamilyModel).all()
    
    def update_member_count(self, family_id: str, count: int) -> None:
        """Update family member count"""
        family = self.get_by_id(family_id)
        if family:
            family.member_count = count
            family.updated_at = datetime.utcnow()
            self.db.commit()
    
    def get_all_centroids(self) -> Dict[str, List[float]]:
        """Get all family centroids as dict of family_id -> centroid vector"""
        families = self.get_all()
        return {
            f.family_id: f.centroid_vector 
            for f in families 
            if f.centroid_vector is not None
        }
    
    def create_or_update_family(
        self,
        cluster_id: int,
        centroid: Optional[List[float]],
        member_count: int,
        family_name: Optional[str] = None
    ) -> str:
        """
        Create a new family or update existing one for a cluster.
        
        Args:
            cluster_id: HDBSCAN cluster ID
            centroid: Centroid vector for the cluster
            member_count: Number of prompts in the cluster
            family_name: Optional custom name (generated by LLM)
        
        Returns:
            family_id of created/updated family
        """
        import uuid
        
        # Use provided name or fallback to Cluster-X
        name = family_name or f"Cluster-{cluster_id}"
        existing = (
            self.db.query(PromptFamilyModel)
            .filter(PromptFamilyModel.family_name == name)
            .first()
        )
        
        if existing:
            # Update existing family
            existing.family_name = name  # Update name in case it changed
            existing.centroid_vector = centroid
            existing.member_count = member_count
            existing.updated_at = datetime.utcnow()
            existing.version += 1
            self.db.commit()
            return existing.family_id
        else:
            # Create new family
            family = PromptFamilyModel(
                family_id=str(uuid.uuid4()),
                family_name=name,
                description=f"Auto-generated cluster {cluster_id}",
                centroid_vector=centroid,
                member_count=member_count
            )
            self.db.add(family)
            self.db.commit()
            return family.family_id
    
    def update_all_member_counts(self) -> None:
        """Update member counts for all families based on actual prompt counts"""
        families = self.get_all()
        for family in families:
            count = (
                self.db.query(PromptInstanceModel)
                .filter(PromptInstanceModel.family_id == family.family_id)
                .count()
            )
            family.member_count = count
            family.updated_at = datetime.utcnow()
            self.db.commit()

    def create_family(
        self,
        family_id: str,
        family_name: str,
        description: Optional[str] = None,
        member_count: int = 0,
        centroid_vector: Optional[List[float]] = None,
    ) -> PromptFamilyModel:
        """Create a new prompt family (cluster)."""
        family = PromptFamilyModel(
            family_id=family_id,
            family_name=family_name,
            description=description,
            member_count=member_count,
            centroid_vector=centroid_vector,
        )
        self.db.add(family)
        self.db.commit()
        self.db.refresh(family)
        return family

    def create_template(
        self,
        family_id: str,
        template_text: str,
        slots: dict,
        quality_score: Optional[float] = None,
    ) -> TemplateModel:
        """Create a template for a family. slots typically: {variables: [...], example_values: {...}}."""
        template = TemplateModel(
            template_id=str(uuid.uuid4()),
            family_id=family_id,
            template_text=template_text,
            slots=slots,
            template_version=1,
            quality_score=quality_score,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template_by_family(self, family_id: str) -> Optional[TemplateModel]:
        """Get the template for a family (assumes one template per family)."""
        return (
            self.db.query(TemplateModel)
            .filter(TemplateModel.family_id == family_id)
            .order_by(TemplateModel.created_at.desc())
            .first()
        )

    def count_all(self) -> int:
        """Get total count of families."""
        return self.db.query(PromptFamilyModel).count()


class TemplateRepository:
    """Repository for template operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_family(self, family_id: str) -> Optional[TemplateModel]:
        """Get template for a family."""
        return (
            self.db.query(TemplateModel)
            .filter(TemplateModel.family_id == family_id)
            .order_by(TemplateModel.created_at.desc())
            .first()
        )
    
    def get_all(self, limit: int = 20, offset: int = 0) -> List[TemplateModel]:
        """Get all templates with pagination."""
        return (
            self.db.query(TemplateModel)
            .order_by(TemplateModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def count_all(self) -> int:
        """Get total count of templates."""
        return self.db.query(TemplateModel).count()

    def update_template(
        self,
        template_id: str,
        template_text: str,
        slots: dict,
    ) -> Optional[TemplateModel]:
        """Update an existing template with new text/slots."""
        template = (
            self.db.query(TemplateModel)
            .filter(TemplateModel.template_id == template_id)
            .first()
        )
        if template:
            template.template_text = template_text
            template.slots = slots
            template.template_version += 1
            template.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(template)
        return template


class LineageRepository:
    """Repository for lineage operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_lineage(
        self,
        parent_prompt_id: Optional[str],
        child_prompt_id: str,
        mutation_type: str,
        confidence: float = 0.0,
    ) -> "LineageModel":
        """Create a lineage link between parent and child prompts."""
        from packages.storage.models import Lineage as LineageModel
        
        lineage = LineageModel(
            parent_prompt_id=parent_prompt_id,
            child_prompt_id=child_prompt_id,
            mutation_type=mutation_type,
            confidence=confidence,
        )
        self.db.add(lineage)
        self.db.commit()
        self.db.refresh(lineage)
        return lineage
    
    def get_lineage_chain(self, prompt_id: str) -> List[dict]:
        """Get full evolution chain for a prompt (all ancestors and descendants)."""
        from packages.storage.models import Lineage as LineageModel
        
        chain = []
        visited = set()
        
        def traverse_up(current_id: str, path: List[str]):
            if current_id in visited or current_id is None:
                return
            visited.add(current_id)
            
            parents = (
                self.db.query(LineageModel)
                .filter(LineageModel.child_prompt_id == current_id)
                .all()
            )
            
            for parent_link in parents:
                if parent_link.parent_prompt_id:
                    new_path = [parent_link.parent_prompt_id] + path
                    chain.append({
                        "prompt_id": parent_link.parent_prompt_id,
                        "mutation_type": parent_link.mutation_type,
                        "confidence": parent_link.confidence,
                        "created_at": parent_link.created_at.isoformat() if parent_link.created_at else None,
                        "direction": "ancestor",
                        "path": new_path,
                    })
                    traverse_up(parent_link.parent_prompt_id, new_path)
        
        def traverse_down(current_id: str, path: List[str]):
            if current_id in visited or current_id is None:
                return
            visited.add(current_id)
            
            children = (
                self.db.query(LineageModel)
                .filter(LineageModel.parent_prompt_id == current_id)
                .all()
            )
            
            for child_link in children:
                new_path = path + [child_link.child_prompt_id]
                chain.append({
                    "prompt_id": child_link.child_prompt_id,
                    "mutation_type": child_link.mutation_type,
                    "confidence": child_link.confidence,
                    "created_at": child_link.created_at.isoformat() if child_link.created_at else None,
                    "direction": "descendant",
                    "path": new_path,
                })
                traverse_down(child_link.child_prompt_id, new_path)
        
        chain.append({
            "prompt_id": prompt_id,
            "mutation_type": "root",
            "confidence": 1.0,
            "direction": "current",
            "path": [prompt_id],
        })
        
        visited.clear()
        traverse_up(prompt_id, [prompt_id])
        visited.clear()
        visited.add(prompt_id)
        traverse_down(prompt_id, [prompt_id])
        
        return chain
    
    def get_children(self, prompt_id: str) -> List["LineageModel"]:
        """Get all direct children of a prompt."""
        from packages.storage.models import Lineage as LineageModel
        
        return (
            self.db.query(LineageModel)
            .filter(LineageModel.parent_prompt_id == prompt_id)
            .all()
        )
    
    def get_parents(self, prompt_id: str) -> List["LineageModel"]:
        """Get all direct parents of a prompt."""
        from packages.storage.models import Lineage as LineageModel
        
        return (
            self.db.query(LineageModel)
            .filter(LineageModel.child_prompt_id == prompt_id)
            .all()
        )
    
    def count_all(self) -> int:
        """Get total count of lineage links."""
        from packages.storage.models import Lineage as LineageModel
        
        return self.db.query(LineageModel).count()
        self.db.commit()
