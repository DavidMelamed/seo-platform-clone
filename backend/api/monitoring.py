"""
Real-time Monitoring API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import json
import asyncio

from core.database import get_db, Project, Keyword, Alert
from api.auth import get_current_user, User
from core.redis_client import redis_client

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.project_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if project_id not in self.project_connections:
            self.project_connections[project_id] = []
        self.project_connections[project_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        self.active_connections.remove(websocket)
        if project_id in self.project_connections:
            self.project_connections[project_id].remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def send_to_project(self, message: str, project_id: str):
        if project_id in self.project_connections:
            for connection in self.project_connections[project_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection is dead, remove it
                    self.project_connections[project_id].remove(connection)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection is dead, remove it
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Pydantic models
class MonitoringStatus(BaseModel):
    project_id: str
    status: str  # active, paused, stopped
    keywords_monitored: int
    last_check: datetime
    next_check: datetime

class AlertCreate(BaseModel):
    project_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    data: Dict[str, Any] = {}

class AlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

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
@router.get("/status/{project_id}", response_model=MonitoringStatus)
async def get_monitoring_status(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real-time monitoring status for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get monitoring data from Redis
    monitoring_key = f"monitoring:{project_id}"
    status_data = await redis_client.get_json(monitoring_key)
    
    if not status_data:
        # Initialize monitoring
        status_data = {
            "status": "stopped",
            "keywords_monitored": 0,
            "last_check": None,
            "next_check": None
        }
        await redis_client.set(monitoring_key, status_data, expire=3600)
    
    # Get keyword count
    keyword_count = db.query(Keyword).filter(
        and_(Keyword.project_id == project_id, Keyword.is_active == True)
    ).count()
    
    return MonitoringStatus(
        project_id=project_id,
        status=status_data.get("status", "stopped"),
        keywords_monitored=keyword_count,
        last_check=datetime.fromisoformat(status_data["last_check"]) if status_data.get("last_check") else datetime.utcnow(),
        next_check=datetime.fromisoformat(status_data["next_check"]) if status_data.get("next_check") else datetime.utcnow()
    )

@router.post("/start/{project_id}")
async def start_monitoring(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start real-time monitoring for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Update monitoring status
    monitoring_key = f"monitoring:{project_id}"
    status_data = {
        "status": "active",
        "last_check": datetime.utcnow().isoformat(),
        "next_check": (datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
    }
    await redis_client.set(monitoring_key, status_data, expire=3600)
    
    # Broadcast to connected clients
    await manager.send_to_project(
        json.dumps({
            "type": "monitoring_started",
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat()
        }),
        project_id
    )
    
    return {"message": "Monitoring started", "project_id": project_id}

@router.post("/stop/{project_id}")
async def stop_monitoring(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop real-time monitoring for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Update monitoring status
    monitoring_key = f"monitoring:{project_id}"
    status_data = {
        "status": "stopped",
        "last_check": datetime.utcnow().isoformat(),
        "next_check": None
    }
    await redis_client.set(monitoring_key, status_data, expire=3600)
    
    # Broadcast to connected clients
    await manager.send_to_project(
        json.dumps({
            "type": "monitoring_stopped",
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat()
        }),
        project_id
    )
    
    return {"message": "Monitoring stopped", "project_id": project_id}

@router.get("/alerts/{project_id}", response_model=List[AlertResponse])
async def get_alerts(
    project_id: str,
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alerts for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Build query
    query = db.query(Alert).filter(Alert.project_id == project_id)
    
    if unread_only:
        query = query.filter(Alert.is_read == False)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    return [
        AlertResponse(
            id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            is_read=alert.is_read,
            created_at=alert.created_at
        )
        for alert in alerts
    ]

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert"""
    
    # Verify project access
    project = get_user_project(alert_data.project_id, current_user, db)
    
    # Create alert
    alert = Alert(
        project_id=alert_data.project_id,
        alert_type=alert_data.alert_type,
        severity=alert_data.severity,
        title=alert_data.title,
        message=alert_data.message,
        data=alert_data.data
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Broadcast to connected clients
    alert_message = {
        "type": "new_alert",
        "alert": {
            "id": str(alert.id),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "created_at": alert.created_at.isoformat()
        }
    }
    
    await manager.send_to_project(json.dumps(alert_message), alert_data.project_id)
    
    return AlertResponse(
        id=str(alert.id),
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        is_read=alert.is_read,
        created_at=alert.created_at
    )

@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an alert as read"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Verify access through project
    get_user_project(str(alert.project_id), current_user, db)
    
    alert.is_read = True
    db.commit()
    
    return {"message": "Alert marked as read"}

@router.get("/live-data/{project_id}")
async def get_live_data(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get live monitoring data"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get real-time data from Redis
    live_data_key = f"live_data:{project_id}"
    live_data = await redis_client.get_json(live_data_key)
    
    if not live_data:
        # Generate sample data
        live_data = {
            "rankings_checked": 0,
            "position_changes": 0,
            "volatility_score": 0.0,
            "last_update": datetime.utcnow().isoformat(),
            "active_monitors": 0
        }
    
    return live_data

# WebSocket endpoint
@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time updates"""
    
    await manager.connect(websocket, project_id)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connected",
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                    websocket
                )
            elif message.get("type") == "start_monitoring":
                # Start monitoring for this project
                # This would integrate with the real-time monitoring service
                await manager.send_personal_message(
                    json.dumps({
                        "type": "monitoring_started",
                        "project_id": project_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)

# Background task to simulate real-time updates
async def simulate_real_time_updates():
    """Simulate real-time ranking updates (for demo purposes)"""
    
    while True:
        try:
            # Get all active monitoring projects
            # For demo, we'll just broadcast to all projects
            
            import random
            
            # Simulate a ranking change
            fake_update = {
                "type": "ranking_update",
                "keyword": "seo tools",
                "old_position": 15,
                "new_position": 12,
                "change": -3,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast(json.dumps(fake_update))
            
            # Wait 30 seconds before next update
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Error in real-time updates: {e}")
            await asyncio.sleep(5)

# Start the background task (in production, this would be a separate service)
# asyncio.create_task(simulate_real_time_updates())