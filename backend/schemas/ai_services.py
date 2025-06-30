"""
Pydantic schemas for AI services
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Vision Analysis Schemas
class VisionAnalysisRequest(BaseModel):
    image_url: Optional[str] = None
    keyword: Optional[str] = None
    analysis_type: str = "serp"  # serp, competitor, layout

class VisionAnalysisResponse(BaseModel):
    keyword: Optional[str]
    url: Optional[str]
    analysis: Dict[str, Any]
    timestamp: datetime

# Content Generation Schemas
class ContentGenerationRequest(BaseModel):
    content_type: str  # blog, product, landing_page, email, social
    topic: str
    keywords: List[str]
    tone: str = "professional"  # professional, casual, technical, sales
    length: int = 1000  # target word count
    additional_instructions: Optional[str] = None

class ContentGenerationResponse(BaseModel):
    content: str
    meta_title: Optional[str]
    meta_description: Optional[str]
    word_count: int
    reading_time: int  # in minutes
    seo_score: float

class BulkContentItem(BaseModel):
    topic: str
    keywords: List[str]
    custom_fields: Dict[str, Any] = {}

class ContentTemplate(BaseModel):
    name: str
    content_type: str
    structure: Dict[str, Any]
    variables: List[str]

class BulkContentRequest(BaseModel):
    items: List[BulkContentItem]
    template: Optional[ContentTemplate] = None
    content_type: str = "blog"
    tone: str = "professional"

# Voice Search Schemas
class VoiceOptimizationRequest(BaseModel):
    content: str
    target_queries: List[str]
    location: Optional[str] = None
    language: str = "en"

class VoiceOptimizationResponse(BaseModel):
    optimized_content: str
    voice_snippets: List[str]
    faq_schema: Dict[str, Any]
    natural_language_variations: List[str]
    optimization_score: float

# Chat Schemas
class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str]
    relevant_data: Dict[str, Any]
    session_id: str

# SEO Analysis Schemas  
class SEOAnalysisRequest(BaseModel):
    url: str
    keywords: List[str]
    competitors: Optional[List[str]] = []

class SEOAnalysisResponse(BaseModel):
    url: str
    seo_score: float
    technical_issues: List[Dict[str, Any]]
    content_analysis: Dict[str, Any]
    competitor_comparison: Dict[str, Any]
    recommendations: List[str]

# Content Optimization Schemas
class ContentOptimizationRequest(BaseModel):
    content: str
    target_keywords: List[str]
    content_type: str = "blog"

class ContentOptimizationResponse(BaseModel):
    optimized_content: str
    keyword_density: Dict[str, float]
    readability_score: float
    suggested_headings: List[str]
    internal_linking_suggestions: List[Dict[str, str]]
    optimization_tips: List[str]