"""
Domain models for Prompt DNA and Families
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PromptStructure(BaseModel):
    """Structural components of a prompt"""
    system_message: Optional[str] = None
    user_message: str
    assistant_prefill: Optional[str] = None
    total_tokens: int = 0


class PromptVariables(BaseModel):
    """Detected variables in a prompt"""
    detected: list[str] = Field(default_factory=list)
    slots: int = 0


class PromptInstructions(BaseModel):
    """Extracted instructions and constraints"""
    tone: list[str] = Field(default_factory=list)
    format: Optional[str] = None  # "JSON", "markdown", "plain", etc.
    constraints: list[str] = Field(default_factory=list)
    examples_count: int = 0


class PromptDNA(BaseModel):
    """Complete DNA representation of a prompt"""
    id: str
    raw_text: str
    hash: str  # SHA256 for deduplication
    
    structure: PromptStructure
    variables: PromptVariables
    instructions: PromptInstructions
    
    embedding: list[float]  # Semantic embedding vector
    
    metadata: dict = Field(default_factory=dict)
    family_id: Optional[str] = None
    parent_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CanonicalTemplate(BaseModel):
    """Canonical template extracted from a prompt family"""
    text: str  # Template with {{variable}} slots
    variables: list[str]
    example_values: dict[str, list[str]] = Field(default_factory=dict)


class PromptFamily(BaseModel):
    """A family of related prompts"""
    id: str
    name: str
    description: str
    
    canonical_template: CanonicalTemplate
    
    members: list[str]  # PromptDNA IDs
    member_count: int
    
    statistics: dict = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
