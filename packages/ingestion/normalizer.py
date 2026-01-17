"""
Prompt normalization and deduplication utilities
"""

import hashlib
import re
from typing import Dict, Any


def normalize_text(text: str) -> str:
    """
    Normalize prompt text for comparison and deduplication.
    
    Steps:
    1. Convert to lowercase
    2. Remove punctuation (keep alphanumeric and whitespace)
    3. Collapse multiple whitespace to single space
    4. Strip leading/trailing whitespace
    
    Args:
        text: Raw prompt text
    
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation (keep only alphanumeric and whitespace)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Collapse multiple whitespace to single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()


def compute_hash(text: str) -> str:
    """
    Compute SHA256 hash of normalized text for exact deduplication.
    
    Args:
        text: Text to hash (should already be normalized)
    
    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def extract_metadata(source: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from source data
    
    Args:
        source: Source type (portkey, file, git, etc.)
        data: Raw data dictionary
    
    Returns:
        Metadata dictionary
    """
    metadata = {
        "source": source,
        "timestamp": data.get("timestamp") or data.get("created_at"),
        "user_id": data.get("user_id") or data.get("user"),
        "model": data.get("model"),
        "original_file": data.get("file_path") or data.get("file"),
    }
    
    return {k: v for k, v in metadata.items() if v is not None}
