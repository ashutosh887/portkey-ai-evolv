"""
Domain models for Prompt Classification & Template System
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class PromptFamily(BaseModel):
    """
    PromptFamily (Cluster Level)
    Represents a semantic cluster of similar prompts (a "family").
    """
    family_id: str
    family_name: str
    description: Optional[str] = None
    member_count: int = 0
    centroid_vector: Optional[List[float]] = None
    version: int = 1
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PromptInstance(BaseModel):
    """
    PromptInstance (Individual Prompt Level)
    Stores raw and processed prompts, meta info, and their family assignments.
    """
    prompt_id: str
    original_text: str
    normalized_text: Optional[str] = None
    dedup_hash: Optional[str] = None
    simhash: Optional[str] = None  # 64-bit SimHash fingerprint as hex string
    
    embedding_vector: Optional[List[float]] = None
    similarity_score: Optional[float] = None
    
    family_id: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_template_seed: bool = False
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Template(BaseModel):
    """
    Template (Extracted Template Level)
    Stores the canonical prompt templates derived from each family.
    """
    template_id: str
    family_id: str
    
    template_text: str
    slots: Dict[str, Any] = Field(default_factory=dict)
    examples: List[str] = Field(default_factory=list)
    
    template_version: int = 1
    quality_score: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
