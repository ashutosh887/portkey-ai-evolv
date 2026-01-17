"""
Evolution tracking and mutation detection
"""

from typing import List, Optional, Tuple
from packages.core.models import PromptDNA
from packages.clustering.engine import compute_confidence, CONFIDENCE_THRESHOLDS


def classify_new_prompt(
    new_prompt: PromptDNA,
    existing_families: List[Tuple[str, List[PromptDNA]]],
) -> Tuple[str, str, float]:
    """
    Classify a new prompt into existing families or mark as new
    
    Args:
        new_prompt: The new prompt to classify
        existing_families: List of (family_id, prompts) tuples
    
    Returns:
        Tuple of (classification, family_id, confidence)
        classification: "exact_match", "variant", "new_family"
        family_id: ID of matched family (or None)
        confidence: Confidence score (0.0 to 1.0)
    """
    if not new_prompt.embedding:
        return ("new_family", None, 0.0)
    
    best_match = None
    best_confidence = 0.0
    best_family_id = None
    
    for family_id, family_prompts in existing_families:
        family_embeddings = [p.embedding for p in family_prompts if p.embedding]
        
        if not family_embeddings:
            continue
        
        confidence = compute_confidence(new_prompt, family_embeddings)
        
        if confidence > best_confidence:
            best_confidence = confidence
            best_family_id = family_id
            best_match = family_prompts
    
    if best_confidence >= CONFIDENCE_THRESHOLDS["auto_merge"]:
        return ("exact_match", best_family_id, best_confidence)
    elif best_confidence >= CONFIDENCE_THRESHOLDS["suggest_merge"]:
        return ("variant", best_family_id, best_confidence)
    else:
        return ("new_family", None, best_confidence)


def detect_mutation_type(
    parent: PromptDNA,
    child: PromptDNA,
) -> str:
    """
    Detect type of mutation between parent and child
    
    Args:
        parent: Parent prompt
        child: Child prompt
    
    Returns:
        Mutation type: "minor_edit", "major_change", "variable_change", etc.
    """
    if not parent.embedding or not child.embedding:
        return "unknown"
    
    from packages.clustering.engine import compute_confidence
    confidence = compute_confidence(child, [parent.embedding])
    
    parent_vars = set(parent.variables.detected)
    child_vars = set(child.variables.detected)
    
    if parent_vars != child_vars:
        return "variable_change"
    
    if parent.structure.system_message != child.structure.system_message:
        return "system_change"
    
    if confidence >= 0.95:
        return "minor_edit"
    elif confidence >= 0.80:
        return "moderate_change"
    else:
        return "major_change"
