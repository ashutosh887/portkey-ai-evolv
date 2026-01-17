"""
Repository pattern for database operations
"""

import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.orm import Session
from packages.storage.models import (
    PromptInstance as PromptInstanceModel,
    PromptFamily as PromptFamilyModel,
    Template as TemplateModel,
)
from packages.core.models import PromptInstance as PromptInstanceDomain
from packages.ingestion.normalizer import normalize_text
from datetime import datetime

if TYPE_CHECKING:
    from packages.core.models import PromptDNA


class PromptRepository:
    """Repository for prompt operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_from_instance(self, instance: PromptInstanceDomain) -> PromptInstanceModel:
        """Create a new prompt record from a domain instance"""
        # Check if already exists by ID
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
        """Get prompts that haven't been assigned to a family"""
        return (
            self.db.query(PromptInstanceModel)
            .filter(PromptInstanceModel.family_id.is_(None))
            .limit(limit)
            .all()
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

    def count_all(self) -> int:
        """Get total count of prompts."""
        return self.db.query(PromptInstanceModel).count()
    
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
    
    def count_all(self) -> int:
        """Get total count of templates."""
        return self.db.query(TemplateModel).count()
