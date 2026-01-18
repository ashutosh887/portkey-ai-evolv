"""
SQLAlchemy models for database tables
"""

import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from packages.storage.database import Base


class PromptFamily(Base):
    """
    PromptFamily (Cluster Level)
    Represents a semantic cluster of similar prompts (a "family").
    """
    __tablename__ = "prompt_families"
    
    family_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    family_name = Column(String, nullable=False)
    description = Column(Text)
    member_count = Column(Integer, default=0)
    centroid_vector = Column(JSON)
    version = Column(Integer, default=1)
    
    # Template update tracking (threshold-based trigger)
    member_count_at_last_template = Column(Integer, default=0)  # Count when last template was generated
    needs_template_update = Column(Boolean, default=True, index=True)  # Flag for pending update
    template_update_threshold = Column(Integer, default=5)  # How many new prompts trigger update
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    members = relationship("PromptInstance", back_populates="family")
    templates = relationship("Template", back_populates="family")
    
    def check_needs_template_update(self) -> bool:
        """Check if family needs a template update based on threshold."""
        new_members = self.member_count - self.member_count_at_last_template
        return new_members >= self.template_update_threshold or self.needs_template_update


class PromptInstance(Base):
    """
    PromptInstance (Individual Prompt Level)
    Stores raw and processed prompts, meta info, and their family assignments.
    """
    __tablename__ = "prompt_instances"
    
    prompt_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_text = Column(Text, nullable=False)
    normalized_text = Column(Text, index=True)
    dedup_hash = Column(String, index=True)
    simhash = Column(String, index=True)
    
    embedding_vector = Column(JSON)
    similarity_score = Column(Float)
    
    family_id = Column(String, ForeignKey("prompt_families.family_id"), nullable=True, index=True)
    
    metadata_ = Column(JSON, default={})
    is_template_seed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    family = relationship("PromptFamily", back_populates="members")


class Template(Base):
    """
    Template (Extracted Template Level)
    Stores the canonical prompt templates derived from each family.
    
    IMMUTABLE VERSIONING: Each new version creates a NEW ROW with parent_template_id
    pointing to the previous version. This preserves full history.
    """
    __tablename__ = "templates"
    
    template_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    family_id = Column(String, ForeignKey("prompt_families.family_id"), nullable=False, index=True)
    
    # Version tracking (immutable - new row per version)
    parent_template_id = Column(String, ForeignKey("templates.template_id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)  # Current "live" version
    
    template_text = Column(Text, nullable=False)
    slots = Column(JSON, default={})  # Slot definitions
    
    # Semantic versioning
    version_major = Column(Integer, default=1)
    version_minor = Column(Integer, default=0)
    version_patch = Column(Integer, default=0)
    
    # Quality and refinement
    quality_score = Column(Float)
    is_refined = Column(Boolean, default=False)  # True if LLM-refined
    
    # Intent mapping
    intent_embedding = Column(JSON)  # Vector for intent matching
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    family = relationship("PromptFamily", back_populates="templates")


class Lineage(Base):
    """
    Lineage (Evolution Tracking)
    Tracks parent-child relationships between prompts to build evolution chains.
    """
    __tablename__ = "lineage"
    
    lineage_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_prompt_id = Column(String, ForeignKey("prompt_instances.prompt_id"), nullable=True, index=True)
    child_prompt_id = Column(String, ForeignKey("prompt_instances.prompt_id"), nullable=False, index=True)
    mutation_type = Column(String, nullable=False)
    confidence = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("PromptInstance", foreign_keys=[parent_prompt_id], backref="children")
    child = relationship("PromptInstance", foreign_keys=[child_prompt_id], backref="parents")
