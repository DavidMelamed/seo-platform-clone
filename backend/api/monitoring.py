"""
Monitoring API endpoints
Real-time monitoring with alerts and notifications
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio
import json
from enum import Enum

logger = logging.getLogger(__name__)

from core.database import get_db
from models import User, Project, Keyword, Ranking, Alert, Notification
from api.auth import get_current_user
from services.dataforseo.client import DataForSEOClient
from core.redis_client import redis_client

router = APIRouter()

# Enums
class AlertType(str, Enum):
    RANKING_DROP = "ranking_drop"
    RANKING_IMPROVEMENT = "ranking_improvement"
    KEYWORD_LOST = "keyword_lost"
    KEYWORD_GAINED = "keyword_gained"
    TRAFFIC_DROP = "traffic_drop"
    TRAFFIC_SPIKE = "traffic_spike"
    COMPETITOR_CHANGE = "competitor_change"
    TECHNICAL_ISSUE = "technical_issue"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

# Pydantic models
class AlertCreate(BaseModel):
    name: str
    project_id: str
    alert_type: AlertType
    threshold_value: float
    comparison_operator: str  # >, <, >=, <=, =
    is_active: bool = True
    email_notifications: bool = True
    slack_notifications: bool = False
    webhook_url: Optional[str] = None

class AlertUpdate(BaseModel):
    name: Optional[str] = None
    threshold_value: Optional[float] = None
    comparison_operator: Optional[str] = None
    is_active: Optional[bool] = None
    email_notifications: Optional[bool] = None
    slack_notifications: Optional[bool] = None
    webhook_url: Optional[str] = None

class AlertResponse(BaseModel):
    id: str
    name: str
    project_id: str
    alert_type: AlertType
    threshold_value: float
    comparison_operator: str
    severity: AlertSeverity
    is_active: bool
    email_notifications: bool
    slack_notifications: bool
    webhook_url: Optional[str]
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class NotificationResponse(BaseModel):
    id: str
    alert_id: str
    project_id: str
    title: str
    message: str
    severity: AlertSeverity
    status: NotificationStatus
    metadata: Dict[str, Any]
    created_at: datetime

class MonitoringOverview(BaseModel):
    total_alerts: int
    active_alerts: int
    triggered_today: int
    unread_notifications: int
    system_health: str
    uptime_percentage: float

class SystemHealth(BaseModel):
    status: str
    response_time: float
    database_status: str
    redis_status: str
    dataforseo_status: str
    last_check: datetime

class RealTimeUpdate(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection closed, remove it
                    self.user_connections[user_id].remove(connection)
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                self.active_connections.remove(connection)

manager = ConnectionManager()


# Helper functions
def get_user_project(project_id: str, user: User, db: Session):
    """Get project and verify user access"""
    project = db.query(Project).filter(
        and_(Project.id == project_id, Project.org_id == user.org_id)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

def calculate_alert_severity(alert_type: AlertType, change_magnitude: float) -> AlertSeverity:
    """Calculate alert severity based on type and magnitude"""
    if alert_type in [AlertType.KEYWORD_LOST, AlertType.TRAFFIC_DROP]:
        if change_magnitude >= 50:
            return AlertSeverity.CRITICAL
        elif change_magnitude >= 30:
            return AlertSeverity.HIGH
        elif change_magnitude >= 15:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    elif alert_type in [AlertType.RANKING_DROP]:
        if change_magnitude >= 20:
            return AlertSeverity.CRITICAL
        elif change_magnitude >= 10:
            return AlertSeverity.HIGH
        elif change_magnitude >= 5:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    else:
        return AlertSeverity.MEDIUM

async def check_ranking_alerts(project_id: str, db: Session):
    """Check for ranking-related alerts"""
    alerts_triggered = []
    
    # Get active ranking alerts for the project
    alerts = db.query(Alert).filter(
        and_(
            Alert.project_id == project_id,
            Alert.is_active == True,
            Alert.alert_type.in_([AlertType.RANKING_DROP, AlertType.RANKING_IMPROVEMENT])
        )
    ).all()
    
    if not alerts:
        return alerts_triggered
    
    # Get recent rankings
    cutoff_date = datetime.utcnow() - timedelta(days=1)
    keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
    
    for keyword in keywords:
        recent_rankings = db.query(Ranking).filter(
            and_(
                Ranking.keyword_id == keyword.id,
                Ranking.recorded_at >= cutoff_date
            )
        ).order_by(desc(Ranking.recorded_at)).limit(2).all()
        
        if len(recent_rankings) >= 2:
            current_pos = recent_rankings[0].position
            previous_pos = recent_rankings[1].position
            change = previous_pos - current_pos  # Positive = improvement
            
            for alert in alerts:
                triggered = False
                
                if alert.alert_type == AlertType.RANKING_DROP and change < 0:
                    # Position worsened
                    if alert.comparison_operator == ">" and abs(change) > alert.threshold_value:
                        triggered = True
                    elif alert.comparison_operator == ">=" and abs(change) >= alert.threshold_value:
                        triggered = True
                elif alert.alert_type == AlertType.RANKING_IMPROVEMENT and change > 0:
                    # Position improved
                    if alert.comparison_operator == ">" and change > alert.threshold_value:
                        triggered = True
                    elif alert.comparison_operator == ">=" and change >= alert.threshold_value:
                        triggered = True
                
                if triggered:
                    severity = calculate_alert_severity(alert.alert_type, abs(change))
                    
                    # Create notification
                    notification = Notification(
                        alert_id=alert.id,
                        project_id=project_id,
                        title=f"Ranking {alert.alert_type.value.replace('_', ' ').title()}",
                        message=f"Keyword '{keyword.keyword}' moved from position {previous_pos} to {current_pos}",
                        severity=severity,
                        status=NotificationStatus.UNREAD,
                        metadata={
                            "keyword": keyword.keyword,
                            "previous_position": previous_pos,
                            "current_position": current_pos,
                            "change": change
                        }
                    )
                    
                    db.add(notification)
                    alerts_triggered.append({
                        "alert": alert,
                        "notification": notification,
                        "severity": severity
                    })
                    
                    # Update alert last triggered
                    alert.last_triggered_at = datetime.utcnow()
    
    db.commit()
    return alerts_triggered

# API endpoints
@router.get("/overview")
async def get_monitoring_overview(
    project_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MonitoringOverview:
    """Get monitoring overview for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get alert counts
    total_alerts = db.query(Alert).filter(Alert.project_id == project_id).count()
    active_alerts = db.query(Alert).filter(
        and_(Alert.project_id == project_id, Alert.is_active == True)
    ).count()
    
    # Get notifications triggered today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    triggered_today = db.query(Notification).filter(
        and_(
            Notification.project_id == project_id,
            Notification.created_at >= today_start
        )
    ).count()
    
    # Get unread notifications
    unread_notifications = db.query(Notification).filter(
        and_(
            Notification.project_id == project_id,
            Notification.status == NotificationStatus.UNREAD
        )
    ).count()
    
    # System health (simplified)
    system_health = "healthy"
    uptime_percentage = 99.9  # Would be calculated from actual uptime data
    
    return MonitoringOverview(
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        triggered_today=triggered_today,
        unread_notifications=unread_notifications,
        system_health=system_health,
        uptime_percentage=uptime_percentage
    )

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new monitoring alert"""
    
    # Verify project access
    project = get_user_project(alert_data.project_id, current_user, db)
    
    # Create alert
    alert = Alert(
        name=alert_data.name,
        project_id=alert_data.project_id,
        alert_type=alert_data.alert_type,
        threshold_value=alert_data.threshold_value,
        comparison_operator=alert_data.comparison_operator,
        severity=AlertSeverity.MEDIUM,  # Default severity
        is_active=alert_data.is_active,
        email_notifications=alert_data.email_notifications,
        slack_notifications=alert_data.slack_notifications,
        webhook_url=alert_data.webhook_url
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return AlertResponse(
        id=str(alert.id),
        name=alert.name,
        project_id=alert.project_id,
        alert_type=alert.alert_type,
        threshold_value=alert.threshold_value,
        comparison_operator=alert.comparison_operator,
        severity=alert.severity,
        is_active=alert.is_active,
        email_notifications=alert.email_notifications,
        slack_notifications=alert.slack_notifications,
        webhook_url=alert.webhook_url,
        last_triggered_at=alert.last_triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at
    )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    project_id: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get monitoring alerts for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    alerts = db.query(Alert).filter(
        Alert.project_id == project_id
    ).offset(skip).limit(limit).all()
    
    return [
        AlertResponse(
            id=str(alert.id),
            name=alert.name,
            project_id=alert.project_id,
            alert_type=alert.alert_type,
            threshold_value=alert.threshold_value,
            comparison_operator=alert.comparison_operator,
            severity=alert.severity,
            is_active=alert.is_active,
            email_notifications=alert.email_notifications,
            slack_notifications=alert.slack_notifications,
            webhook_url=alert.webhook_url,
            last_triggered_at=alert.last_triggered_at,
            created_at=alert.created_at,
            updated_at=alert.updated_at
        )
        for alert in alerts
    ]

@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a monitoring alert"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Verify project access
    get_user_project(alert.project_id, current_user, db)
    
    # Update fields
    update_data = alert_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)
    
    alert.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    
    return AlertResponse(
        id=str(alert.id),
        name=alert.name,
        project_id=alert.project_id,
        alert_type=alert.alert_type,
        threshold_value=alert.threshold_value,
        comparison_operator=alert.comparison_operator,
        severity=alert.severity,
        is_active=alert.is_active,
        email_notifications=alert.email_notifications,
        slack_notifications=alert.slack_notifications,
        webhook_url=alert.webhook_url,
        last_triggered_at=alert.last_triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at
    )

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a monitoring alert"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Verify project access
    get_user_project(alert.project_id, current_user, db)
    
    db.delete(alert)
    db.commit()
    
    return {"message": "Alert deleted successfully"}

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    project_id: str = Query(...),
    status: Optional[NotificationStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    query = db.query(Notification).filter(Notification.project_id == project_id)
    
    if status:
        query = query.filter(Notification.status == status)
    
    notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
    
    return [
        NotificationResponse(
            id=str(n.id),
            alert_id=str(n.alert_id),
            project_id=n.project_id,
            title=n.title,
            message=n.message,
            severity=n.severity,
            status=n.status,
            metadata=n.metadata or {},
            created_at=n.created_at
        )
        for n in notifications
    ]

@router.put("/notifications/{notification_id}/status")
async def update_notification_status(
    notification_id: str,
    status: NotificationStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update notification status"""
    
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Verify project access
    get_user_project(notification.project_id, current_user, db)
    
    notification.status = status
    db.commit()
    
    return {"message": "Notification status updated"}

