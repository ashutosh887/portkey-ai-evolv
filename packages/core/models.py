"""
Domain models for Prompt Classification & Template System
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


def utcnow():
    """Get current UTC datetime (compatible with Python 3.11+)"""
    return datetime.now(timezone.utc)


class SlotType(str, Enum):
    """Types of template slots."""
    NUMERIC = "numeric"
    ENUM = "enum"
    TEXT = "text"
    DATE = "date"
    EMAIL = "email"
    URL = "url"


class Slot(BaseModel):
    """Represents a variable slot in a template."""
    name: str
    slot_type: SlotType
    position: int
    examples: List[str] = Field(default_factory=list)
    enum_values: Optional[List[str]] = None
    validation_pattern: Optional[str] = None
    description: Optional[str] = None
    required: bool = True
    default_value: Optional[str] = None


class TemplateVersion(BaseModel):
    """Semantic version for a template."""
    major: int = 1
    minor: int = 0
    patch: int = 0
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def from_string(cls, version_str: str) -> "TemplateVersion":
        parts = version_str.split('.')
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 1,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0
        )


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
    
    # Template update tracking (threshold-based trigger)
    member_count_at_last_template: int = 0
    needs_template_update: bool = True
    template_update_threshold: int = 5
    
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    
    def check_needs_template_update(self) -> bool:
        """Check if family needs a template update based on threshold."""
        new_members = self.member_count - self.member_count_at_last_template
        return new_members >= self.template_update_threshold or self.needs_template_update


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
    
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Template(BaseModel):
    """
    Template (Extracted Template Level)
    Stores the canonical prompt templates derived from each family.
    
    IMMUTABLE VERSIONING: Each new version creates a NEW record with parent_template_id
    pointing to the previous version. This preserves full history.
    """
    template_id: str
    family_id: str
    
    # Version tracking (immutable - new record per version)
    parent_template_id: Optional[str] = None
    is_active: bool = True
    
    template_text: str
    slots: List[Slot] = Field(default_factory=list)
    
    # Semantic versioning
    version_major: int = 1
    version_minor: int = 0
    version_patch: int = 0
    
    # Quality and refinement
    quality_score: Optional[float] = None
    is_refined: bool = False
    
    # Intent mapping
    intent_embedding: Optional[List[float]] = None
    
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    
    @property
    def version_string(self) -> str:
        """Return version as string like '1.2.3'."""
        return f"{self.version_major}.{self.version_minor}.{self.version_patch}"
    
    def get_version(self) -> TemplateVersion:
        """Get version as TemplateVersion object."""
        return TemplateVersion(
            major=self.version_major,
            minor=self.version_minor,
            patch=self.version_patch
        )
