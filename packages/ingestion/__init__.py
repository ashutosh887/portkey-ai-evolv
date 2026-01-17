"""
Data ingestion from various sources
"""

from packages.ingestion.files import ingest_from_file
from packages.ingestion.portkey import ingest_from_portkey
from packages.ingestion.normalizer import normalize_text, compute_hash, extract_metadata

__all__ = [
    "ingest_from_file",
    "ingest_from_portkey",
    "normalize_text",
    "compute_hash",
    "extract_metadata",
]
