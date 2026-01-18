"""
Step 7: Intent → Template Mapping
Map user intents to appropriate templates using embeddings.
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class IntentMatch:
    """Result of intent matching."""
    template_id: str
    family_id: str
    similarity_score: float
    confidence: str  # "high", "medium", "low"


@dataclass
class IntentCentroid:
    """Stored intent centroid for a family/template."""
    family_id: str
    template_id: Optional[str]
    embedding: List[float]
    label: str


class IntentMapper:
    """
    Maps user intents to templates using embedding similarity.
    
    Primary: Embedding similarity search
    Fallback: LLM classification (when confidence < threshold)
    """
    
    def __init__(
        self,
        embedding_model: Any = None,
        similarity_threshold: float = 0.7,
        llm_fallback_threshold: float = 0.5
    ):
        """
        Initialize the intent mapper.
        
        Args:
            embedding_model: Model to embed queries (must have .embed() method)
            similarity_threshold: Minimum similarity for "high" confidence
            llm_fallback_threshold: Below this, use LLM fallback
        """
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
        self.llm_fallback_threshold = llm_fallback_threshold
        self.intent_centroids: List[IntentCentroid] = []
    
    def add_intent(
        self,
        family_id: str,
        embedding: List[float],
        label: str,
        template_id: Optional[str] = None
    ) -> None:
        """
        Add an intent centroid to the mapper.
        
        Args:
            family_id: Family this intent belongs to
            embedding: Embedding vector for the intent
            label: Human-readable label
            template_id: Optional specific template ID
        """
        self.intent_centroids.append(IntentCentroid(
            family_id=family_id,
            template_id=template_id,
            embedding=embedding,
            label=label
        ))
    
    def load_intents(self, intents: List[Dict]) -> None:
        """
        Load multiple intents from a list of dicts.
        
        Args:
            intents: List of intent dictionaries
        """
        for intent in intents:
            self.intent_centroids.append(IntentCentroid(
                family_id=intent["family_id"],
                template_id=intent.get("template_id"),
                embedding=intent["embedding"],
                label=intent["label"]
            ))
    
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def match(
        self,
        query_embedding: List[float],
        top_k: int = 1
    ) -> List[IntentMatch]:
        """
        Match a query embedding to the best templates.
        
        Args:
            query_embedding: Embedding of the user's query/intent
            top_k: Number of top matches to return
            
        Returns:
            List of IntentMatch objects sorted by similarity
        """
        if not self.intent_centroids:
            return []
        
        # Calculate similarities
        scores = []
        for centroid in self.intent_centroids:
            sim = self._cosine_similarity(query_embedding, centroid.embedding)
            scores.append((centroid, sim))
        
        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to IntentMatch objects
        matches = []
        for centroid, sim in scores[:top_k]:
            confidence = self._get_confidence(sim)
            matches.append(IntentMatch(
                template_id=centroid.template_id or "",
                family_id=centroid.family_id,
                similarity_score=sim,
                confidence=confidence
            ))
        
        return matches
    
    def _get_confidence(self, similarity: float) -> str:
        """Determine confidence level from similarity score."""
        if similarity >= self.similarity_threshold:
            return "high"
        elif similarity >= self.llm_fallback_threshold:
            return "medium"
        return "low"
    
    def match_with_text(
        self,
        query_text: str,
        top_k: int = 1
    ) -> List[IntentMatch]:
        """
        Match a text query to templates (embeds the query first).
        
        Args:
            query_text: The user's text query
            top_k: Number of top matches to return
            
        Returns:
            List of IntentMatch objects
            
        Raises:
            ValueError: If no embedding model is configured
        """
        if self.embedding_model is None:
            raise ValueError("No embedding model configured. Use match() with pre-computed embeddings.")
        
        query_embedding = self.embedding_model.embed(query_text)
        return self.match(query_embedding, top_k)
    
    async def match_with_llm_fallback(
        self,
        query_text: str,
        llm_client: Any,
        template_descriptions: Dict[str, str],
        model: str = "gpt-4.1-mini"
    ) -> IntentMatch:
        """
        Match intent with LLM fallback for low-confidence cases.
        
        Args:
            query_text: The user's text query
            llm_client: LLM client for fallback classification
            template_descriptions: Dict of template_id -> description
            model: Model for LLM fallback
            
        Returns:
            Best IntentMatch (from embedding or LLM)
        """
        # First try embedding match
        matches = self.match_with_text(query_text, top_k=1)
        
        if matches and matches[0].confidence != "low":
            return matches[0]
        
        # LLM fallback
        template_list = "\n".join([
            f"- {tid}: {desc}" 
            for tid, desc in template_descriptions.items()
        ])
        
        prompt = f"""Given the user intent below, select the most appropriate template.

User Intent: {query_text}

Available Templates:
{template_list}

Respond with ONLY the template ID that best matches the intent."""

        response = await llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        
        selected_id = response.choices[0].message.content.strip()
        
        # Find the corresponding family
        for centroid in self.intent_centroids:
            if centroid.template_id == selected_id:
                return IntentMatch(
                    template_id=selected_id,
                    family_id=centroid.family_id,
                    similarity_score=0.0,  # LLM match, no embedding score
                    confidence="llm_fallback"
                )
        
        # Default if not found
        return IntentMatch(
            template_id=selected_id,
            family_id="",
            similarity_score=0.0,
            confidence="llm_fallback"
        )
