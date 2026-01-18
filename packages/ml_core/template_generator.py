from datetime import datetime
import logging
import asyncio
from typing import List, Optional, Any
from sqlalchemy.orm import Session

from packages.storage.repositories import PromptRepository, FamilyRepository, TemplateRepository
from packages.llm.client import LLMClient
from packages.llm.mock_client import MockLLMClient
from packages.core.models import PromptDNA
from packages.dna_extractor import extract_dna

logger = logging.getLogger(__name__)

class TemplateGenerator:
    """
    Handles automatic generation and updating of templates for families.
    
    Logic:
    1. New Template: If family members > 2 and no template exists.
    2. Update Template: If existing template and current_members >= created_at_members + 5.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.prompt_repo = PromptRepository(db)
        self.family_repo = FamilyRepository(db)
        self.template_repo = TemplateRepository(db)
        
        try:
            self.llm_client = LLMClient()
        except Exception as e:
            logger.warning(f"Failed to init LLMClient, using MockLLMClient: {e}")
            self.llm_client = MockLLMClient()
            
    def _model_to_dna(self, model: Any) -> PromptDNA:
        """Convert DB model to PromptDNA object."""
        dna = extract_dna(model.original_text, model.metadata_ or {})
        dna.id = model.prompt_id
        dna.embedding = list(model.embedding_vector) if model.embedding_vector else []
        return dna

    async def _extract_template(self, prompt_dnas: List[PromptDNA]):
        """Extract template using LLM."""
        try:
            return await self.llm_client.extract_template(prompt_dnas)
        except Exception as e:
            logger.error(f"LLM template extraction failed: {e}")
            # Fallback to mock if LLM fails
            mock = MockLLMClient()
            return await mock.extract_template(prompt_dnas)

    async def process_family(self, family_id: str, force: bool = False) -> bool:
        """
        Check if family needs template generation/update and perform it.
        Returns True if a change was made.
        """
        family = self.family_repo.get_by_id(family_id)
        if not family:
            return False
            
        current_count = family.member_count
        template = self.template_repo.get_by_family(family_id)
        
        should_generate = False
        is_update = False
        
        if not template:
            # Condition 1: New Template if members > 2
            if current_count > 2:
                should_generate = True
                logger.info(f"Generating NEW template for family {family.family_name} (members: {current_count})")
        else:
            # Condition 2: Update Template if members increased by >= 5
            # Count members created AFTER the template was last updated
            last_update = template.updated_at or template.created_at
            
            new_member_count = self.prompt_repo.count_new_members_since(family_id, last_update)
            
            if new_member_count >= 5:
                should_generate = True
                is_update = True
                logger.info(f"UPDATING template for family {family.family_name} (new members: {new_member_count})")
        
        if force:
            logger.info(f"FORCE generating template for family {family.family_name}")
            should_generate = True
            is_update = True if template else False

        if should_generate:
            # Fetch prompt members
            members = self.prompt_repo.get_by_family(family_id)
            if not members:
                return False
                
            # Convert to DNA
            prompt_dnas = [self._model_to_dna(m) for m in members]
            
            # Limit samples
            if len(prompt_dnas) > 20:
                prompt_dnas = prompt_dnas[:20] 

            # Generate Template
            canonical = await self._extract_template(prompt_dnas)
            
            if is_update and template:
                self.template_repo.update_template(
                    template_id=template.template_id,
                    template_text=canonical.text,
                    slots={"variables": canonical.variables, "example_values": canonical.example_values}
                )
            else:
                self.family_repo.create_template(
                    family_id=family_id,
                    template_text=canonical.text,
                    slots={"variables": canonical.variables, "example_values": canonical.example_values},
                    quality_score=None
                )
            
            return True
            
        return False
        
    async def process_all_families(self, force: bool = False) -> int:
        """Process all families and return count of updates."""
        families = self.family_repo.get_all()
        updated_count = 0
        for family in families:
            if await self.process_family(family.family_id, force=force):
                updated_count += 1
        return updated_count
