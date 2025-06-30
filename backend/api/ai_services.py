"""
AI Services API endpoints
Handles AI vision, content generation, voice search optimization, and LLM chat
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import json

from core.deps import get_db, get_current_user
from models.user import User
from services.ai_vision_service import AIVisionService
from services.content_generation_service import ContentGenerationService
from services.voice_search_service import VoiceSearchService
from services.llm_chat_service import LLMChatService
from schemas.ai_services import (
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    ContentGenerationRequest,
    ContentGenerationResponse,
    VoiceOptimizationRequest,
    VoiceOptimizationResponse,
    ChatMessage,
    ChatResponse,
    BulkContentRequest,
    ContentTemplate
)

router = APIRouter()

# Service dependency functions
def get_vision_service() -> AIVisionService:
    from core.config import settings
    return AIVisionService(openai_api_key=settings.OPENAI_API_KEY)

def get_content_service() -> ContentGenerationService:
    return ContentGenerationService()

def get_voice_service() -> VoiceSearchService:
    return VoiceSearchService()

def get_chat_service() -> LLMChatService:
    return LLMChatService()

@router.post("/vision/analyze-serp", response_model=VisionAnalysisResponse)
async def analyze_serp_screenshot(
    file: UploadFile = File(...),
    keyword: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    vision_service: AIVisionService = Depends(get_vision_service)
):
    """
    Analyze a SERP screenshot using GPT-4 Vision
    """
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Analyze with AI Vision
        analysis = await vision_service.analyze_serp_screenshot(tmp_path, keyword)
        
        # Clean up
        os.unlink(tmp_path)
        
        # Save analysis to database
        from models.analysis import VisionAnalysis
        db_analysis = VisionAnalysis(
            user_id=current_user.id,
            keyword=keyword,
            analysis_data=json.dumps(analysis),
            created_at=datetime.utcnow()
        )
        db.add(db_analysis)
        db.commit()
        
        return VisionAnalysisResponse(
            keyword=keyword,
            analysis=analysis,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vision/analyze-competitor", response_model=VisionAnalysisResponse)
async def analyze_competitor_page(
    url: str,
    screenshot: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze competitor page layout and content using AI Vision
    """
    try:
        if screenshot:
            # Use provided screenshot
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                content = await screenshot.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            vision_service = get_vision_service()
            analysis = await vision_service.analyze_page_layout(tmp_path, url)
            os.unlink(tmp_path)
        else:
            # Take screenshot of URL
            vision_service = get_vision_service()
            analysis = await vision_service.analyze_competitor_page(url)
        
        return VisionAnalysisResponse(
            url=url,
            analysis=analysis,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate SEO-optimized content using AI
    """
    try:
        content_service = get_content_service()
        # Generate content
        content = await content_service.generate_content(
            content_type=request.content_type,
            topic=request.topic,
            keywords=request.keywords,
            tone=request.tone,
            length=request.length,
            additional_instructions=request.additional_instructions
        )
        
        # Save to database
        from models.content import GeneratedContent
        db_content = GeneratedContent(
            user_id=current_user.id,
            content_type=request.content_type,
            topic=request.topic,
            keywords=",".join(request.keywords),
            content=content['content'],
            meta_title=content.get('meta_title'),
            meta_description=content.get('meta_description'),
            created_at=datetime.utcnow()
        )
        db.add(db_content)
        db.commit()
        
        return ContentGenerationResponse(
            content=content['content'],
            meta_title=content.get('meta_title'),
            meta_description=content.get('meta_description'),
            word_count=content.get('word_count', 0),
            reading_time=content.get('reading_time', 0),
            seo_score=content.get('seo_score', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content/bulk-generate")
async def bulk_generate_content(
    request: BulkContentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate multiple pieces of content in bulk
    """
    try:
        # Create bulk generation job
        from models.jobs import BulkContentJob
        job = BulkContentJob(
            user_id=current_user.id,
            total_items=len(request.items),
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        
        content_service = get_content_service()
        # Add to background tasks
        background_tasks.add_task(
            content_service.bulk_generate,
            job_id=job.id,
            items=request.items,
            template=request.template
        )
        
        return {
            "job_id": job.id,
            "status": "processing",
            "total_items": len(request.items),
            "message": "Bulk content generation started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/optimize", response_model=VoiceOptimizationResponse)
async def optimize_for_voice_search(
    request: VoiceOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize content for voice search
    """
    try:
        voice_service = get_voice_service()
        # Optimize content
        optimization = await voice_service.optimize_for_voice(
            content=request.content,
            target_queries=request.target_queries,
            location=request.location,
            language=request.language
        )
        
        return VoiceOptimizationResponse(
            optimized_content=optimization['optimized_content'],
            voice_snippets=optimization['voice_snippets'],
            faq_schema=optimization['faq_schema'],
            natural_language_variations=optimization['natural_language_variations'],
            optimization_score=optimization['score']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/message", response_model=ChatResponse)
async def chat_with_ai(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    chat_service: LLMChatService = Depends(get_chat_service)
):
    """
    Chat with AI for SEO insights and recommendations
    """
    try:
        # Get chat context
        from models.chat import ChatSession
        session = db.query(ChatSession).filter_by(
            id=message.session_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            # Create new session
            session = ChatSession(
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()
        
        # Get AI response
        response = await chat_service.chat(
            message=message.message,
            context=message.context,
            session_id=session.id
        )
        
        # Save conversation
        from models.chat import ChatMessage as DBChatMessage
        db_message = DBChatMessage(
            session_id=session.id,
            role="user",
            content=message.message,
            created_at=datetime.utcnow()
        )
        db.add(db_message)
        
        db_response = DBChatMessage(
            session_id=session.id,
            role="assistant",
            content=response['response'],
            created_at=datetime.utcnow()
        )
        db.add(db_response)
        db.commit()
        
        return ChatResponse(
            response=response['response'],
            suggestions=response.get('suggestions', []),
            relevant_data=response.get('relevant_data', {}),
            session_id=session.id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions")
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's chat sessions
    """
    from models.chat import ChatSession
    sessions = db.query(ChatSession).filter_by(
        user_id=current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    
    return {
        "sessions": [
            {
                "id": s.id,
                "created_at": s.created_at,
                "last_message": s.messages[-1].content if s.messages else None,
                "message_count": len(s.messages)
            }
            for s in sessions
        ]
    }

@router.get("/chat/session/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get messages from a specific chat session
    """
    from models.chat import ChatSession, ChatMessage as DBChatMessage
    
    session = db.query(ChatSession).filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(DBChatMessage).filter_by(
        session_id=session_id
    ).order_by(DBChatMessage.created_at).all()
    
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at
            }
            for m in messages
        ]
    }

@router.get("/templates")
async def get_content_templates(
    current_user: User = Depends(get_current_user)
):
    """
    Get available content templates
    """
    content_service = get_content_service()
    templates = await content_service.get_templates()
    return {"templates": templates}

@router.post("/templates")
async def create_content_template(
    template: ContentTemplate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a custom content template
    """
    try:
        # Save template
        from models.content import ContentTemplate as DBTemplate
        db_template = DBTemplate(
            user_id=current_user.id,
            name=template.name,
            content_type=template.content_type,
            structure=json.dumps(template.structure),
            variables=json.dumps(template.variables),
            created_at=datetime.utcnow()
        )
        db.add(db_template)
        db.commit()
        
        return {
            "id": db_template.id,
            "message": "Template created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seo/analyze")
async def analyze_seo(
    request: dict,  # Using dict since we need to add the schema
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive SEO analysis of a URL
    """
    try:
        # Mock SEO analysis response for now
        return {
            "url": request.get("url", ""),
            "seo_score": 75.5,
            "technical_issues": [
                {"type": "missing_meta_description", "severity": "medium", "description": "Meta description is missing"},
                {"type": "slow_loading", "severity": "high", "description": "Page load time exceeds 3 seconds"}
            ],
            "content_analysis": {
                "word_count": 1250,
                "readability_score": 68,
                "keyword_density": {"main_keyword": 2.1, "secondary_keyword": 1.3}
            },
            "competitor_comparison": {
                "avg_score": 72,
                "ranking_position": 3,
                "gaps": ["missing schema markup", "low mobile score"]
            },
            "recommendations": [
                "Add meta description",
                "Optimize images for faster loading",
                "Implement schema markup",
                "Improve mobile responsiveness"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content/optimize")
async def optimize_content(
    request: dict,  # Using dict since we need to add the schema
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize existing content for SEO
    """
    try:
        content = request.get("content", "")
        target_keywords = request.get("target_keywords", [])
        
        # Mock content optimization response
        return {
            "optimized_content": content + "\n\n[SEO-optimized version with better keyword placement and structure]",
            "keyword_density": {kw: 2.5 for kw in target_keywords},
            "readability_score": 78.5,
            "suggested_headings": [
                "Introduction to " + target_keywords[0] if target_keywords else "Introduction",
                "Benefits and Features",
                "Best Practices",
                "Conclusion"
            ],
            "internal_linking_suggestions": [
                {"anchor_text": "related article", "url": "/related-content"},
                {"anchor_text": "learn more", "url": "/detailed-guide"}
            ],
            "optimization_tips": [
                "Add more subheadings for better structure",
                "Include target keywords in first paragraph",
                "Add internal links to related content",
                "Optimize for featured snippets with bullet points"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))