"""
Keywords API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)

from core.database import get_db
from models import Keyword, Project, Ranking, User
from api.auth import get_current_user
from services.dataforseo.client import DataForSEOClient
from services.ml_predictive_seo_service import PredictiveSEOService
from core.redis_client import redis_client

router = APIRouter()

# Pydantic models
class KeywordCreate(BaseModel):
    keyword: str
    project_id: str
    target_position: Optional[int] = None
    priority: str = "medium"
    tags: List[str] = []

class KeywordUpdate(BaseModel):
    target_position: Optional[int] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None

class KeywordResponse(BaseModel):
    id: str
    keyword: str
    search_volume: Optional[int]
    difficulty: Optional[float]
    cpc: Optional[float]
    current_position: Optional[int]
    target_position: Optional[int]
    priority: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime

class KeywordAnalysisResponse(BaseModel):
    keyword: str
    search_volume: int
    difficulty: float
    cpc: float
    competition: float
    trends: dict
    suggestions: List[str]

class RankingResponse(BaseModel):
    id: str
    position: int
    url: str
    title: str
    recorded_at: datetime
    serp_features: List[str]

class BulkKeywordRequest(BaseModel):
    keywords: List[str]
    project_id: str

# Helper functions
def get_user_project(project_id: str, user: User, db: Session):
    """Get project and verify user access"""
    project = db.query(Project).filter(
        and_(Project.id == project_id, Project.org_id == user.org_id)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

async def analyze_keyword_data(keyword: str) -> dict:
    """Analyze keyword using DataForSEO with comprehensive data"""
    try:
        # Check cache first
        cache_key = f"keyword_analysis:{keyword}"
        cached_data = await redis_client.get_cached_response(cache_key)
        if cached_data:
            return cached_data
        
        # Initialize DataForSEO client
        async with DataForSEOClient() as dataforseo:
            # Get multiple data points in parallel
            tasks = [
                dataforseo.get_keyword_data([keyword]),
                dataforseo.get_keyword_suggestions(keyword, limit=10),
                dataforseo.get_related_keywords(keyword, limit=5)
            ]
            
            keyword_data, suggestions_data, related_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Parse main keyword data
            analysis = {
                "search_volume": 0,
                "difficulty": 0,
                "cpc": 0,
                "competition": 0,
                "trends": {},
                "suggestions": []
            }
            
            # Process keyword data
            if keyword_data and not isinstance(keyword_data, Exception):
                if keyword_data.get("tasks") and keyword_data["tasks"]:
                    task_result = keyword_data["tasks"][0].get("result", [])
                    if task_result:
                        data = task_result[0]
                        analysis.update({
                            "search_volume": data.get("search_volume", 0),
                            "difficulty": data.get("keyword_difficulty", 0),
                            "cpc": data.get("cpc", 0),
                            "competition": data.get("competition_level", 0),
                            "trends": data.get("monthly_searches", {})
                        })
            
            # Process suggestions
            if suggestions_data and not isinstance(suggestions_data, Exception):
                if suggestions_data.get("tasks") and suggestions_data["tasks"]:
                    suggestions_result = suggestions_data["tasks"][0].get("result", [])
                    if suggestions_result:
                        suggestions = []
                        for item in suggestions_result[0].get("items", [])[:10]:
                            suggestions.append(item.get("keyword", ""))
                        analysis["suggestions"] = [s for s in suggestions if s]
            
            # Add related keywords to suggestions if available
            if related_data and not isinstance(related_data, Exception):
                if related_data.get("tasks") and related_data["tasks"]:
                    related_result = related_data["tasks"][0].get("result", [])
                    if related_result:
                        for item in related_result[0].get("items", [])[:5]:
                            related_keyword = item.get("keyword", "")
                            if related_keyword and related_keyword not in analysis["suggestions"]:
                                analysis["suggestions"].append(related_keyword)
        
        # Cache for 24 hours
        await redis_client.cache_response(cache_key, analysis, 86400)
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing keyword {keyword}: {e}")
        return {
            "search_volume": 0,
            "difficulty": 0,
            "cpc": 0,
            "competition": 0,
            "trends": {},
            "suggestions": []
        }

# API endpoints
@router.post("/", response_model=KeywordResponse)
async def create_keyword(
    keyword_data: KeywordCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Create a new keyword"""
    
    # Verify project access
    project = get_user_project(keyword_data.project_id, current_user, db)
    
    # Check if keyword already exists in project
    existing = db.query(Keyword).filter(
        and_(
            Keyword.project_id == keyword_data.project_id,
            Keyword.keyword == keyword_data.keyword
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists in this project")
    
    # Create keyword
    keyword = Keyword(
        project_id=keyword_data.project_id,
        keyword=keyword_data.keyword,
        target_position=keyword_data.target_position,
        priority=keyword_data.priority,
        tags=keyword_data.tags
    )
    
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    
    # Analyze keyword data in background
    background_tasks.add_task(update_keyword_analysis, str(keyword.id), keyword_data.keyword)
    
    return {
        "id": str(keyword.id),
        "keyword": keyword.keyword,
        "search_volume": keyword.search_volume,
        "difficulty": keyword.difficulty,
        "cpc": keyword.cpc,
        "current_position": keyword.current_position,
        "target_position": keyword.target_position,
        "priority": keyword.priority,
        "tags": keyword.tags,
        "created_at": keyword.created_at,
        "updated_at": keyword.updated_at
    }

@router.get("/", response_model=List[KeywordResponse])
async def get_keywords(
    project_id: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get keywords for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Build query
    query = db.query(Keyword).filter(Keyword.project_id == project_id)
    
    if search:
        query = query.filter(Keyword.keyword.ilike(f"%{search}%"))
    
    if priority:
        query = query.filter(Keyword.priority == priority)
    
    # Get keywords
    keywords = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(k.id),
            "keyword": k.keyword,
            "search_volume": k.search_volume,
            "difficulty": k.difficulty,
            "cpc": k.cpc,
            "current_position": k.current_position,
            "target_position": k.target_position,
            "priority": k.priority,
            "tags": k.tags,
            "created_at": k.created_at,
            "updated_at": k.updated_at
        }
        for k in keywords
    ]

@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific keyword"""
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # Verify access through project
    get_user_project(str(keyword.project_id), current_user, db)
    
    return {
        "id": str(keyword.id),
        "keyword": keyword.keyword,
        "search_volume": keyword.search_volume,
        "difficulty": keyword.difficulty,
        "cpc": keyword.cpc,
        "current_position": keyword.current_position,
        "target_position": keyword.target_position,
        "priority": keyword.priority,
        "tags": keyword.tags,
        "created_at": keyword.created_at,
        "updated_at": keyword.updated_at
    }

@router.put("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: str,
    keyword_data: KeywordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a keyword"""
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # Verify access
    get_user_project(str(keyword.project_id), current_user, db)
    
    # Update fields
    if keyword_data.target_position is not None:
        keyword.target_position = keyword_data.target_position
    if keyword_data.priority:
        keyword.priority = keyword_data.priority
    if keyword_data.tags is not None:
        keyword.tags = keyword_data.tags
    
    keyword.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(keyword)
    
    return {
        "id": str(keyword.id),
        "keyword": keyword.keyword,
        "search_volume": keyword.search_volume,
        "difficulty": keyword.difficulty,
        "cpc": keyword.cpc,
        "current_position": keyword.current_position,
        "target_position": keyword.target_position,
        "priority": keyword.priority,
        "tags": keyword.tags,
        "created_at": keyword.created_at,
        "updated_at": keyword.updated_at
    }

@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a keyword"""
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # Verify access
    get_user_project(str(keyword.project_id), current_user, db)
    
    db.delete(keyword)
    db.commit()
    
    return {"message": "Keyword deleted successfully"}

@router.post("/analyze", response_model=KeywordAnalysisResponse)
async def analyze_keyword(
    keyword: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze a keyword before adding it"""
    
    analysis = await analyze_keyword_data(keyword)
    
    return {
        "keyword": keyword,
        "search_volume": analysis["search_volume"],
        "difficulty": analysis["difficulty"],
        "cpc": analysis["cpc"],
        "competition": analysis["competition"],
        "trends": analysis["trends"],
        "suggestions": analysis["suggestions"]
    }

@router.post("/bulk", response_model=dict)
async def bulk_add_keywords(
    request: BulkKeywordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk add keywords to a project"""
    
    # Verify project access
    project = get_user_project(request.project_id, current_user, db)
    
    # Get existing keywords
    existing_keywords = db.query(Keyword.keyword).filter(
        Keyword.project_id == request.project_id
    ).all()
    existing_set = {k.keyword for k in existing_keywords}
    
    # Filter new keywords
    new_keywords = [k for k in request.keywords if k not in existing_set]
    
    # Create keyword records
    keyword_objects = []
    for keyword_text in new_keywords:
        keyword = Keyword(
            project_id=request.project_id,
            keyword=keyword_text
        )
        keyword_objects.append(keyword)
    
    db.add_all(keyword_objects)
    db.commit()
    
    # Analyze keywords in background
    for keyword_obj in keyword_objects:
        background_tasks.add_task(
            update_keyword_analysis, 
            str(keyword_obj.id), 
            keyword_obj.keyword
        )
    
    return {
        "message": f"Added {len(new_keywords)} new keywords",
        "added": len(new_keywords),
        "skipped": len(request.keywords) - len(new_keywords),
        "total": len(request.keywords)
    }

@router.get("/{keyword_id}/rankings", response_model=List[RankingResponse])
async def get_keyword_rankings(
    keyword_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ranking history for a keyword"""
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # Verify access
    get_user_project(str(keyword.project_id), current_user, db)
    
    # Get rankings from the last N days
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    rankings = db.query(Ranking).filter(
        and_(
            Ranking.keyword_id == keyword_id,
            Ranking.recorded_at >= cutoff_date
        )
    ).order_by(desc(Ranking.recorded_at)).all()
    
    return [
        {
            "id": str(r.id),
            "position": r.position,
            "url": r.url,
            "title": r.title,
            "recorded_at": r.recorded_at,
            "serp_features": r.serp_features
        }
        for r in rankings
    ]

@router.post("/{keyword_id}/predict")
async def predict_keyword_ranking(
    keyword_id: str,
    days_ahead: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict future rankings for a keyword using ML"""
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # Verify access
    get_user_project(str(keyword.project_id), current_user, db)
    
    try:
        # Get historical ranking data
        rankings = db.query(Ranking).filter(
            Ranking.keyword_id == keyword_id
        ).order_by(Ranking.recorded_at).all()
        
        # Initialize ML service
        ml_service = PredictiveSEOService()
        
        # Prepare training data
        if len(rankings) >= 7:  # Need at least a week of data
            historical_data = [
                {
                    "date": r.recorded_at.isoformat(),
                    "position": r.position,
                    "search_volume": keyword.search_volume or 1000,
                    "difficulty": keyword.difficulty or 50,
                    "competition": keyword.competition or 0.5
                }
                for r in rankings
            ]
            
            # Get prediction
            prediction_result = await ml_service.predict_keyword_ranking(
                keyword_data={
                    "keyword": keyword.keyword,
                    "current_position": keyword.current_position or 50,
                    "search_volume": keyword.search_volume or 1000,
                    "difficulty": keyword.difficulty or 50,
                    "target_position": keyword.target_position or 10
                },
                historical_data=historical_data,
                days_ahead=days_ahead
            )
            
            return prediction_result
            
        else:
            # Not enough data - return baseline prediction
            current_pos = keyword.current_position or 50
            target_pos = keyword.target_position or 10
            
            # Simple trend calculation
            improvement_rate = (current_pos - target_pos) / days_ahead if current_pos > target_pos else 0
            
            predictions = []
            for i in range(1, min(days_ahead + 1, 13)):  # Up to 12 predictions
                days_out = i * (days_ahead // 12) if days_ahead > 12 else i * 7
                predicted_pos = max(target_pos, current_pos - (improvement_rate * days_out))
                confidence = max(0.3, 0.9 - (i * 0.05))  # Decreasing confidence over time
                
                future_date = datetime.utcnow() + timedelta(days=days_out)
                predictions.append({
                    "date": future_date.strftime("%Y-%m-%d"),
                    "position": round(predicted_pos, 1),
                    "confidence": round(confidence, 2)
                })
            
            # Calculate probabilities based on target and difficulty
            difficulty_factor = (keyword.difficulty or 50) / 100
            prob_top_10 = max(0.1, 0.8 - difficulty_factor) if target_pos <= 10 else 0.3
            prob_top_3 = max(0.05, 0.4 - difficulty_factor) if target_pos <= 3 else 0.1
            
            return {
                "keyword": keyword.keyword,
                "current_position": current_pos,
                "target_position": target_pos,
                "predictions": predictions,
                "probability_top_10": round(prob_top_10, 2),
                "probability_top_3": round(prob_top_3, 2),
                "factors": {
                    "content_quality": 0.25,
                    "backlinks": 0.25,
                    "technical_seo": 0.20,
                    "user_experience": 0.15,
                    "competition": 0.15
                },
                "confidence_note": "Limited historical data available. Predictions based on keyword difficulty and target position."
            }
            
    except Exception as e:
        logger.error(f"Error predicting ranking for keyword {keyword_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate ranking prediction")

# Background tasks
async def update_keyword_analysis(keyword_id: str, keyword_text: str):
    """Background task to update keyword analysis"""
    try:
        analysis = await analyze_keyword_data(keyword_text)
        
        # Update database (need to create new session for background task)
        from core.database import SessionLocal
        db = SessionLocal()
        
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            keyword.search_volume = analysis["search_volume"]
            keyword.difficulty = analysis["difficulty"]
            keyword.cpc = analysis["cpc"]
            keyword.competition = analysis["competition"]
            keyword.data = analysis
            keyword.updated_at = datetime.utcnow()
            
            db.commit()
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error updating keyword analysis for {keyword_id}: {e}")

async def update_keyword_rankings(project_id: str):
    """Background task to update keyword rankings for a project"""
    try:
        from core.database import SessionLocal
        db = SessionLocal()
        
        # Get project and domain
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return
        
        # Get all keywords for the project
        keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
        
        if not keywords:
            logger.info(f"No keywords found for project {project_id}")
            return
        
        async with DataForSEOClient() as dataforseo:
            for keyword in keywords:
                try:
                    # Get SERP results for the keyword
                    serp_data = await dataforseo.get_serp_results(keyword.keyword)
                    
                    if serp_data and serp_data.get("tasks"):
                        task_result = serp_data["tasks"][0].get("result", [])
                        if task_result:
                            organic_results = task_result[0].get("items", [])
                            
                            # Find our domain in results
                            position = None
                            url = ""
                            title = ""
                            serp_features = []
                            
                            for i, result in enumerate(organic_results):
                                if result.get("domain") == project.domain:
                                    position = i + 1
                                    url = result.get("url", "")
                                    title = result.get("title", "")
                                    break
                            
                            # Extract SERP features
                            if task_result[0].get("feature_snippets"):
                                serp_features.append("featured_snippet")
                            if task_result[0].get("knowledge_graph"):
                                serp_features.append("knowledge_graph")
                            if task_result[0].get("local_pack"):
                                serp_features.append("local_pack")
                            
                            # Update keyword position
                            if position:
                                keyword.current_position = position
                                keyword.updated_at = datetime.utcnow()
                                
                                # Create ranking record
                                ranking = Ranking(
                                    keyword_id=keyword.id,
                                    position=position,
                                    url=url,
                                    title=title,
                                    serp_features=serp_features,
                                    recorded_at=datetime.utcnow()
                                )
                                db.add(ranking)
                            
                    # Small delay between requests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error updating ranking for keyword {keyword.keyword}: {e}")
                    continue
        
        db.commit()
        db.close()
        logger.info(f"Updated rankings for {len(keywords)} keywords in project {project_id}")
        
    except Exception as e:
        logger.error(f"Error updating keyword rankings for project {project_id}: {e}")

# Add endpoint to trigger ranking updates
@router.post("/refresh-rankings")
async def refresh_keyword_rankings(
    project_id: str = Query(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger keyword ranking updates for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Add background task
    background_tasks.add_task(update_keyword_rankings, project_id)
    
    return {
        "message": "Keyword ranking update started",
        "project_id": project_id,
        "project_name": project.name
    }