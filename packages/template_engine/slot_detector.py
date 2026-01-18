"""
Step 2 & 3: Variable Slot Detection & Typing
Identify variable regions and classify them into typed slots.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import re

from packages.template_engine.alignment import AlignmentResult


class SlotType(Enum):
    """Types of template slots."""
    NUMERIC = "numeric"      # Numbers, quantities
    ENUM = "enum"            # Finite set of values
    TEXT = "text"            # Free-form text
    DATE = "date"            # Date/time values
    EMAIL = "email"          # Email addresses
    URL = "url"              # URLs


@dataclass
class Slot:
    """Represents a variable slot in a template."""
    name: str
    slot_type: SlotType
    position: int           # Token position in template
    examples: List[str]     # Example values from prompts
    enum_values: Optional[List[str]] = None  # For enum slots
    validation_pattern: Optional[str] = None  # Regex pattern
    description: Optional[str] = None
    required: bool = True
    default_value: Optional[str] = None


@dataclass
class SlotValidationResult:
    """Result of slot validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# Patterns for slot type detection
NUMERIC_PATTERN = re.compile(r'^-?\d+\.?\d*$')
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}$')
EMAIL_PATTERN = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
URL_PATTERN = re.compile(r'^https?://|www\.')


def detect_slot_type(examples: List[str]) -> SlotType:
    """
    Detect the type of a slot based on example values.
    
    Rules:
    - All numeric → NUMERIC
    - Small finite set → ENUM
    - Matches special patterns → DATE/EMAIL/URL
    - Everything else → TEXT
    
    Args:
        examples: List of example values from the variable region
        
    Returns:
        The detected SlotType
    """
    if not examples:
        return SlotType.TEXT
    
    # Clean examples
    cleaned = [ex.strip() for ex in examples if ex.strip()]
    if not cleaned:
        return SlotType.TEXT
    
    # Check if all are numeric
    if all(NUMERIC_PATTERN.match(ex) for ex in cleaned):
        return SlotType.NUMERIC
    
    # Check for dates
    if all(DATE_PATTERN.match(ex) for ex in cleaned):
        return SlotType.DATE
    
    # Check for emails
    if all(EMAIL_PATTERN.match(ex) for ex in cleaned):
        return SlotType.EMAIL
    
    # Check for URLs
    if all(URL_PATTERN.match(ex) for ex in cleaned):
        return SlotType.URL
    
    # Check for enum (small finite set with repetition)
    unique_values = set(cleaned)
    if len(unique_values) <= 5 and len(cleaned) >= 3:
        # Likely an enum if we see the same values repeated
        return SlotType.ENUM
    
    return SlotType.TEXT


def generate_slot_name(position: int, examples: List[str], slot_type: SlotType) -> str:
    """
    Generate a meaningful name for a slot based on context.
    
    Args:
        position: Position in the template
        examples: Example values
        slot_type: The detected type
        
    Returns:
        A human-readable slot name
    """
    # Try to infer from examples
    if slot_type == SlotType.NUMERIC:
        # Check for common patterns
        examples_lower = [ex.lower() for ex in examples]
        if any('word' in ex for ex in examples_lower):
            return "word_count"
        if any('%' in ex for ex in examples):
            return "percentage"
        return f"number_{position}"
    
    if slot_type == SlotType.DATE:
        return "date"
    
    if slot_type == SlotType.EMAIL:
        return "email"
    
    if slot_type == SlotType.URL:
        return "url"
    
    if slot_type == SlotType.ENUM:
        # Use first example as hint
        if examples:
            base = examples[0].lower().replace(' ', '_')[:15]
            return f"{base}_option"
        return f"option_{position}"
    
    return f"text_{position}"


def detect_slots(alignment: AlignmentResult) -> List[Slot]:
    """
    Detect and classify slots from an alignment result.
    
    This is the main entry point for Steps 2 & 3 of template creation.
    
    Args:
        alignment: Result from align_prompts()
        
    Returns:
        List of typed Slot objects
    """
    slots = []
    
    for i, (start, end, examples) in enumerate(alignment.variable_regions):
        # Detect type
        slot_type = detect_slot_type(examples)
        
        # Generate name
        name = generate_slot_name(i, examples, slot_type)
        
        # Build slot
        slot = Slot(
            name=name,
            slot_type=slot_type,
            position=start,
            examples=examples[:10],  # Keep up to 10 examples
        )
        
        # Add enum values if applicable
        if slot_type == SlotType.ENUM:
            slot.enum_values = list(set(examples))
        
        # Add validation pattern
        if slot_type == SlotType.NUMERIC:
            slot.validation_pattern = r'^-?\d+\.?\d*$'
        elif slot_type == SlotType.EMAIL:
            slot.validation_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        elif slot_type == SlotType.URL:
            slot.validation_pattern = r'^https?://'
        
        slots.append(slot)
    
    return slots


class SlotValidator:
    """Validates slot values against their type and constraints."""
    
    def __init__(self, slots: List[Slot]):
        self.slots = {slot.name: slot for slot in slots}
    
    def validate(self, params: Dict[str, Any]) -> SlotValidationResult:
        """
        Validate parameters against slot definitions.
        
        Args:
            params: Dictionary of slot_name -> value
            
        Returns:
            SlotValidationResult with validity and errors
        """
        errors = []
        warnings = []
        
        # Check required slots
        for name, slot in self.slots.items():
            if slot.required and name not in params:
                if slot.default_value is not None:
                    warnings.append(f"Using default value for '{name}'")
                else:
                    errors.append(f"Missing required slot: '{name}'")
        
        # Validate each provided value
        for name, value in params.items():
            if name not in self.slots:
                warnings.append(f"Unknown slot: '{name}'")
                continue
            
            slot = self.slots[name]
            value_str = str(value)
            
            # Type validation
            if slot.slot_type == SlotType.NUMERIC:
                if not NUMERIC_PATTERN.match(value_str):
                    errors.append(f"Slot '{name}' must be numeric, got: '{value}'")
            
            elif slot.slot_type == SlotType.ENUM:
                if slot.enum_values and value_str not in slot.enum_values:
                    errors.append(
                        f"Slot '{name}' must be one of {slot.enum_values}, got: '{value}'"
                    )
            
            elif slot.slot_type == SlotType.EMAIL:
                if not EMAIL_PATTERN.match(value_str):
                    errors.append(f"Slot '{name}' must be a valid email, got: '{value}'")
            
            elif slot.slot_type == SlotType.URL:
                if not URL_PATTERN.match(value_str):
                    errors.append(f"Slot '{name}' must be a valid URL, got: '{value}'")
            
            # Custom pattern validation
            if slot.validation_pattern:
                if not re.match(slot.validation_pattern, value_str):
                    errors.append(
                        f"Slot '{name}' failed pattern validation: '{value}'"
                    )
        
        return SlotValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
