"""
SimHash-based near-duplicate detection for prompts.

Google-style fingerprinting: similar texts produce hashes that differ in few bits.
Uses Hamming distance to measure similarity.
"""

import hashlib
import logging
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


def simhash(text: str, num_bits: int = 64) -> int:
    """
    Compute SimHash fingerprint for text.
    
    How it works:
    1. Split text into tokens (words)
    2. Hash each token to a 64-bit number
    3. For each bit position, accumulate +1 (if bit=1) or -1 (if bit=0)
    4. Final hash: bit=1 if sum>0, else bit=0
    
    Args:
        text: Normalized text to hash
        num_bits: Number of bits in fingerprint (default 64)
    
    Returns:
        Integer fingerprint (64-bit)
    """
    tokens = text.split()
    
    if not tokens:
        return 0
    
    vector = [0] * num_bits
    
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16) & ((1 << num_bits) - 1)
        
        for i in range(num_bits):
            bit = (h >> i) & 1
            vector[i] += 1 if bit else -1
    
    fingerprint = 0
    for i, v in enumerate(vector):
        if v > 0:
            fingerprint |= (1 << i)
    
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    """
    Compute Hamming distance (number of differing bits) between two hashes.
    
    Args:
        a: First fingerprint
        b: Second fingerprint
    
    Returns:
        Number of bits that differ (0-64)
    """
    return bin(a ^ b).count("1")


class SimHashDeduplicator:
    """
    Near-duplicate detector using SimHash fingerprints.
    
    Similarity is measured by Hamming distance:
    - 0-3 bits: Almost identical (98%+ similar)
    - 4-8 bits: Very similar (90%+ similar)
    - 9-15 bits: Loosely similar
    - 16+ bits: Different
    """
    
    def __init__(self, threshold: int = 3):
        """
        Initialize the deduplicator.
        
        Args:
            threshold: Max Hamming distance to consider as duplicate (default: 3)
                      Lower = stricter matching
        """
        self.threshold = threshold
        self._fingerprints: dict[str, int] = {}  # prompt_id -> fingerprint
    
    def compute_fingerprint(self, text: str) -> int:
        """Compute SimHash fingerprint for text."""
        return simhash(text)
    
    def is_near_duplicate(self, text: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if text is a near-duplicate of any indexed text.
        
        Args:
            text: Normalized text to check
        
        Returns:
            Tuple of (is_duplicate, matching_id or None, hamming_distance or None)
        """
        fingerprint = simhash(text)
        
        for prompt_id, existing_fp in self._fingerprints.items():
            distance = hamming_distance(fingerprint, existing_fp)
            if distance <= self.threshold:
                return True, prompt_id, distance
        
        return False, None, None
    
    def add(self, prompt_id: str, text: str) -> int:
        """
        Add text to the index for future duplicate detection.
        
        Args:
            prompt_id: Unique identifier for the prompt
            text: Normalized text
        
        Returns:
            The computed fingerprint
        """
        fingerprint = simhash(text)
        self._fingerprints[prompt_id] = fingerprint
        return fingerprint
    
    def get_similar(self, text: str, max_distance: int = None) -> List[Tuple[str, int]]:
        """
        Get all similar prompt IDs for a given text.
        
        Args:
            text: Normalized text
            max_distance: Max Hamming distance (default: self.threshold)
        
        Returns:
            List of (prompt_id, distance) tuples
        """
        if max_distance is None:
            max_distance = self.threshold
            
        fingerprint = simhash(text)
        similar = []
        
        for prompt_id, existing_fp in self._fingerprints.items():
            distance = hamming_distance(fingerprint, existing_fp)
            if distance <= max_distance:
                similar.append((prompt_id, distance))
        
        return sorted(similar, key=lambda x: x[1])
    
    def size(self) -> int:
        """Return number of indexed prompts."""
        return len(self._fingerprints)


def are_similar(text_a: str, text_b: str, threshold: int = 3) -> Tuple[bool, int]:
    """
    Check if two texts are similar.
    
    Args:
        text_a: First normalized text
        text_b: Second normalized text
        threshold: Max Hamming distance for similarity
    
    Returns:
        Tuple of (is_similar, hamming_distance)
    """
    fp_a = simhash(text_a)
    fp_b = simhash(text_b)
    distance = hamming_distance(fp_a, fp_b)
    return distance <= threshold, distance
