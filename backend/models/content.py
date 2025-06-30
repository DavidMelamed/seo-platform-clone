"""
Content generation models
"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database import Base


class GeneratedContent(Base):
    __tablename__ = "generated_content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content_type = Column(String(50))  # blog, product, email, social
    topic = Column(String(500))
    keywords = Column(Text)  # Comma-separated keywords
    content = Column(Text)
    meta_title = Column(String(255))
    meta_description = Column(String(500))
    word_count = Column(Integer)
    reading_time = Column(Integer)  # in minutes
    seo_score = Column(Float)
    tone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContentTemplate(Base):
    __tablename__ = "content_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    content_type = Column(String(50))
    structure = Column(JSON)  # Template structure definition
    variables = Column(JSON)  # Variable placeholders
    is_public = Column(String, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)