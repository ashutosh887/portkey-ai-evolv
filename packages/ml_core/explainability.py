import os
from typing import Dict, List, Optional, Tuple

try:
    from portkey_ai import Portkey
except ImportError:
    Portkey = None


class Explainer:
    def __init__(self, api_key: Optional[str] = None, virtual_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        if Portkey is None:
            raise ImportError("portkey-ai package is required for explainability")
        
        self.api_key = api_key or os.getenv("PORTKEY_API_KEY")
        self.virtual_key = virtual_key or os.getenv("PORTKEY_VIRTUAL_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("PORTKEY_API_KEY required for explainability")
        
        portkey_config = {"api_key": self.api_key}
        if self.virtual_key:
            portkey_config["virtual_key"] = self.virtual_key
        
        self.portkey = Portkey(**portkey_config)
    
    def _create_explanation_prompt(
        self,
        prompt: str,
        cluster_id: int,
        cluster_members: List[str],
        similarity_score: float,
        centroid_distance: Optional[float] = None
    ) -> str:
        members_text = "\n".join([f"- {member}" for member in cluster_members[:5]])
        
        return f"""Explain why this prompt was assigned to cluster {cluster_id}.

Prompt:
"{prompt}"

Cluster {cluster_id} contains {len(cluster_members)} similar prompts, including:
{members_text}

Similarity score: {similarity_score:.3f}
{f'Distance to centroid: {centroid_distance:.3f}' if centroid_distance else ''}

Provide a concise explanation (2-3 sentences) of:
1. Why this prompt semantically belongs with the cluster
2. What common intent or pattern they share"""
    
    def explain_cluster_assignment(
        self,
        prompt: str,
        prompt_id: str,
        cluster_id: int,
        cluster_members: List[str],
        similarity_score: float,
        centroid_distance: Optional[float] = None
    ) -> str:
        prompt_text = self._create_explanation_prompt(
            prompt, cluster_id, cluster_members, similarity_score, centroid_distance
        )
        
        try:
            model_map = {
                "gpt-4o-mini": "@openai/gpt-4o-mini",
                "claude-3-haiku": "@anthropic/claude-3-haiku-20240307"
            }
            portkey_model = model_map.get(self.model, f"@openai/{self.model}")
            
            response = self.portkey.chat.completions.create(
                model=portkey_model,
                messages=[
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Explanation generation failed: {str(e)}"
    
    def explain_selection(
        self,
        query: str,
        selected_prompt: str,
        similarity_score: float,
        reason: str = "retrieval"
    ) -> str:
        prompt_text = f"""Explain why this prompt was selected as similar to the query.

Query:
"{query}"

Selected prompt:
"{selected_prompt}"

Similarity score: {similarity_score:.3f}
Selection method: {reason}

Provide a concise explanation (1-2 sentences) of why these prompts are semantically similar."""
        
        try:
            model_map = {
                "gpt-4o-mini": "@openai/gpt-4o-mini",
                "claude-3-haiku": "@anthropic/claude-3-haiku-20240307"
            }
            portkey_model = model_map.get(self.model, self.model)
            
            response = self.portkey.chat.completions.create(
                model=portkey_model,
                messages=[
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Explanation generation failed: {str(e)}"
