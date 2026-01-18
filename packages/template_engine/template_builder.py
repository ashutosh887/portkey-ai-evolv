"""
Step 4: Template Builder
Create canonical templates from aligned prompts with slots.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
import re

from packages.template_engine.alignment import AlignmentResult
from packages.template_engine.slot_detector import Slot, SlotType


@dataclass
class CanonicalTemplate:
    """A canonical template with slots."""
    text: str                           # Template with {{slot_name}} placeholders
    slots: List[Slot]                   # Slot definitions
    source_prompts: List[str]           # Original prompts used to create this
    slot_map: Dict[str, int] = field(default_factory=dict)  # slot_name -> position


def build_template(
    alignment: AlignmentResult,
    slots: List[Slot],
    slot_format: str = "{{{{{name}}}}}"  # Default: {{name}}
) -> CanonicalTemplate:
    """
    Build a canonical template from alignment result and detected slots.
    
    This is the main entry point for Step 4 of template creation.
    
    Args:
        alignment: Result from align_prompts()
        slots: Detected slots from detect_slots()
        slot_format: Format string for slot placeholders
        
    Returns:
        CanonicalTemplate with text and slot definitions
    """
    template_text = alignment.common_structure
    slot_map = {}
    
    # Replace generic slot placeholders with named ones
    for i, slot in enumerate(slots):
        old_placeholder = f"{{{{slot_{i}}}}}"
        new_placeholder = slot_format.format(name=slot.name)
        template_text = template_text.replace(old_placeholder, new_placeholder)
        slot_map[slot.name] = slot.position
    
    return CanonicalTemplate(
        text=template_text,
        slots=slots,
        source_prompts=alignment.prompts,
        slot_map=slot_map
    )


def template_to_dict(template: CanonicalTemplate) -> Dict:
    """
    Convert a CanonicalTemplate to a dictionary for storage.
    
    Args:
        template: The template to convert
        
    Returns:
        Dictionary representation suitable for JSON/DB storage
    """
    return {
        "text": template.text,
        "slots": [
            {
                "name": slot.name,
                "type": slot.slot_type.value,
                "position": slot.position,
                "examples": slot.examples,
                "enum_values": slot.enum_values,
                "validation_pattern": slot.validation_pattern,
                "description": slot.description,
                "required": slot.required,
                "default_value": slot.default_value,
            }
            for slot in template.slots
        ],
        "source_prompt_count": len(template.source_prompts),
    }


def template_from_dict(data: Dict, source_prompts: Optional[List[str]] = None) -> CanonicalTemplate:
    """
    Reconstruct a CanonicalTemplate from a dictionary.
    
    Args:
        data: Dictionary from template_to_dict()
        source_prompts: Optional original prompts
        
    Returns:
        Reconstructed CanonicalTemplate
    """
    slots = [
        Slot(
            name=s["name"],
            slot_type=SlotType(s["type"]),
            position=s["position"],
            examples=s.get("examples", []),
            enum_values=s.get("enum_values"),
            validation_pattern=s.get("validation_pattern"),
            description=s.get("description"),
            required=s.get("required", True),
            default_value=s.get("default_value"),
        )
        for s in data.get("slots", [])
    ]
    
    slot_map = {slot.name: slot.position for slot in slots}
    
    return CanonicalTemplate(
        text=data["text"],
        slots=slots,
        source_prompts=source_prompts or [],
        slot_map=slot_map
    )


def extract_slot_names(template_text: str) -> List[str]:
    """
    Extract slot names from a template string.
    
    Args:
        template_text: Template with {{name}} placeholders
        
    Returns:
        List of slot names found
    """
    pattern = r'\{\{(\w+)\}\}'
    return re.findall(pattern, template_text)
