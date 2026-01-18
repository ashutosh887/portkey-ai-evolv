"""
Step 1: Structural Alignment
Find common structure across prompts using token-level alignment algorithms.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re


@dataclass
class DiffOp:
    """Represents a single diff operation."""
    tag: str  # 'equal', 'replace', 'insert', 'delete'
    text_a: str
    text_b: str
    position: int


@dataclass
class AlignmentResult:
    """Result of aligning multiple prompts."""
    common_structure: str  # The invariant parts
    variable_regions: List[Tuple[int, int, List[str]]]  # (start, end, examples)
    prompts: List[str]
    tokens: List[List[str]] = field(default_factory=list)


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words and punctuation.
    Preserves whitespace structure for accurate reconstruction.
    """
    # Split on word boundaries while keeping delimiters
    tokens = re.findall(r'\S+|\s+', text)
    return tokens


def find_lcs(texts: List[str]) -> str:
    """
    Find the Longest Common Subsequence across multiple texts.
    Uses token-level comparison for better granularity.
    
    Args:
        texts: List of prompt texts to align
        
    Returns:
        The longest common subsequence as a string
    """
    if not texts:
        return ""
    if len(texts) == 1:
        return texts[0]
    
    # Tokenize all texts
    tokenized = [tokenize(text) for text in texts]
    
    # Start with first text's tokens as baseline
    common_tokens = tokenized[0]
    
    # Iteratively find LCS with each subsequent text
    for i in range(1, len(tokenized)):
        common_tokens = _lcs_tokens(common_tokens, tokenized[i])
        if not common_tokens:
            break
    
    return ''.join(common_tokens)


def _lcs_tokens(tokens_a: List[str], tokens_b: List[str]) -> List[str]:
    """Find LCS between two token lists using dynamic programming."""
    m, n = len(tokens_a), len(tokens_b)
    
    # DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if tokens_a[i-1] == tokens_b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Backtrack to find LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if tokens_a[i-1] == tokens_b[j-1]:
            lcs.append(tokens_a[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    return list(reversed(lcs))


def compute_diff(text_a: str, text_b: str) -> List[DiffOp]:
    """
    Compute token-level diff between two texts.
    
    Args:
        text_a: First text
        text_b: Second text
        
    Returns:
        List of diff operations
    """
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    
    matcher = SequenceMatcher(None, tokens_a, tokens_b)
    ops = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        ops.append(DiffOp(
            tag=tag,
            text_a=''.join(tokens_a[i1:i2]),
            text_b=''.join(tokens_b[j1:j2]),
            position=i1
        ))
    
    return ops


def align_prompts(prompts: List[str]) -> AlignmentResult:
    """
    Align multiple prompts to find common structure and variable regions.
    
    This is the main entry point for Step 1 of template creation.
    
    Args:
        prompts: List of prompt texts from the same family
        
    Returns:
        AlignmentResult with common structure and variable regions
    """
    if not prompts:
        return AlignmentResult(
            common_structure="",
            variable_regions=[],
            prompts=[]
        )
    
    if len(prompts) == 1:
        return AlignmentResult(
            common_structure=prompts[0],
            variable_regions=[],
            prompts=prompts,
            tokens=[tokenize(prompts[0])]
        )
    
    # Tokenize all prompts
    all_tokens = [tokenize(p) for p in prompts]
    
    # Use first prompt as reference
    reference_tokens = all_tokens[0]
    
    # Find matching regions across all prompts
    common_mask = [True] * len(reference_tokens)
    variable_examples: List[List[str]] = [[] for _ in reference_tokens]
    
    for other_tokens in all_tokens[1:]:
        matcher = SequenceMatcher(None, reference_tokens, other_tokens)
        
        # Mark non-matching regions
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                for i in range(i1, min(i2, len(common_mask))):
                    common_mask[i] = False
                    # Collect examples of what varies
                    if j1 < j2:
                        variable_examples[i].append(''.join(other_tokens[j1:j2]))
    
    # Build common structure and identify variable regions
    common_parts = []
    variable_regions = []
    
    i = 0
    while i < len(reference_tokens):
        if common_mask[i]:
            common_parts.append(reference_tokens[i])
            i += 1
        else:
            # Found a variable region
            start = i
            examples = set()
            examples.add(reference_tokens[i])
            
            while i < len(reference_tokens) and not common_mask[i]:
                for ex in variable_examples[i]:
                    examples.add(ex)
                i += 1
            
            # Add placeholder
            common_parts.append(f"{{{{slot_{len(variable_regions)}}}}}")
            variable_regions.append((start, i, list(examples)))
    
    return AlignmentResult(
        common_structure=''.join(common_parts),
        variable_regions=variable_regions,
        prompts=prompts,
        tokens=all_tokens
    )
