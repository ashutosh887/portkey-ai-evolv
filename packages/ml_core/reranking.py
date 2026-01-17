import os
import json
import re
from typing import List, Tuple, Dict, Optional

try:
    from portkey_ai import Portkey
except ImportError:
    Portkey = None


class Reranker:
    def __init__(self, api_key: Optional[str] = None, virtual_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        if Portkey is None:
            raise ImportError("portkey-ai package is required for reranking")
        
        self.api_key = api_key or os.getenv("PORTKEY_API_KEY")
        self.virtual_key = virtual_key or os.getenv("PORTKEY_VIRTUAL_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("PORTKEY_API_KEY required for reranking")
        
        portkey_config = {"api_key": self.api_key}
        if self.virtual_key:
            portkey_config["virtual_key"] = self.virtual_key
        
        self.portkey = Portkey(**portkey_config)
    
    def _create_rerank_prompt(self, query: str, candidates: List[str]) -> str:
        candidates_text = "\n".join([f"{i+1}. {cand}" for i, cand in enumerate(candidates)])
        
        return f"""You are a semantic similarity evaluator. Given a query prompt and a list of candidate prompts, rank the candidates by how semantically similar they are to the query.

Query prompt:
{query}

Candidate prompts:
{candidates_text}

Rank the candidates from most similar (1) to least similar ({len(candidates)}). Return ONLY a JSON array of numbers representing the ranking, e.g., [2, 1, 3, 4] means candidate 2 is most similar, then 1, then 3, then 4."""
    
    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, str]],
        top_k: int = 8
    ) -> List[Tuple[str, float]]:
        if not candidates:
            return []
        
        candidates = candidates[:top_k]
        candidate_texts = [text for _, text in candidates]
        candidate_ids = [pid for pid, _ in candidates]
        
        prompt = self._create_rerank_prompt(query, candidate_texts)
        
        try:
            model_map = {
                "gpt-4o-mini": "@openai/gpt-4o-mini",
                "claude-3-haiku": "@anthropic/claude-3-haiku-20240307",
                "gemini-1.5-flash": "@google/gemini-1.5-flash"
            }
            portkey_model = model_map.get(self.model, f"@openai/{self.model}")
            
            response = self.portkey.chat.completions.create(
                model=portkey_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                json_match = re.search(r'\[[\d,\s]+\]', content)
                if json_match:
                    ranking = json.loads(json_match.group())
                else:
                    ranking = json.loads(content)
                
                ranked_results = []
                for rank_pos, candidate_idx in enumerate(ranking):
                    if 0 <= candidate_idx - 1 < len(candidate_ids):
                        prompt_id = candidate_ids[candidate_idx - 1]
                        score = 1.0 - (rank_pos * 0.1)
                        ranked_results.append((prompt_id, score))
                
                return ranked_results
            except (json.JSONDecodeError, ValueError, IndexError) as e:
                return [(pid, 0.5) for pid in candidate_ids]
        
        except Exception as e:
            return [(pid, 0.5) for pid, _ in candidates]
