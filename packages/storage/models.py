"""
SQLAlchemy models for database tables
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from packages.storage.database import Base


class PromptModel(Base):
    """Database model for prompts"""
    __tablename__ = "prompts"
    
    id = Column(String, primary_key=True)
    raw_text = Column(Text, nullable=False)
    hash = Column(String, unique=True, nullable=False, index=True)
    dna_json = Column(JSON)  # Serialized PromptDNA
    family_id = Column(String, ForeignKey("families.id"), nullable=True, index=True)
    parent_id = Column(String, ForeignKey("prompts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    family = relationship("FamilyModel", back_populates="members")
    parent = relationship("PromptModel", remote_side=[id])


class FamilyModel(Base):
    """Database model for prompt families"""
    __tablename__ = "families"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    canonical_template_json = Column(JSON)  # Serialized CanonicalTemplate
    member_count = Column(Integer, default=0)
    statistics = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("PromptModel", back_populates="family")


class LineageModel(Base):
    """Database model for evolution tracking"""
    __tablename__ = "lineage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(String, ForeignKey("prompts.id"), nullable=False)
    parent_id = Column(String, ForeignKey("prompts.id"), nullable=False)
    mutation_type = Column(String)  # "exact_match", "variant", "new_family"
    confidence = Column(String)  # Store as string for flexibility
    timestamp = Column(DateTime, default=datetime.utcnow)


class ProcessingLogModel(Base):
    """Database model for processing batches"""
    __tablename__ = "processing_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String, unique=True, nullable=False)
    status = Column(String)  # "pending", "processing", "completed", "failed"
    prompts_processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
