import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import faiss


class FAISSIndex:
    def __init__(self, dimension: int, index_type: str = "IVF_FLAT", nlist: int = 100, m: int = 32, ef_construction: int = 200):
        self.dimension = dimension
        self.index_type = index_type
        self.prompt_id_to_index: Dict[str, int] = {}
        self.index_to_prompt_id: Dict[int, str] = {}
        
        if index_type == "IVF_FLAT":
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            self.index.nprobe = 10
        elif index_type == "HNSW":
            self.index = faiss.IndexHNSWFlat(dimension, m)
            self.index.hnsw.efConstruction = ef_construction
            self.index.hnsw.efSearch = 50
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        self.index = faiss.IndexIDMap(self.index)
    
    def add(self, prompt_id: str, embedding: List[float]):
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        idx = len(self.prompt_id_to_index)
        self.prompt_id_to_index[prompt_id] = idx
        self.index_to_prompt_id[idx] = prompt_id
        
        self.index.add_with_ids(embedding_array, np.array([idx], dtype=np.int64))
    
    def add_batch(self, embeddings: Dict[str, List[float]]):
        if not embeddings:
            return
        
        prompt_ids = list(embeddings.keys())
        embedding_matrix = np.array([embeddings[pid] for pid in prompt_ids], dtype=np.float32)
        
        faiss.normalize_L2(embedding_matrix)
        
        start_idx = len(self.prompt_id_to_index)
        indices = np.arange(start_idx, start_idx + len(prompt_ids), dtype=np.int64)
        
        for i, prompt_id in enumerate(prompt_ids):
            self.prompt_id_to_index[prompt_id] = int(indices[i])
            self.index_to_prompt_id[int(indices[i])] = prompt_id
        
        if self.index_type == "IVF_FLAT":
            base_index = self.index
            if isinstance(self.index, faiss.IndexIDMap):
                base_index = faiss.downcast_index(self.index.index)
            
            if isinstance(base_index, faiss.IndexIVFFlat):
                total_vectors = len(prompt_ids)
                nlist = base_index.nlist
                
                if not base_index.is_trained:
                    if total_vectors >= nlist:
                        base_index.train(embedding_matrix)
                    else:
                        if total_vectors > 0:
                            base_index.train(embedding_matrix)
        
        self.index.add_with_ids(embedding_matrix, indices)
    
    def search(self, query_embedding: List[float], k: int = 10) -> List[Tuple[str, float]]:
        if self.index.ntotal == 0:
            return []
        
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        distances, indices = self.index.search(query_array, min(k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            prompt_id = self.index_to_prompt_id.get(int(idx))
            if prompt_id:
                similarity = 1.0 - (float(dist) / 2.0)
                results.append((prompt_id, similarity))
        
        return results
    
    def save(self, filepath: Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(filepath))
        
        import json
        mappings_file = filepath.parent / f"{filepath.stem}_mappings.json"
        with open(mappings_file, 'w') as f:
            json.dump({
                'prompt_id_to_index': self.prompt_id_to_index,
                'index_to_prompt_id': {str(k): v for k, v in self.index_to_prompt_id.items()}
            }, f)
    
    @classmethod
    def load(cls, filepath: Path) -> "FAISSIndex":
        index = faiss.read_index(str(filepath))
        
        import json
        mappings_file = filepath.parent / f"{filepath.stem}_mappings.json"
        with open(mappings_file, 'r') as f:
            mappings = json.load(f)
            prompt_id_to_index = mappings['prompt_id_to_index']
            index_to_prompt_id = {int(k): v for k, v in mappings['index_to_prompt_id'].items()}
        
        base_index = index
        if isinstance(index, faiss.IndexIDMap):
            base_index = faiss.downcast_index(index.index)
        
        if isinstance(base_index, faiss.IndexIVFFlat):
            index_type = "IVF_FLAT"
        elif isinstance(base_index, faiss.IndexHNSWFlat):
            index_type = "HNSW"
        else:
            index_type = "IVF_FLAT"
        
        instance = cls.__new__(cls)
        instance.index = index
        instance.prompt_id_to_index = prompt_id_to_index
        instance.index_to_prompt_id = index_to_prompt_id
        instance.dimension = index.d
        instance.index_type = index_type
        
        return instance
