"""
Repository pattern for database operations
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from packages.storage.models import PromptModel, FamilyModel, LineageModel
from packages.core.models import PromptDNA, PromptFamily
from datetime import datetime


class PromptRepository:
    """Repository for prompt operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, prompt_dna: PromptDNA) -> PromptModel:
        """Create a new prompt record"""
        prompt_model = PromptModel(
            id=prompt_dna.id,
            raw_text=prompt_dna.raw_text,
            hash=prompt_dna.hash,
            dna_json=prompt_dna.model_dump(),
            family_id=prompt_dna.family_id,
            parent_id=prompt_dna.parent_id,
        )
        self.db.add(prompt_model)
        self.db.commit()
        self.db.refresh(prompt_model)
        return prompt_model
    
    def get_by_id(self, prompt_id: str) -> Optional[PromptModel]:
        """Get prompt by ID"""
        return self.db.query(PromptModel).filter(PromptModel.id == prompt_id).first()
    
    def get_by_hash(self, prompt_hash: str) -> Optional[PromptModel]:
        """Get prompt by hash"""
        return self.db.query(PromptModel).filter(PromptModel.hash == prompt_hash).first()
    
    def get_pending(self, limit: int = 100) -> List[PromptModel]:
        """Get prompts that haven't been assigned to a family"""
        return (
            self.db.query(PromptModel)
            .filter(PromptModel.family_id.is_(None))
            .limit(limit)
            .all()
        )
    
    def update_family(self, prompt_id: str, family_id: str) -> None:
        """Assign prompt to a family"""
        prompt = self.get_by_id(prompt_id)
        if prompt:
            prompt.family_id = family_id
            self.db.commit()
    
    def get_by_family(self, family_id: str) -> List[PromptModel]:
        """Get all prompts in a family"""
        return (
            self.db.query(PromptModel)
            .filter(PromptModel.family_id == family_id)
            .all()
        )


class FamilyRepository:
    """Repository for family operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, family: PromptFamily) -> FamilyModel:
        """Create a new family"""
        family_model = FamilyModel(
            id=family.id,
            name=family.name,
            description=family.description,
            canonical_template_json=family.canonical_template.model_dump(),
            member_count=family.member_count,
            statistics=family.statistics,
        )
        self.db.add(family_model)
        self.db.commit()
        self.db.refresh(family_model)
        return family_model
    
    def get_by_id(self, family_id: str) -> Optional[FamilyModel]:
        """Get family by ID"""
        return self.db.query(FamilyModel).filter(FamilyModel.id == family_id).first()
    
    def get_all(self) -> List[FamilyModel]:
        """Get all families"""
        return self.db.query(FamilyModel).all()
    
    def update_member_count(self, family_id: str, count: int) -> None:
        """Update family member count"""
        family = self.get_by_id(family_id)
        if family:
            family.member_count = count
            family.updated_at = datetime.utcnow()
            self.db.commit()


class LineageRepository:
    """Repository for lineage tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, child_id: str, parent_id: str, mutation_type: str, confidence: float) -> LineageModel:
        """Create a lineage relationship"""
        lineage = LineageModel(
            child_id=child_id,
            parent_id=parent_id,
            mutation_type=mutation_type,
            confidence=str(confidence),
        )
        self.db.add(lineage)
        self.db.commit()
        self.db.refresh(lineage)
        return lineage
    
    def get_lineage(self, prompt_id: str) -> List[LineageModel]:
        """Get evolution chain for a prompt"""
        return (
            self.db.query(LineageModel)
            .filter(LineageModel.child_id == prompt_id)
            .all()
        )
