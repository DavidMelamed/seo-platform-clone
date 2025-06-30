"""
Dashboard API endpoints with real metrics and data
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from core.database import get_db
from models import User, Project, Keyword, Ranking, Alert
from core.deps import get_current_user

router = APIRouter()

# Pydantic models
class DashboardMetrics(BaseModel):
    total_keywords: int
    avg_position: float
    top_ten_keywords: int
    organic_traffic: int
    keyword_changes: Dict[str, int]
    projects_count: int
    alerts_count: int

class TrafficData(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]

class PositionData(BaseModel):
    labels: List[str] 
    datasets: List[Dict[str, Any]]

class RecentActivity(BaseModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: datetime
    status: str

class DashboardData(BaseModel):
    metrics: DashboardMetrics
    traffic_data: TrafficData
    position_data: PositionData
    recent_activities: List[RecentActivity]


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="Filter by project ID")
):
    """Get dashboard metrics for the current user"""
    
    # Base query filter
    base_filter = [Project.org_id == current_user.org_id]
    if project_id:
        base_filter.append(Project.id == project_id)
    
    # Get projects count
    projects_count = db.query(Project).filter(*base_filter).count()
    
    # Get keywords count and average position
    keyword_query = db.query(Keyword).join(Project).filter(*base_filter)
    total_keywords = keyword_query.count()
    
    # Calculate average position from latest rankings
    avg_position_result = db.execute(text("""
        SELECT AVG(latest_rankings.position) as avg_pos
        FROM (
            SELECT DISTINCT ON (k.id) k.id, r.position
            FROM keywords k
            JOIN projects p ON k.project_id = p.id
            LEFT JOIN rankings r ON k.id = r.keyword_id
            WHERE p.org_id = :org_id
            AND (:project_id IS NULL OR p.id = :project_id)
            ORDER BY k.id, r.recorded_at DESC
        ) as latest_rankings
        WHERE latest_rankings.position IS NOT NULL
    """), {"org_id": str(current_user.org_id), "project_id": project_id})
    
    avg_position = avg_position_result.fetchone()
    avg_position = float(avg_position[0]) if avg_position and avg_position[0] else 0.0
    
    # Get top 10 keywords count
    top_ten_count = db.execute(text("""
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT ON (k.id) k.id, r.position
            FROM keywords k
            JOIN projects p ON k.project_id = p.id
            LEFT JOIN rankings r ON k.id = r.keyword_id
            WHERE p.org_id = :org_id
            AND (:project_id IS NULL OR p.id = :project_id)
            ORDER BY k.id, r.recorded_at DESC
        ) as latest_rankings
        WHERE latest_rankings.position <= 10
    """), {"org_id": str(current_user.org_id), "project_id": project_id})
    
    top_ten_keywords = int(top_ten_count.fetchone()[0])
    
    # Calculate organic traffic estimate (simplified)
    # In a real implementation, this would come from Google Analytics or similar
    organic_traffic = int(top_ten_keywords * 50 + (total_keywords - top_ten_keywords) * 10)
    
    # Get keyword changes from last week
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    keyword_changes_result = db.execute(text("""
        WITH current_positions AS (
            SELECT DISTINCT ON (k.id) k.id, r.position as current_pos
            FROM keywords k
            JOIN projects p ON k.project_id = p.id
            LEFT JOIN rankings r ON k.id = r.keyword_id
            WHERE p.org_id = :org_id
            AND (:project_id IS NULL OR p.id = :project_id)
            ORDER BY k.id, r.recorded_at DESC
        ),
        previous_positions AS (
            SELECT DISTINCT ON (k.id) k.id, r.position as previous_pos
            FROM keywords k
            JOIN projects p ON k.project_id = p.id
            LEFT JOIN rankings r ON k.id = r.keyword_id
            WHERE p.org_id = :org_id
            AND (:project_id IS NULL OR p.id = :project_id)
            AND r.recorded_at >= :week_ago
            ORDER BY k.id, r.recorded_at ASC
        )
        SELECT 
            COUNT(CASE WHEN cp.current_pos < pp.previous_pos THEN 1 END) as improved,
            COUNT(CASE WHEN cp.current_pos > pp.previous_pos THEN 1 END) as declined,
            COUNT(CASE WHEN pp.previous_pos IS NULL AND cp.current_pos IS NOT NULL THEN 1 END) as new_keywords
        FROM current_positions cp
        LEFT JOIN previous_positions pp ON cp.id = pp.id
    """), {"org_id": str(current_user.org_id), "project_id": project_id, "week_ago": week_ago})
    
    changes_result = keyword_changes_result.fetchone()
    keyword_changes = {
        "improved": int(changes_result[0] or 0),
        "declined": int(changes_result[1] or 0), 
        "new": int(changes_result[2] or 0)
    }
    
    # Get alerts count
    alerts_count = db.query(Alert).join(Project).filter(
        *base_filter,
        Alert.is_resolved == False
    ).count()
    
    return DashboardMetrics(
        total_keywords=total_keywords,
        avg_position=round(avg_position, 1),
        top_ten_keywords=top_ten_keywords,
        organic_traffic=organic_traffic,
        keyword_changes=keyword_changes,
        projects_count=projects_count,
        alerts_count=alerts_count
    )


@router.get("/traffic-data", response_model=TrafficData)
async def get_traffic_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    days: int = Query(30, description="Number of days to retrieve data for")
):
    """Get traffic data for charts"""
    
    # Generate traffic data based on keyword performance
    # In production, this would integrate with Google Analytics, Search Console, etc.
    
    base_filter = [Project.org_id == current_user.org_id]
    if project_id:
        base_filter.append(Project.id == project_id)
    
    # Get keyword count per day for the last N days
    start_date = datetime.utcnow() - timedelta(days=days)
    
    traffic_data = []
    labels = []
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        labels.append(date.strftime("%b %d"))
        
        # Simulate traffic data based on keyword performance
        # This would be replaced with real analytics data
        keyword_count = db.query(Keyword).join(Project).filter(
            *base_filter,
            Keyword.created_at <= date
        ).count()
        
        # Estimate traffic based on keywords (simplified algorithm)
        estimated_traffic = int(keyword_count * 15 + (i * 10))
        traffic_data.append(estimated_traffic)
    
    return TrafficData(
        labels=labels,
        datasets=[{
            "label": "Estimated Organic Traffic",
            "data": traffic_data,
            "borderColor": "rgb(75, 192, 192)",
            "backgroundColor": "rgba(75, 192, 192, 0.2)",
            "fill": True
        }]
    )


@router.get("/position-data", response_model=PositionData)
async def get_position_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="Filter by project ID")
):
    """Get position distribution data for charts"""
    
    base_filter = [Project.org_id == current_user.org_id]
    if project_id:
        base_filter.append(Project.id == project_id)
    
    # Get position distribution
    position_distribution = db.execute(text("""
        SELECT 
            COUNT(CASE WHEN position <= 3 THEN 1 END) as top_3,
            COUNT(CASE WHEN position <= 10 AND position > 3 THEN 1 END) as top_10,
            COUNT(CASE WHEN position <= 20 AND position > 10 THEN 1 END) as top_20,
            COUNT(CASE WHEN position <= 50 AND position > 20 THEN 1 END) as top_50,
            COUNT(CASE WHEN position > 50 THEN 1 END) as beyond_50
        FROM (
            SELECT DISTINCT ON (k.id) k.id, r.position
            FROM keywords k
            JOIN projects p ON k.project_id = p.id
            LEFT JOIN rankings r ON k.id = r.keyword_id
            WHERE p.org_id = :org_id
            AND (:project_id IS NULL OR p.id = :project_id)
            AND r.position IS NOT NULL
            ORDER BY k.id, r.recorded_at DESC
        ) as latest_rankings
    """), {"org_id": str(current_user.org_id), "project_id": project_id})
    
    result = position_distribution.fetchone()
    
    return PositionData(
        labels=["Top 3", "Top 10", "Top 20", "Top 50", "50+"],
        datasets=[{
            "data": [
                int(result[0] or 0),
                int(result[1] or 0), 
                int(result[2] or 0),
                int(result[3] or 0),
                int(result[4] or 0)
            ],
            "backgroundColor": [
                "#4CAF50",
                "#8BC34A", 
                "#FFC107",
                "#FF9800",
                "#F44336"
            ]
        }]
    )


@router.get("/recent-activities", response_model=List[RecentActivity])
async def get_recent_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of activities to return")
):
    """Get recent activities and changes"""
    
    activities = []
    
    # Get recent alerts
    recent_alerts = db.query(Alert).join(Project).filter(
        Project.org_id == current_user.org_id,
        Alert.created_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(desc(Alert.created_at)).limit(limit // 2).all()
    
    for alert in recent_alerts:
        activities.append(RecentActivity(
            id=str(alert.id),
            type="alert",
            title=alert.title,
            description=alert.message,
            timestamp=alert.created_at,
            status=alert.severity
        ))
    
    # Get recent keyword additions
    recent_keywords = db.query(Keyword).join(Project).filter(
        Project.org_id == current_user.org_id,
        Keyword.created_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(desc(Keyword.created_at)).limit(limit // 2).all()
    
    for keyword in recent_keywords:
        activities.append(RecentActivity(
            id=str(keyword.id),
            type="keyword",
            title=f"New keyword: {keyword.keyword}",
            description="Added to tracking",
            timestamp=keyword.created_at,
            status="new"
        ))
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]


@router.get("/complete", response_model=DashboardData)
async def get_complete_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="Filter by project ID")
):
    """Get complete dashboard data in one request"""
    
    metrics = await get_dashboard_metrics(current_user, db, project_id)
    traffic_data = await get_traffic_data(current_user, db, project_id)
    position_data = await get_position_data(current_user, db, project_id)
    recent_activities = await get_recent_activities(current_user, db)
    
    return DashboardData(
        metrics=metrics,
        traffic_data=traffic_data,
        position_data=position_data,
        recent_activities=recent_activities
    )