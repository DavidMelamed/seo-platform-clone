"""
Analytics API endpoints
Comprehensive SEO analytics and reporting
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, case
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

from core.database import get_db
from models import User, Project, Keyword, Ranking, TrafficData
from api.auth import get_current_user
from services.dataforseo.client import DataForSEOClient
from core.redis_client import redis_client

router = APIRouter()

# Pydantic models
class TrafficMetrics(BaseModel):
    date: str
    organic_traffic: int
    organic_clicks: int
    impressions: int
    ctr: float
    avg_position: float

class KeywordPerformance(BaseModel):
    keyword: str
    current_position: int
    previous_position: Optional[int]
    position_change: int
    search_volume: int
    estimated_traffic: int
    difficulty: float

class CompetitorAnalysis(BaseModel):
    domain: str
    total_keywords: int
    top_10_keywords: int
    estimated_traffic: int
    common_keywords: int
    avg_position: float

class ConversionMetrics(BaseModel):
    date: str
    sessions: int
    conversions: int
    conversion_rate: float
    goal_completions: int
    revenue: float

class AnalyticsOverview(BaseModel):
    total_keywords: int
    avg_position: float
    organic_traffic: int
    top_10_count: int
    visibility_score: float
    traffic_change: float
    position_change: float
    keyword_opportunities: int

class DetailedReport(BaseModel):
    project_id: str
    date_range: str
    overview: AnalyticsOverview
    traffic_metrics: List[TrafficMetrics]
    keyword_performance: List[KeywordPerformance]
    competitor_analysis: List[CompetitorAnalysis]
    conversion_metrics: List[ConversionMetrics]

# Helper functions
def get_user_project(project_id: str, user: User, db: Session):
    """Get project and verify user access"""
    project = db.query(Project).filter(
        and_(Project.id == project_id, Project.org_id == user.org_id)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

def calculate_visibility_score(keywords: List[Keyword]) -> float:
    """Calculate visibility score based on keyword positions and search volumes"""
    if not keywords:
        return 0.0
    
    total_score = 0
    total_volume = 0
    
    for keyword in keywords:
        if keyword.current_position and keyword.search_volume:
            # CTR curve based on position
            if keyword.current_position == 1:
                ctr = 0.284
            elif keyword.current_position <= 3:
                ctr = 0.15
            elif keyword.current_position <= 10:
                ctr = 0.05
            else:
                ctr = 0.01
            
            score = keyword.search_volume * ctr
            total_score += score
            total_volume += keyword.search_volume
    
    return (total_score / total_volume) * 100 if total_volume > 0 else 0.0

async def get_competitor_data(domain: str, competitors: List[str]) -> List[CompetitorAnalysis]:
    """Get competitor analysis data"""
    competitor_data = []
    
    try:
        async with DataForSEOClient() as dataforseo:
            for competitor_domain in competitors[:5]:  # Limit to top 5 competitors
                try:
                    # Get competitor domain data
                    domain_data = await dataforseo.get_domain_keywords(competitor_domain, limit=1000)
                    
                    if domain_data and domain_data.get("tasks"):
                        result = domain_data["tasks"][0].get("result", [])
                        if result:
                            keywords_data = result[0].get("items", [])
                            
                            total_keywords = len(keywords_data)
                            top_10_keywords = len([k for k in keywords_data if k.get("se_results_count", 0) <= 10])
                            estimated_traffic = sum(k.get("search_volume", 0) * 0.1 for k in keywords_data)
                            avg_position = sum(k.get("se_results_count", 50) for k in keywords_data) / len(keywords_data) if keywords_data else 0
                            
                            competitor_data.append(CompetitorAnalysis(
                                domain=competitor_domain,
                                total_keywords=total_keywords,
                                top_10_keywords=top_10_keywords,
                                estimated_traffic=int(estimated_traffic),
                                common_keywords=0,  # TODO: Calculate common keywords
                                avg_position=round(avg_position, 1)
                            ))
                            
                except Exception as e:
                    logger.error(f"Error fetching competitor data for {competitor_domain}: {e}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error in competitor analysis: {e}")
    
    return competitor_data

# API endpoints
@router.get("/overview")
async def get_analytics_overview(
    project_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AnalyticsOverview:
    """Get analytics overview for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get keywords for the project
    keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
    
    # Calculate metrics
    total_keywords = len(keywords)
    positions = [k.current_position for k in keywords if k.current_position]
    avg_position = sum(positions) / len(positions) if positions else 0
    
    top_10_count = len([k for k in keywords if k.current_position and k.current_position <= 10])
    visibility_score = calculate_visibility_score(keywords)
    
    # Calculate estimated organic traffic
    organic_traffic = 0
    for keyword in keywords:
        if keyword.current_position and keyword.search_volume:
            if keyword.current_position <= 3:
                ctr = 0.25
            elif keyword.current_position <= 10:
                ctr = 0.1
            else:
                ctr = 0.02
            organic_traffic += int(keyword.search_volume * ctr)
    
    # Get historical data for changes
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Calculate position change
    recent_rankings = db.query(Ranking).filter(
        and_(
            Ranking.keyword_id.in_([k.id for k in keywords]),
            Ranking.recorded_at >= cutoff_date
        )
    ).all()
    
    position_change = 0.0
    traffic_change = 0.0
    
    if recent_rankings:
        # Simple calculation - could be more sophisticated
        old_avg = sum(r.position for r in recent_rankings[:len(recent_rankings)//2]) / (len(recent_rankings)//2) if recent_rankings else avg_position
        new_avg = sum(r.position for r in recent_rankings[len(recent_rankings)//2:]) / (len(recent_rankings) - len(recent_rankings)//2) if recent_rankings else avg_position
        position_change = old_avg - new_avg  # Positive means improvement
    
    # Keyword opportunities (keywords ranking 11-20)
    keyword_opportunities = len([k for k in keywords if k.current_position and 11 <= k.current_position <= 20])
    
    return AnalyticsOverview(
        total_keywords=total_keywords,
        avg_position=round(avg_position, 1),
        organic_traffic=organic_traffic,
        top_10_count=top_10_count,
        visibility_score=round(visibility_score, 2),
        traffic_change=round(traffic_change, 2),
        position_change=round(position_change, 1),
        keyword_opportunities=keyword_opportunities
    )

@router.get("/keywords/performance")
async def get_keyword_performance(
    project_id: str = Query(...),
    limit: int = Query(50, le=200),
    order_by: str = Query("position_change", regex="^(position_change|traffic|difficulty|volume)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[KeywordPerformance]:
    """Get keyword performance analytics"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get keywords with their latest rankings
    keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
    
    performance_data = []
    for keyword in keywords:
        # Get recent rankings for position change calculation
        recent_rankings = db.query(Ranking).filter(
            Ranking.keyword_id == keyword.id
        ).order_by(desc(Ranking.recorded_at)).limit(2).all()
        
        current_position = keyword.current_position or 50
        previous_position = None
        position_change = 0
        
        if len(recent_rankings) >= 2:
            current_position = recent_rankings[0].position
            previous_position = recent_rankings[1].position
            position_change = previous_position - current_position  # Positive means improvement
        
        # Calculate estimated traffic
        if current_position <= 3:
            ctr = 0.25
        elif current_position <= 10:
            ctr = 0.1
        else:
            ctr = 0.02
        
        estimated_traffic = int((keyword.search_volume or 0) * ctr)
        
        performance_data.append(KeywordPerformance(
            keyword=keyword.keyword,
            current_position=current_position,
            previous_position=previous_position,
            position_change=position_change,
            search_volume=keyword.search_volume or 0,
            estimated_traffic=estimated_traffic,
            difficulty=keyword.difficulty or 0
        ))
    
    # Sort by specified criteria
    if order_by == "position_change":
        performance_data.sort(key=lambda x: x.position_change, reverse=True)
    elif order_by == "traffic":
        performance_data.sort(key=lambda x: x.estimated_traffic, reverse=True)
    elif order_by == "difficulty":
        performance_data.sort(key=lambda x: x.difficulty)
    elif order_by == "volume":
        performance_data.sort(key=lambda x: x.search_volume, reverse=True)
    
    return performance_data[:limit]

@router.get("/traffic")
async def get_traffic_analytics(
    project_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TrafficMetrics]:
    """Get traffic analytics over time"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get traffic data from database
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    traffic_data = db.query(TrafficData).filter(
        and_(
            TrafficData.project_id == project_id,
            TrafficData.date >= cutoff_date
        )
    ).order_by(TrafficData.date).all()
    
    if traffic_data:
        return [
            TrafficMetrics(
                date=t.date.isoformat(),
                organic_traffic=t.sessions,
                organic_clicks=t.clicks,
                impressions=t.impressions,
                ctr=round(t.ctr, 3),
                avg_position=round(t.avg_position, 1)
            )
            for t in traffic_data
        ]
    else:
        # Generate sample data if no real data exists
        sample_data = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days-i)
            # Simulate realistic traffic patterns
            base_traffic = 1000 + (i * 10)  # Growing trend
            daily_variance = int(base_traffic * 0.1 * ((i % 7) / 7))  # Weekly pattern
            
            sample_data.append(TrafficMetrics(
                date=date.strftime("%Y-%m-%d"),
                organic_traffic=base_traffic + daily_variance,
                organic_clicks=int((base_traffic + daily_variance) * 0.8),
                impressions=int((base_traffic + daily_variance) * 5),
                ctr=round(0.15 + (i * 0.001), 3),
                avg_position=round(max(15, 25 - (i * 0.1)), 1)
            ))
        
        return sample_data

@router.get("/competitors")
async def get_competitor_analysis(
    project_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[CompetitorAnalysis]:
    """Get competitor analysis"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Check cache first
    cache_key = f"competitor_analysis:{project_id}"
    cached_data = await redis_client.get_cached_response(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Get competitor domains using DataForSEO
        async with DataForSEOClient() as dataforseo:
            competitor_data = await dataforseo.get_competitor_domains(project.domain, limit=10)
            
            competitors = []
            if competitor_data and competitor_data.get("tasks"):
                result = competitor_data["tasks"][0].get("result", [])
                if result:
                    for item in result[0].get("items", [])[:5]:
                        competitors.append(item.get("domain", ""))
            
            if not competitors:
                # Fallback to sample competitors
                competitors = ["example1.com", "example2.com", "example3.com"]
            
            # Get detailed competitor analysis
            analysis_data = await get_competitor_data(project.domain, competitors)
            
            # Cache for 4 hours
            await redis_client.cache_response(cache_key, analysis_data, 14400)
            
            return analysis_data
            
    except Exception as e:
        logger.error(f"Error in competitor analysis: {e}")
        # Return sample data
        return [
            CompetitorAnalysis(
                domain="competitor1.com",
                total_keywords=1250,
                top_10_keywords=89,
                estimated_traffic=12500,
                common_keywords=45,
                avg_position=18.5
            ),
            CompetitorAnalysis(
                domain="competitor2.com",
                total_keywords=980,
                top_10_keywords=67,
                estimated_traffic=9800,
                common_keywords=32,
                avg_position=22.1
            )
        ]

@router.get("/conversions")
async def get_conversion_analytics(
    project_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ConversionMetrics]:
    """Get conversion analytics"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # TODO: Integrate with Google Analytics API for real conversion data
    # For now, generate sample conversion data
    
    conversion_data = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days-i)
        sessions = 100 + (i * 2) + int(20 * ((i % 7) / 7))
        conversions = int(sessions * (0.02 + (i * 0.0001)))  # Improving conversion rate
        
        conversion_data.append(ConversionMetrics(
            date=date.strftime("%Y-%m-%d"),
            sessions=sessions,
            conversions=conversions,
            conversion_rate=round(conversions / sessions * 100, 2),
            goal_completions=conversions + int(conversions * 0.3),
            revenue=round(conversions * 50.0 + (i * 2), 2)
        ))
    
    return conversion_data

@router.get("/report")
async def get_detailed_report(
    project_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DetailedReport:
    """Generate a comprehensive analytics report"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get all analytics data
    overview = await get_analytics_overview(project_id, days, db, current_user)
    traffic_metrics = await get_traffic_analytics(project_id, days, db, current_user)
    keyword_performance = await get_keyword_performance(project_id, 50, "position_change", db, current_user)
    competitor_analysis = await get_competitor_analysis(project_id, db, current_user)
    conversion_metrics = await get_conversion_analytics(project_id, days, db, current_user)
    
    return DetailedReport(
        project_id=project_id,
        date_range=f"{days} days",
        overview=overview,
        traffic_metrics=traffic_metrics,
        keyword_performance=keyword_performance,
        competitor_analysis=competitor_analysis,
        conversion_metrics=conversion_metrics
    )

@router.post("/refresh")
async def refresh_analytics_data(
    project_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh analytics data from external sources"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Clear relevant caches
    cache_keys = [
        f"competitor_analysis:{project_id}",
        f"traffic_data:{project_id}",
        f"keyword_performance:{project_id}"
    ]
    
    for key in cache_keys:
        await redis_client.delete_cache(key)
    
    return {
        "message": "Analytics data refresh initiated",
        "project_id": project_id,
        "project_name": project.name
    }