"""
Data ingestion from various sources
"""

from packages.ingestion.files import ingest_from_file
from packages.ingestion.portkey import PortKeyIngestor
from packages.ingestion.normalizer import normalize_text, compute_hash, extract_metadata

__all__ = [
    "ingest_from_file",
    "PortKeyIngestor",
    "normalize_text",
    "compute_hash",
    "extract_metadata",
]
