"""
Project, Keyword, Ranking, and Campaign models
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database import Base


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    description = Column(Text)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    keywords = relationship("Keyword", back_populates="project")
    campaigns = relationship("Campaign", back_populates="project")


class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer)
    difficulty = Column(Float)
    cpc = Column(Float)
    competition = Column(Float)
    current_position = Column(Integer)
    target_position = Column(Integer)
    priority = Column(String(20), default="medium")
    tags = Column(JSON, default=[])
    data = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="keywords")
    rankings = relationship("Ranking", back_populates="keyword")


class Ranking(Base):
    __tablename__ = "rankings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("keywords.id"))
    position = Column(Integer)
    url = Column(Text)
    title = Column(Text)
    description = Column(Text)
    serp_features = Column(JSON, default=[])
    competitors = Column(JSON, default=[])
    location = Column(String(100))
    device = Column(String(20), default="desktop")
    search_engine = Column(String(20), default="google")
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    keyword = relationship("Keyword", back_populates="rankings")


class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    campaign_type = Column(String(50))  # seo, ppc, content
    status = Column(String(20), default="active")
    budget = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    goals = Column(JSON, default=[])
    metrics = Column(JSON, default={})
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="campaigns")