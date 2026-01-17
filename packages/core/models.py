"""
Domain models for Prompt Classification & Template System
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class PromptStructure(BaseModel):
    """Structural components of a prompt."""
    system_message: Optional[str] = None
    user_message: Optional[str] = None
    assistant_prefill: Optional[str] = None
    total_tokens: int = 0


class PromptVariables(BaseModel):
    """Detected variables in a prompt."""
    detected: List[str] = Field(default_factory=list)
    slots: int = 0


class PromptInstructions(BaseModel):
    """Extracted instructions and constraints."""
    tone: List[str] = Field(default_factory=list)
    format: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    examples_count: int = 0


class PromptDNA(BaseModel):
    """
    Extracted "DNA" of a prompt: structure, variables, instructions, embedding.
    Used for clustering and template extraction.
    """
    id: str
    raw_text: str
    hash: str
    structure: PromptStructure
    variables: PromptVariables
    instructions: PromptInstructions
    embedding: List[float] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalTemplate(BaseModel):
    """Canonical template extracted from a cluster of prompts."""
    text: str
    variables: List[str] = Field(default_factory=list)
    example_values: Dict[str, List[str]] = Field(default_factory=dict)


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
    simhash: Optional[str] = None
    
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
