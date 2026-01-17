"""
Prompt DNA extraction engine
"""

from packages.dna_extractor.extractor import extract_dna
from packages.dna_extractor.embedding import EmbeddingService

__all__ = ["extract_dna", "EmbeddingService"]
