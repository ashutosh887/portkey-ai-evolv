"""
Extract DNA from raw prompts
"""

import hashlib
import re
from typing import Optional
from packages.core.models import PromptDNA, PromptStructure, PromptVariables, PromptInstructions


VARIABLE_PATTERNS = [
    r'\{\{(\w+)\}\}',           # {{variable}}
    r'\{(\w+)\}',               # {variable}
    r'\$(\w+)',                 # $VARIABLE
    r'\[(\w+)\]',               # [PLACEHOLDER]
    r'<(\w+)>',                 # <input>
    r'__(\w+)__',               # __SLOT__
]


def extract_dna(raw_text: str, metadata: Optional[dict] = None) -> PromptDNA:
    """
    Extract DNA from raw prompt text
    
    Args:
        raw_text: The raw prompt text
        metadata: Optional metadata (source, timestamp, etc.)
    
    Returns:
        PromptDNA object
    """
    # Generate hash for deduplication
    prompt_hash = hashlib.sha256(raw_text.encode()).hexdigest()
    
    # Extract structure
    structure = _extract_structure(raw_text)
    
    # Detect variables
    variables = _detect_variables(raw_text)
    
    # Extract instructions (basic version, LLM-enhanced later)
    instructions = _extract_instructions(raw_text)
    
    # Embedding will be generated separately
    embedding: list[float] = []
    
    return PromptDNA(
        id=f"pg-{prompt_hash[:8]}",
        raw_text=raw_text,
        hash=prompt_hash,
        structure=structure,
        variables=variables,
        instructions=instructions,
        embedding=embedding,
        metadata=metadata or {},
    )


def _extract_structure(text: str) -> PromptStructure:
    """Extract structural components"""
    # Basic parsing - detect system/user/assistant patterns
    # TODO: Enhance with more sophisticated parsing
    
    system_message = None
    user_message = text
    assistant_prefill = None
    
    # Try to detect system message patterns
    if "system:" in text.lower() or "system message:" in text.lower():
        # Basic extraction - enhance later
        parts = re.split(r'(?i)system\s*:?\s*', text, maxsplit=1)
        if len(parts) > 1:
            system_message = parts[1].split("\n")[0]
            user_message = "\n".join(parts[1].split("\n")[1:]) if len(parts[1].split("\n")) > 1 else parts[1]
    
    # Estimate tokens (rough: 1 token ≈ 4 characters)
    total_tokens = len(text) // 4
    
    return PromptStructure(
        system_message=system_message,
        user_message=user_message,
        assistant_prefill=assistant_prefill,
        total_tokens=total_tokens,
    )


def _detect_variables(text: str) -> PromptVariables:
    """Detect variable patterns in text"""
    detected = []
    
    for pattern in VARIABLE_PATTERNS:
        matches = re.findall(pattern, text)
        detected.extend(matches)
    
    # Remove duplicates while preserving order
    detected = list(dict.fromkeys(detected))
    
    return PromptVariables(
        detected=detected,
        slots=len(detected),
    )


def _extract_instructions(text: str) -> PromptInstructions:
    """Extract instructions and constraints (basic version)"""
    tone = []
    format_type = None
    constraints = []
    examples_count = 0
    
    # Detect format
    if "json" in text.lower():
        format_type = "JSON"
    elif "markdown" in text.lower():
        format_type = "markdown"
    
    # Count examples (rough heuristic)
    examples_count = text.count("example") + text.count("Example")
    
    # Detect tone keywords
    tone_keywords = {
        "professional": ["professional", "formal", "business"],
        "friendly": ["friendly", "casual", "conversational"],
        "concise": ["concise", "brief", "short"],
    }
    
    text_lower = text.lower()
    for tone_name, keywords in tone_keywords.items():
        if any(kw in text_lower for kw in keywords):
            tone.append(tone_name)
    
    # Detect constraints
    if "under" in text_lower and ("word" in text_lower or "token" in text_lower):
        constraints.append("length_limit")
    if "bullet" in text_lower or "list" in text_lower:
        constraints.append("use_bullet_points")
    
    return PromptInstructions(
        tone=tone,
        format=format_type,
        constraints=constraints,
        examples_count=examples_count,
    )
