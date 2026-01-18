"""
Step 5: Template Refinement (Optional, LLM-based)
Improve template readability without changing semantics.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from difflib import unified_diff

from packages.template_engine.template_builder import CanonicalTemplate


@dataclass
class RefinementResult:
    """Result of template refinement."""
    original_text: str
    refined_text: str
    diff: str
    accepted: bool = False
    refinement_notes: Optional[str] = None


REFINEMENT_PROMPT = """You are a prompt template editor. Your task is to improve the readability of the following template WITHOUT changing its meaning or structure.

Rules:
1. Keep all {{slot_name}} placeholders exactly as they are
2. Fix grammar and awkward phrasing
3. Normalize tone to be professional and clear
4. Do not add or remove any information
5. Do not change the intent or meaning

Template to refine:
{template_text}

Respond with ONLY the refined template, nothing else."""


async def refine_template_async(
    template: CanonicalTemplate,
    llm_client: Any,
    model: str = "gpt-4.1"
) -> RefinementResult:
    """
    Refine a template using an LLM (async version).
    
    Args:
        template: The template to refine
        llm_client: LLM client (must have async chat completion)
        model: Model to use for refinement
        
    Returns:
        RefinementResult with original, refined, and diff
    """
    prompt = REFINEMENT_PROMPT.format(template_text=template.text)
    
    response = await llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,  # Low temperature for consistency
    )
    
    refined_text = response.choices[0].message.content.strip()
    
    # Generate diff
    diff = '\n'.join(unified_diff(
        template.text.splitlines(keepends=True),
        refined_text.splitlines(keepends=True),
        fromfile='original',
        tofile='refined'
    ))
    
    return RefinementResult(
        original_text=template.text,
        refined_text=refined_text,
        diff=diff,
        accepted=False,
        refinement_notes=f"Refined using {model}"
    )


def refine_template_sync(
    template: CanonicalTemplate,
    llm_client: Any,
    model: str = "gpt-4.1"
) -> RefinementResult:
    """
    Refine a template using an LLM (sync version).
    
    Args:
        template: The template to refine
        llm_client: LLM client (must have sync chat completion)
        model: Model to use for refinement
        
    Returns:
        RefinementResult with original, refined, and diff
    """
    prompt = REFINEMENT_PROMPT.format(template_text=template.text)
    
    response = llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    
    refined_text = response.choices[0].message.content.strip()
    
    diff = '\n'.join(unified_diff(
        template.text.splitlines(keepends=True),
        refined_text.splitlines(keepends=True),
        fromfile='original',
        tofile='refined'
    ))
    
    return RefinementResult(
        original_text=template.text,
        refined_text=refined_text,
        diff=diff,
        accepted=False,
        refinement_notes=f"Refined using {model}"
    )


def validate_refinement(
    original: CanonicalTemplate,
    refined_text: str
) -> tuple[bool, list[str]]:
    """
    Validate that a refinement preserves template structure.
    
    Args:
        original: Original template
        refined_text: Refined template text
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    import re
    errors = []
    
    # Extract slots from both
    slot_pattern = r'\{\{(\w+)\}\}'
    original_slots = set(re.findall(slot_pattern, original.text))
    refined_slots = set(re.findall(slot_pattern, refined_text))
    
    # Check no slots were removed
    missing_slots = original_slots - refined_slots
    if missing_slots:
        errors.append(f"Slots removed during refinement: {missing_slots}")
    
    # Check no new slots were added
    new_slots = refined_slots - original_slots
    if new_slots:
        errors.append(f"New slots added during refinement: {new_slots}")
    
    # Check slot order is preserved
    original_order = re.findall(slot_pattern, original.text)
    refined_order = re.findall(slot_pattern, refined_text)
    if original_order != refined_order:
        errors.append("Slot order changed during refinement")
    
    return len(errors) == 0, errors


def apply_refinement(
    template: CanonicalTemplate,
    result: RefinementResult
) -> CanonicalTemplate:
    """
    Apply a validated refinement to a template.
    
    Args:
        template: Original template
        result: Validated refinement result
        
    Returns:
        New CanonicalTemplate with refined text
    """
    is_valid, errors = validate_refinement(template, result.refined_text)
    
    if not is_valid:
        raise ValueError(f"Invalid refinement: {errors}")
    
    return CanonicalTemplate(
        text=result.refined_text,
        slots=template.slots,
        source_prompts=template.source_prompts,
        slot_map=template.slot_map
    )
