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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    members = relationship("PromptInstance", back_populates="family")
    templates = relationship("Template", back_populates="family")


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
    """
    __tablename__ = "templates"
    
    template_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    family_id = Column(String, ForeignKey("prompt_families.family_id"), nullable=False, index=True)
    
    template_text = Column(Text, nullable=False)
    slots = Column(JSON, default={})
    
    template_version = Column(Integer, default=1)
    quality_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    family = relationship("PromptFamily", back_populates="templates")
