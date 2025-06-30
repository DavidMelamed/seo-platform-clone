"""
Database configuration and models
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import uuid
from datetime import datetime
from .config import settings

# Create engines
engine = create_engine(settings.DATABASE_URL)
async_engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Base class
Base = declarative_base()

# Models are now imported from separate files
# See models/ directory for model definitions

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

# Create tables
async def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)