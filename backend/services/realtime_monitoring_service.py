"""
Real-time SERP Monitoring Service
Provides minute-by-minute rank tracking and instant alerts
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import aioredis
from fastapi import WebSocket
import httpx
from collections import defaultdict
import numpy as np

class AlertType(Enum):
    """Types of SEO alerts"""
    RANK_DROP = "rank_drop"
    RANK_GAIN = "rank_gain"
    SERP_VOLATILITY = "serp_volatility"
    NEW_COMPETITOR = "new_competitor"
    LOST_SNIPPET = "lost_snippet"
    GAINED_SNIPPET = "gained_snippet"
    ALGORITHM_UPDATE = "algorithm_update"
    TECHNICAL_ISSUE = "technical_issue"
    BACKLINK_CHANGE = "backlink_change"

@dataclass
class RankingSnapshot:
    """Point-in-time ranking data"""
    keyword: str
    position: int
    url: str
    timestamp: datetime
    serp_features: List[str]
    competitors: List[Dict]

@dataclass
class Alert:
    """SEO alert structure"""
    type: AlertType
    severity: str  # critical, warning, info
    keyword: str
    message: str
    data: Dict
    timestamp: datetime

class RealtimeMonitoringService:
    def __init__(self, redis_url: str, dataforseo_client):
        self.redis_url = redis_url
        self.dataforseo = dataforseo_client
        self.redis = None
        self.websocket_connections: Set[WebSocket] = set()
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.alert_thresholds = {
            "rank_drop": 3,  # positions
            "volatility_threshold": 0.3,  # 30% change
            "check_interval": 60  # seconds
        }
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.create_redis_pool(self.redis_url)
        
    async def start_monitoring(self, project_id: str, keywords: List[str]):
        """Start real-time monitoring for keywords"""
        monitoring_key = f"monitoring:{project_id}"
        
        # Store keywords to monitor
        await self.redis.sadd(monitoring_key, *keywords)
        
        # Start monitoring task
        if project_id not in self.monitoring_tasks:
            task = asyncio.create_task(self._monitor_keywords(project_id))
            self.monitoring_tasks[project_id] = task
            
    async def stop_monitoring(self, project_id: str):
        """Stop monitoring for a project"""
        if project_id in self.monitoring_tasks:
            self.monitoring_tasks[project_id].cancel()
            del self.monitoring_tasks[project_id]
            
    async def _monitor_keywords(self, project_id: str):
        """Main monitoring loop"""
        monitoring_key = f"monitoring:{project_id}"
        
        while True:
            try:
                # Get keywords to monitor
                keywords = await self.redis.smembers(monitoring_key)
                
                if keywords:
                    # Check rankings in parallel
                    tasks = [
                        self._check_keyword_ranking(project_id, keyword.decode())
                        for keyword in keywords
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results and detect changes
                    for result in results:
                        if isinstance(result, RankingSnapshot):
                            await self._process_ranking_change(project_id, result)
                            
                # Wait before next check
                await asyncio.sleep(self.alert_thresholds["check_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
                
    async def _check_keyword_ranking(self, project_id: str, keyword: str) -> RankingSnapshot:
        """Check current ranking for a keyword"""
        # Call DataForSEO API
        serp_data = await self.dataforseo.get_serp_data(keyword)
        
        # Extract ranking position
        position = None
        url = None
        competitors = []
        serp_features = []
        
        if serp_data.get("tasks") and serp_data["tasks"][0].get("result"):
            items = serp_data["tasks"][0]["result"][0].get("items", [])
            
            # Find our domain
            our_domain = await self._get_project_domain(project_id)
            
            for i, item in enumerate(items):
                if item["type"] == "organic":
                    if our_domain in item.get("url", ""):
                        position = i + 1
                        url = item["url"]
                    else:
                        competitors.append({
                            "position": i + 1,
                            "domain": item.get("domain"),
                            "title": item.get("title")
                        })
                        
            # Extract SERP features
            for item in items:
                if item["type"] != "organic":
                    serp_features.append(item["type"])
                    
        return RankingSnapshot(
            keyword=keyword,
            position=position or 0,
            url=url or "",
            timestamp=datetime.utcnow(),
            serp_features=list(set(serp_features)),
            competitors=competitors[:5]  # Top 5 competitors
        )
        
    async def _process_ranking_change(self, project_id: str, snapshot: RankingSnapshot):
        """Process ranking changes and generate alerts"""
        history_key = f"ranking_history:{project_id}:{snapshot.keyword}"
        
        # Get previous ranking
        previous_data = await self.redis.get(history_key)
        
        if previous_data:
            previous = json.loads(previous_data)
            previous_position = previous.get("position", 0)
            
            # Check for significant changes
            position_change = snapshot.position - previous_position
            
            # Generate alerts based on changes
            alerts = []
            
            # Rank drop alert
            if position_change >= self.alert_thresholds["rank_drop"]:
                alerts.append(Alert(
                    type=AlertType.RANK_DROP,
                    severity="warning" if position_change < 5 else "critical",
                    keyword=snapshot.keyword,
                    message=f"Ranking dropped from #{previous_position} to #{snapshot.position}",
                    data={
                        "previous_position": previous_position,
                        "current_position": snapshot.position,
                        "change": position_change
                    },
                    timestamp=snapshot.timestamp
                ))
                
            # Rank gain alert
            elif position_change <= -self.alert_thresholds["rank_drop"]:
                alerts.append(Alert(
                    type=AlertType.RANK_GAIN,
                    severity="info",
                    keyword=snapshot.keyword,
                    message=f"Ranking improved from #{previous_position} to #{snapshot.position}",
                    data={
                        "previous_position": previous_position,
                        "current_position": snapshot.position,
                        "change": position_change
                    },
                    timestamp=snapshot.timestamp
                ))
                
            # Check for new competitors
            previous_competitors = set(c["domain"] for c in previous.get("competitors", []))
            current_competitors = set(c["domain"] for c in snapshot.competitors)
            new_competitors = current_competitors - previous_competitors
            
            if new_competitors:
                alerts.append(Alert(
                    type=AlertType.NEW_COMPETITOR,
                    severity="info",
                    keyword=snapshot.keyword,
                    message=f"New competitors detected: {', '.join(new_competitors)}",
                    data={"new_competitors": list(new_competitors)},
                    timestamp=snapshot.timestamp
                ))
                
            # Check SERP features
            previous_features = set(previous.get("serp_features", []))
            current_features = set(snapshot.serp_features)
            
            lost_features = previous_features - current_features
            gained_features = current_features - previous_features
            
            if "featured_snippet" in lost_features:
                alerts.append(Alert(
                    type=AlertType.LOST_SNIPPET,
                    severity="critical",
                    keyword=snapshot.keyword,
                    message="Lost featured snippet",
                    data={"lost_features": list(lost_features)},
                    timestamp=snapshot.timestamp
                ))
            elif "featured_snippet" in gained_features:
                alerts.append(Alert(
                    type=AlertType.GAINED_SNIPPET,
                    severity="info",
                    keyword=snapshot.keyword,
                    message="Gained featured snippet!",
                    data={"gained_features": list(gained_features)},
                    timestamp=snapshot.timestamp
                ))
                
            # Send alerts
            for alert in alerts:
                await self._send_alert(project_id, alert)
                
        # Store current ranking
        await self.redis.set(
            history_key,
            json.dumps({
                "position": snapshot.position,
                "url": snapshot.url,
                "timestamp": snapshot.timestamp.isoformat(),
                "serp_features": snapshot.serp_features,
                "competitors": snapshot.competitors
            }),
            expire=86400 * 30  # Keep 30 days of history
        )
        
        # Store in time series for volatility analysis
        await self._update_volatility_metrics(project_id, snapshot)
        
    async def _update_volatility_metrics(self, project_id: str, snapshot: RankingSnapshot):
        """Update SERP volatility metrics"""
        volatility_key = f"volatility:{project_id}:{snapshot.keyword}"
        
        # Add to time series
        await self.redis.zadd(
            volatility_key,
            {str(snapshot.position): snapshot.timestamp.timestamp()}
        )
        
        # Keep only last 24 hours
        cutoff_time = (datetime.utcnow() - timedelta(hours=24)).timestamp()
        await self.redis.zremrangebyscore(volatility_key, 0, cutoff_time)
        
        # Calculate volatility
        positions = await self.redis.zrange(volatility_key, 0, -1)
        if len(positions) > 10:  # Need enough data points
            position_values = [int(p) for p in positions]
            volatility = np.std(position_values) / np.mean(position_values)
            
            if volatility > self.alert_thresholds["volatility_threshold"]:
                await self._send_alert(
                    project_id,
                    Alert(
                        type=AlertType.SERP_VOLATILITY,
                        severity="warning",
                        keyword=snapshot.keyword,
                        message=f"High SERP volatility detected: {volatility:.2%}",
                        data={"volatility": volatility, "positions": position_values[-10:]},
                        timestamp=snapshot.timestamp
                    )
                )
                
    async def _send_alert(self, project_id: str, alert: Alert):
        """Send alert through various channels"""
        # Store in Redis for retrieval
        alert_key = f"alerts:{project_id}"
        await self.redis.lpush(
            alert_key,
            json.dumps({
                "type": alert.type.value,
                "severity": alert.severity,
                "keyword": alert.keyword,
                "message": alert.message,
                "data": alert.data,
                "timestamp": alert.timestamp.isoformat()
            })
        )
        await self.redis.ltrim(alert_key, 0, 999)  # Keep last 1000 alerts
        
        # Send to WebSocket connections
        await self._broadcast_to_websockets(project_id, alert)
        
        # TODO: Send email/SMS/Slack notifications based on user preferences
        
    async def _broadcast_to_websockets(self, project_id: str, alert: Alert):
        """Broadcast alert to connected WebSocket clients"""
        message = {
            "type": "alert",
            "project_id": project_id,
            "alert": {
                "type": alert.type.value,
                "severity": alert.severity,
                "keyword": alert.keyword,
                "message": alert.message,
                "data": alert.data,
                "timestamp": alert.timestamp.isoformat()
            }
        }
        
        # Send to all connected clients
        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.add(websocket)
                
        # Clean up disconnected clients
        self.websocket_connections -= disconnected
        
    async def add_websocket(self, websocket: WebSocket):
        """Add WebSocket connection for real-time updates"""
        await websocket.accept()
        self.websocket_connections.add(websocket)
        
    async def remove_websocket(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
        
    async def _get_project_domain(self, project_id: str) -> str:
        """Get domain for project from database"""
        # TODO: Implement actual database lookup
        return "example.com"
        
    async def get_ranking_history(self, project_id: str, keyword: str, hours: int = 24) -> List[Dict]:
        """Get ranking history for a keyword"""
        volatility_key = f"volatility:{project_id}:{keyword}"
        
        # Get data from last N hours
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).timestamp()
        data = await self.redis.zrangebyscore(
            volatility_key,
            cutoff_time,
            "+inf",
            withscores=True
        )
        
        history = []
        for position, timestamp in data:
            history.append({
                "position": int(position),
                "timestamp": datetime.fromtimestamp(timestamp).isoformat()
            })
            
        return history

# WebSocket endpoint for FastAPI
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
monitoring_service = None  # Initialize with your service

@router.websocket("/ws/monitoring/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await monitoring_service.add_websocket(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle different message types
            message = json.loads(data)
            if message["type"] == "start_monitoring":
                await monitoring_service.start_monitoring(
                    project_id, 
                    message["keywords"]
                )
            elif message["type"] == "stop_monitoring":
                await monitoring_service.stop_monitoring(project_id)
                
    except WebSocketDisconnect:
        await monitoring_service.remove_websocket(websocket)