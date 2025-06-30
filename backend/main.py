"""
SEO Platform - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from datetime import datetime

# Import routers
from api.auth import router as auth_router
from api.keywords import router as keywords_router
from api.analytics import router as analytics_router
from api.monitoring import router as monitoring_router
from api.automation import router as automation_router
from api.ai_services import router as ai_router

# Core imports
from core.config import settings
from core.database import engine, create_tables
from core.redis_client import redis_client

# Create FastAPI app
app = FastAPI(
    title="SEO Intelligence Platform",
    description="Next-generation SEO platform with AI and real-time capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(keywords_router, prefix="/api/v1/keywords", tags=["Keywords"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(automation_router, prefix="/api/v1/automation", tags=["Automation"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Services"])

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Check Redis
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "redis": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SEO Intelligence Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    print("🚀 Starting SEO Intelligence Platform...")
    
    # Create database tables
    await create_tables()
    print("✅ Database tables created")
    
    # Initialize Redis
    try:
        await redis_client.ping()
        print("✅ Redis connection established")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
    
    print("🎉 Platform started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    print("🛑 Shutting down SEO Intelligence Platform...")
    await redis_client.close()
    print("✅ Cleanup completed")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )