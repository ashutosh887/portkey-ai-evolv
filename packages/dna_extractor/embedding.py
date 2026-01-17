"""
Embedding generation for prompts
"""

import os
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    """Service for generating embeddings"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding service
        
        Args:
            model_name: Model to use (default: all-MiniLM-L6-v2 for local)
        """
        self.model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        self._model: Optional[SentenceTransformer] = None
    
    def _get_model(self) -> SentenceTransformer:
        """Lazy load model"""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient)
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    async def generate_embedding_async(self, text: str) -> List[float]:
        """Async version of generate_embedding"""
        return self.generate_embedding(text)
    
    async def generate_embeddings_batch_async(self, texts: List[str]) -> List[List[float]]:
        """Async version of generate_embeddings_batch"""
        return self.generate_embeddings_batch(texts)
