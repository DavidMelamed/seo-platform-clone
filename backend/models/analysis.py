"""
Analysis models for AI vision and SEO insights
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from core.database import Base


class VisionAnalysis(Base):
    __tablename__ = "vision_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    keyword = Column(String(255))
    url = Column(Text)
    analysis_type = Column(String(50))  # serp, competitor, layout
    analysis_data = Column(JSON)  # Complete analysis results
    insights = Column(JSON)  # Extracted insights
    recommendations = Column(JSON)  # AI recommendations
    screenshot_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)