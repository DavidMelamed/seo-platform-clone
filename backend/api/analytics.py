"""
Analytics API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from core.database import get_db, Keyword, Project, Ranking
from api.auth import get_current_user, User

router = APIRouter()

# Pydantic models
class ProjectStats(BaseModel):
    total_keywords: int
    avg_position: float
    top_10_keywords: int
    top_3_keywords: int
    improved_keywords: int
    declined_keywords: int

class KeywordPerformance(BaseModel):
    keyword: str
    current_position: int
    previous_position: int
    change: int
    search_volume: int

class AnalyticsDashboard(BaseModel):
    project_stats: ProjectStats
    top_performers: List[KeywordPerformance]
    recent_changes: List[KeywordPerformance]
    position_distribution: Dict[str, int]

# Helper functions
def get_user_project(project_id: str, user: User, db: Session):
    """Get project and verify user access"""
    project = db.query(Project).filter(
        and_(Project.id == project_id, Project.org_id == user.org_id)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

# API endpoints
@router.get("/dashboard/{project_id}", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    project_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics dashboard for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get project keywords
    keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
    
    if not keywords:
        return AnalyticsDashboard(
            project_stats=ProjectStats(
                total_keywords=0,
                avg_position=0,
                top_10_keywords=0,
                top_3_keywords=0,
                improved_keywords=0,
                declined_keywords=0
            ),
            top_performers=[],
            recent_changes=[],
            position_distribution={}
        )
    
    # Calculate project stats
    total_keywords = len(keywords)
    positions = [k.current_position for k in keywords if k.current_position]
    avg_position = sum(positions) / len(positions) if positions else 0
    top_10_keywords = len([p for p in positions if p <= 10])
    top_3_keywords = len([p for p in positions if p <= 3])
    
    # For demo purposes, generate some mock improvement/decline data
    improved_keywords = int(total_keywords * 0.3)
    declined_keywords = int(total_keywords * 0.2)
    
    project_stats = ProjectStats(
        total_keywords=total_keywords,
        avg_position=round(avg_position, 1),
        top_10_keywords=top_10_keywords,
        top_3_keywords=top_3_keywords,
        improved_keywords=improved_keywords,
        declined_keywords=declined_keywords
    )
    
    # Get top performers (mock data for now)
    top_performers = []
    for keyword in keywords[:5]:
        if keyword.current_position:
            top_performers.append(KeywordPerformance(
                keyword=keyword.keyword,
                current_position=keyword.current_position,
                previous_position=keyword.current_position + 2,  # Mock improvement
                change=-2,
                search_volume=keyword.search_volume or 1000
            ))
    
    # Recent changes (mock data)
    recent_changes = []
    for keyword in keywords[5:10]:
        if keyword.current_position:
            recent_changes.append(KeywordPerformance(
                keyword=keyword.keyword,
                current_position=keyword.current_position,
                previous_position=keyword.current_position - 1,  # Mock decline
                change=1,
                search_volume=keyword.search_volume or 800
            ))
    
    # Position distribution
    position_distribution = {
        "1-3": len([p for p in positions if 1 <= p <= 3]),
        "4-10": len([p for p in positions if 4 <= p <= 10]),
        "11-20": len([p for p in positions if 11 <= p <= 20]),
        "21-50": len([p for p in positions if 21 <= p <= 50]),
        "51-100": len([p for p in positions if 51 <= p <= 100]),
        "100+": len([p for p in positions if p > 100])
    }
    
    return AnalyticsDashboard(
        project_stats=project_stats,
        top_performers=top_performers,
        recent_changes=recent_changes,
        position_distribution=position_distribution
    )

@router.get("/keywords/{project_id}/performance")
async def get_keyword_performance(
    project_id: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, le=1000),
    sort_by: str = Query("improvement", regex="^(improvement|decline|position|volume)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get keyword performance analysis"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get keywords with current positions
    keywords = db.query(Keyword).filter(
        and_(
            Keyword.project_id == project_id,
            Keyword.current_position.isnot(None)
        )
    ).limit(limit).all()
    
    performance_data = []
    for keyword in keywords:
        # Mock previous position for demo
        previous_pos = (keyword.current_position or 50) + 3
        
        performance_data.append({
            "keyword": keyword.keyword,
            "current_position": keyword.current_position,
            "previous_position": previous_pos,
            "change": previous_pos - (keyword.current_position or 50),
            "search_volume": keyword.search_volume or 1000,
            "difficulty": keyword.difficulty or 50,
            "cpc": keyword.cpc or 2.5
        })
    
    # Sort data
    if sort_by == "improvement":
        performance_data.sort(key=lambda x: x["change"], reverse=True)
    elif sort_by == "decline":
        performance_data.sort(key=lambda x: x["change"])
    elif sort_by == "position":
        performance_data.sort(key=lambda x: x["current_position"])
    elif sort_by == "volume":
        performance_data.sort(key=lambda x: x["search_volume"], reverse=True)
    
    return {
        "data": performance_data,
        "total": len(performance_data),
        "summary": {
            "avg_change": sum(d["change"] for d in performance_data) / len(performance_data) if performance_data else 0,
            "improved_count": len([d for d in performance_data if d["change"] > 0]),
            "declined_count": len([d for d in performance_data if d["change"] < 0]),
            "unchanged_count": len([d for d in performance_data if d["change"] == 0])
        }
    }

@router.get("/trends/{project_id}")
async def get_ranking_trends(
    project_id: str,
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ranking trends over time"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Generate mock trend data
    from datetime import datetime, timedelta
    import random
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Generate daily data points
    trends = []
    current_date = start_date
    base_avg_position = 45.0
    
    while current_date <= end_date:
        # Add some randomness to simulate real data
        daily_change = random.uniform(-2, 1.5)
        base_avg_position = max(1, min(100, base_avg_position + daily_change))
        
        trends.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "avg_position": round(base_avg_position, 1),
            "top_10_count": random.randint(15, 25),
            "top_3_count": random.randint(3, 8),
            "visibility_score": round(random.uniform(0.3, 0.8), 2)
        })
        
        current_date += timedelta(days=1)
    
    return {
        "trends": trends,
        "period": f"{days} days",
        "summary": {
            "avg_position_change": round(trends[-1]["avg_position"] - trends[0]["avg_position"], 1),
            "best_position": min(t["avg_position"] for t in trends),
            "worst_position": max(t["avg_position"] for t in trends),
            "volatility": round(
                sum(abs(trends[i]["avg_position"] - trends[i-1]["avg_position"]) 
                    for i in range(1, len(trends))) / (len(trends) - 1), 2
            ) if len(trends) > 1 else 0
        }
    }

@router.get("/competitors/{project_id}")
async def get_competitor_analysis(
    project_id: str,
    keyword_limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get competitor analysis"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Mock competitor data
    competitors = [
        {
            "domain": "competitor1.com",
            "common_keywords": 45,
            "avg_position": 8.2,
            "traffic_share": 0.35,
            "strength_score": 85
        },
        {
            "domain": "competitor2.com", 
            "common_keywords": 38,
            "avg_position": 12.1,
            "traffic_share": 0.28,
            "strength_score": 72
        },
        {
            "domain": "competitor3.com",
            "common_keywords": 32,
            "avg_position": 15.4,
            "traffic_share": 0.22,
            "strength_score": 68
        }
    ]
    
    return {
        "competitors": competitors,
        "your_domain": project.domain or "your-site.com",
        "market_share": {
            "your_share": 0.15,
            "total_tracked": 0.85,
            "opportunity": 0.15
        },
        "keyword_gaps": [
            {"keyword": "seo tools", "competitor_position": 3, "your_position": None},
            {"keyword": "keyword research", "competitor_position": 5, "your_position": 15},
            {"keyword": "backlink analysis", "competitor_position": 2, "your_position": None}
        ]
    }

@router.get("/reports/{project_id}/export")
async def export_analytics_report(
    project_id: str,
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export analytics report"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # For now, return JSON data
    # In production, you'd generate actual files
    
    dashboard_data = await get_analytics_dashboard(project_id, days, db, current_user)
    
    if format == "json":
        return {
            "format": "json",
            "data": dashboard_data,
            "generated_at": datetime.utcnow().isoformat(),
            "project": project.name,
            "period": f"{days} days"
        }
    elif format == "csv":
        return {
            "message": "CSV export would be generated here",
            "download_url": f"/downloads/analytics_{project_id}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    else:  # pdf
        return {
            "message": "PDF report would be generated here",
            "download_url": f"/downloads/analytics_{project_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        }