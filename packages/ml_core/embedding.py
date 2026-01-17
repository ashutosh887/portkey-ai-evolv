import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from InstructorEmbedding import INSTRUCTOR
except ImportError:
    INSTRUCTOR = None

try:
    from portkey_ai import Portkey
except ImportError:
    Portkey = None


class EmbeddingModel:
    def __init__(self, model_name: str, cache_dir: str = "./cache", portkey_api_key: Optional[str] = None, portkey_virtual_key: Optional[str] = None):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._model = None
        self._portkey_client = None
        self.portkey_api_key = portkey_api_key or os.getenv("PORTKEY_API_KEY")
        self.portkey_virtual_key = portkey_virtual_key or os.getenv("PORTKEY_VIRTUAL_KEY")
        
    def _get_cache_path(self, text: str) -> Path:
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return self.cache_dir / f"embedding_{text_hash}.json"
    
    def _load_from_cache(self, text: str) -> Optional[List[float]]:
        cache_path = self._get_cache_path(text)
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                data = json.load(f)
                if data.get('model') == self.model_name:
                    return data.get('embedding')
        return None
    
    def _save_to_cache(self, text: str, embedding: List[float]):
        cache_path = self._get_cache_path(text)
        with open(cache_path, 'w') as f:
            json.dump({
                'model': self.model_name,
                'embedding': embedding
            }, f)
    
    def _load_model(self):
        if self._model is not None:
            return
        
        if self.model_name == "bge-large-en":
            self._model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        elif self.model_name == "instructor-xl":
            if INSTRUCTOR is None:
                raise ImportError("InstructorEmbedding package is required for instructor-xl model")
            self._model = INSTRUCTOR('hkunlp/instructor-xl')
        elif self.model_name == "text-embedding-3-large":
            if Portkey is None:
                raise ImportError("portkey-ai package is required for text-embedding-3-large")
            if not self.portkey_api_key:
                raise ValueError("PORTKEY_API_KEY required for text-embedding-3-large")
            
            portkey_config = {"api_key": self.portkey_api_key}
            if self.portkey_virtual_key:
                portkey_config["virtual_key"] = self.portkey_virtual_key
            
            self._portkey_client = Portkey(**portkey_config)
        else:
            raise ValueError(f"Unknown embedding model: {self.model_name}")
    
    def embed(self, text: str, instruction: Optional[str] = None) -> List[float]:
        cached = self._load_from_cache(text)
        if cached is not None:
            return cached
        
        self._load_model()
        
        if self.model_name == "text-embedding-3-large":
            response = self._portkey_client.embeddings.create(
                input=text,
                model="@openai/text-embedding-3-large",
                encoding_format="float"
            )
            embedding = response.data[0].embedding
        elif self.model_name == "instructor-xl":
            if instruction is None:
                instruction = "Represent the instruction prompt:"
            pairs = [[instruction, text]]
            embedding = self._model.encode(pairs, normalize_embeddings=True)[0].tolist()
        else:
            embedding = self._model.encode(text, normalize_embeddings=True).tolist()
        
        self._save_to_cache(text, embedding)
        return embedding
    
    def embed_batch(self, texts: List[str], instruction: Optional[str] = None, batch_size: int = 32) -> List[List[float]]:
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        for idx, text in enumerate(texts):
            cached = self._load_from_cache(text)
            if cached is not None:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                texts_to_embed.append(text)
                indices_to_embed.append(idx)
        
        if not texts_to_embed:
            return embeddings
        
        self._load_model()
        
        if self.model_name == "text-embedding-3-large":
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i:i + batch_size]
                response = self._portkey_client.embeddings.create(
                    input=batch,
                    model="@openai/text-embedding-3-large",
                    encoding_format="float"
                )
                batch_embeddings = [item.embedding for item in response.data]
                for j, emb in enumerate(batch_embeddings):
                    idx = indices_to_embed[i + j]
                    embeddings[idx] = emb
                    self._save_to_cache(texts_to_embed[i + j], emb)
        elif self.model_name == "instructor-xl":
            if instruction is None:
                instruction = "Represent the instruction prompt:"
            pairs = [[instruction, text] for text in texts_to_embed]
            batch_embeddings = self._model.encode(pairs, normalize_embeddings=True, batch_size=batch_size)
            for j, emb in enumerate(batch_embeddings):
                idx = indices_to_embed[j]
                embeddings[idx] = emb.tolist()
                self._save_to_cache(texts_to_embed[j], emb.tolist())
        else:
            batch_embeddings = self._model.encode(
                texts_to_embed, 
                normalize_embeddings=True, 
                batch_size=batch_size,
                show_progress_bar=True
            )
            for j, emb in enumerate(batch_embeddings):
                idx = indices_to_embed[j]
                embeddings[idx] = emb.tolist()
                self._save_to_cache(texts_to_embed[j], emb.tolist())
        
        return embeddings


def create_embeddings(
    prompts: Dict[str, str],
    model_name: str = "bge-large-en",
    cache_dir: str = "./cache",
    portkey_api_key: Optional[str] = None,
    portkey_virtual_key: Optional[str] = None
) -> Dict[str, List[float]]:
    model = EmbeddingModel(
        model_name, 
        cache_dir,
        portkey_api_key=portkey_api_key,
        portkey_virtual_key=portkey_virtual_key
    )
    texts = list(prompts.values())
    prompt_ids = list(prompts.keys())
    
    embeddings_list = model.embed_batch(texts)
    
    return dict(zip(prompt_ids, embeddings_list))
