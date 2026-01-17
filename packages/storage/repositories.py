"""
Repository pattern for database operations
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from packages.storage.models import PromptInstance as PromptInstanceModel, PromptFamily as PromptFamilyModel
from packages.core.models import PromptInstance as PromptInstanceDomain
from datetime import datetime


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
