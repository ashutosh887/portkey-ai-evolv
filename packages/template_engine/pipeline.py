"""
Template Pipeline Runner
Orchestrates the full template creation/update pipeline with threshold-based triggering.
"""

import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from packages.template_engine.alignment import align_prompts
from packages.template_engine.slot_detector import detect_slots
from packages.template_engine.template_builder import build_template, template_to_dict, CanonicalTemplate
from packages.template_engine.versioning import compute_version_bump, TemplateVersion, VersionBumpType


@dataclass
class PipelineResult:
    """Result of running the template pipeline."""
    success: bool
    family_id: str
    template_id: Optional[str] = None
    version: Optional[str] = None
    is_new: bool = False
    bump_type: Optional[str] = None
    error: Optional[str] = None


class TemplatePipeline:
    """
    Orchestrates template creation and updates with threshold-based triggering.
    
    Usage:
        pipeline = TemplatePipeline(db_session)
        
        # Check and update all families that need it
        results = pipeline.run_pending_updates()
        
        # Or force update a specific family
        result = pipeline.update_family(family_id)
    """
    
    def __init__(self, db_session, min_prompts_for_template: int = 3):
        """
        Initialize the pipeline.
        
        Args:
            db_session: SQLAlchemy database session
            min_prompts_for_template: Minimum prompts needed to create a template
        """
        self.db = db_session
        self.min_prompts = min_prompts_for_template
    
    def get_families_needing_update(self) -> List[Any]:
        """Get all families that need a template update."""
        from packages.storage.models import PromptFamily
        
        families = self.db.query(PromptFamily).filter(
            PromptFamily.needs_template_update == True
        ).all()
        
        # Also check threshold-based
        all_families = self.db.query(PromptFamily).all()
        for family in all_families:
            if family not in families and family.check_needs_template_update():
                families.append(family)
        
        return families
    
    def run_pending_updates(self) -> List[PipelineResult]:
        """
        Run template updates for all families that need it.
        
        Returns:
            List of PipelineResult for each family processed
        """
        families = self.get_families_needing_update()
        results = []
        
        for family in families:
            result = self.update_family(family.family_id)
            results.append(result)
        
        return results
    
    def update_family(self, family_id: str, force: bool = False) -> PipelineResult:
        """
        Create or update the template for a specific family.
        
        Args:
            family_id: ID of the family to update
            force: If True, update even if threshold not met
            
        Returns:
            PipelineResult with outcome
        """
        from packages.storage.models import PromptFamily, PromptInstance, Template
        
        # Get family
        family = self.db.query(PromptFamily).filter(
            PromptFamily.family_id == family_id
        ).first()
        
        if not family:
            return PipelineResult(
                success=False,
                family_id=family_id,
                error=f"Family not found: {family_id}"
            )
        
        # Check if update is needed
        if not force and not family.check_needs_template_update():
            return PipelineResult(
                success=True,
                family_id=family_id,
                error="No update needed (threshold not met)"
            )
        
        # Get prompts for this family
        prompts = self.db.query(PromptInstance).filter(
            PromptInstance.family_id == family_id
        ).all()
        
        if len(prompts) < self.min_prompts:
            return PipelineResult(
                success=False,
                family_id=family_id,
                error=f"Not enough prompts ({len(prompts)} < {self.min_prompts})"
            )
        
        # Extract prompt texts
        prompt_texts = [p.normalized_text or p.original_text for p in prompts]
        
        try:
            # Run the template pipeline
            alignment = align_prompts(prompt_texts)
            slots = detect_slots(alignment)
            canonical = build_template(alignment, slots)
            
            # Get current active template (if exists)
            current_template = self.db.query(Template).filter(
                Template.family_id == family_id,
                Template.is_active == True
            ).first()
            
            # Determine version
            if current_template:
                # Update existing - compute version bump
                old_canonical = self._template_to_canonical(current_template)
                bump_result = compute_version_bump(
                    old_canonical, canonical,
                    TemplateVersion(
                        current_template.version_major,
                        current_template.version_minor,
                        current_template.version_patch
                    )
                )
                
                # Deactivate old template
                current_template.is_active = False
                
                # Create new template version
                new_template = Template(
                    template_id=str(uuid.uuid4()),
                    family_id=family_id,
                    parent_template_id=current_template.template_id,
                    is_active=True,
                    template_text=canonical.text,
                    slots=template_to_dict(canonical)["slots"],
                    version_major=bump_result.new_version.major,
                    version_minor=bump_result.new_version.minor,
                    version_patch=bump_result.new_version.patch,
                )
                
                is_new = False
                bump_type = bump_result.bump_type.value
            else:
                # New template
                new_template = Template(
                    template_id=str(uuid.uuid4()),
                    family_id=family_id,
                    is_active=True,
                    template_text=canonical.text,
                    slots=template_to_dict(canonical)["slots"],
                    version_major=1,
                    version_minor=0,
                    version_patch=0,
                )
                is_new = True
                bump_type = None
            
            # Save template
            self.db.add(new_template)
            
            # Mark prompts used as template seeds
            for prompt in prompts[:10]:  # Mark first 10 as seeds
                prompt.is_template_seed = True
            
            # Update family tracking
            family.member_count_at_last_template = family.member_count
            family.needs_template_update = False
            
            self.db.commit()
            
            return PipelineResult(
                success=True,
                family_id=family_id,
                template_id=new_template.template_id,
                version=new_template.version_string,
                is_new=is_new,
                bump_type=bump_type
            )
            
        except Exception as e:
            self.db.rollback()
            return PipelineResult(
                success=False,
                family_id=family_id,
                error=str(e)
            )
    
    def _template_to_canonical(self, template) -> CanonicalTemplate:
        """Convert a database Template to CanonicalTemplate."""
        from packages.template_engine.template_builder import template_from_dict
        
        data = {
            "text": template.template_text,
            "slots": template.slots or [],
        }
        return template_from_dict(data)


def on_prompt_added_to_family(db_session, family_id: str) -> Optional[PipelineResult]:
    """
    Hook to call when a prompt is added to a family.
    Checks threshold and triggers template update if needed.
    
    Args:
        db_session: Database session
        family_id: Family the prompt was added to
        
    Returns:
        PipelineResult if update was triggered, None otherwise
    """
    from packages.storage.models import PromptFamily
    
    family = db_session.query(PromptFamily).filter(
        PromptFamily.family_id == family_id
    ).first()
    
    if not family:
        return None
    
    # Check if threshold is met
    if family.check_needs_template_update():
        pipeline = TemplatePipeline(db_session)
        return pipeline.update_family(family_id)
    
    return None
