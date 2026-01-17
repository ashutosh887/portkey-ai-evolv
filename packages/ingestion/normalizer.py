"""
Prompt normalization and deduplication
"""

import hashlib
import re
from typing import Dict, Any


def normalize_text(text: str) -> str:
    """
    Normalize prompt text for comparison
    
    Args:
        text: Raw prompt text
    
    Returns:
        Normalized text
    """
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    return text


def compute_hash(text: str) -> str:
    """
    Compute SHA256 hash for deduplication
    
    Args:
        text: Normalized text
    
    Returns:
        Hex digest of hash
    """
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


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