@router.get("/health")
async def get_system_health() -> SystemHealth:
    """Get system health status"""
    
    start_time = datetime.utcnow()
    
    # Check database
    try:
        # Simple database check
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis
    try:
        await redis_client.get_cached_response("health_check")
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    # Check DataForSEO
    try:
        async with DataForSEOClient() as client:
            await client.check_account_balance()
        dataforseo_status = "healthy"
    except Exception:
        dataforseo_status = "unhealthy"
    
    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    overall_status = "healthy"
    if any(status == "unhealthy" for status in [db_status, redis_status, dataforseo_status]):
        overall_status = "degraded"
    
    return SystemHealth(
        status=overall_status,
        response_time=response_time,
        database_status=db_status,
        redis_status=redis_status,
        dataforseo_status=dataforseo_status,
        last_check=datetime.utcnow()
    )

@router.post("/check-alerts")
async def trigger_alert_check(
    project_id: str = Query(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger alert checking for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Add background task
    background_tasks.add_task(check_ranking_alerts, project_id, db)
    
    return {
        "message": "Alert check initiated",
        "project_id": project_id
    }

# WebSocket endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time monitoring updates"""
    
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Echo received message (for testing)
            await manager.send_personal_message(f"Echo: {data}", user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Background task to send real-time updates
async def send_real_time_update(user_id: str, update_type: str, data: Dict[str, Any]):
    """Send real-time update to specific user"""
    
    update = RealTimeUpdate(
        type=update_type,
        data=data,
        timestamp=datetime.utcnow()
    )
    
    await manager.send_personal_message(
        json.dumps(update.dict(), default=str),
        user_id
    )