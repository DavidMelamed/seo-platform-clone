"""
Projects API endpoints for project management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import asyncio
import httpx

from core.database import get_db
from models import User, Project, Keyword, Ranking, Alert
from core.deps import get_current_user

router = APIRouter()

# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    domain: str
    description: Optional[str] = None
    settings: Dict[str, Any] = {}

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ProjectStats(BaseModel):
    keywords_count: int
    avg_position: float
    top_10_count: int
    total_rankings: int
    last_updated: Optional[datetime]

class ProjectResponse(BaseModel):
    id: str
    name: str
    domain: str
    description: Optional[str]
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    stats: Optional[ProjectStats] = None

class DomainAnalysis(BaseModel):
    domain: str
    is_accessible: bool
    has_ssl: bool
    page_title: Optional[str]
    meta_description: Optional[str]
    status_code: Optional[int]
    response_time_ms: Optional[int]


async def analyze_domain(domain: str) -> DomainAnalysis:
    """Analyze domain for basic SEO metrics"""
    
    # Ensure domain has protocol
    if not domain.startswith(('http://', 'https://')):
        test_url = f"https://{domain}"
    else:
        test_url = domain
    
    analysis = DomainAnalysis(
        domain=domain,
        is_accessible=False,
        has_ssl=False,
        page_title=None,
        meta_description=None,
        status_code=None,
        response_time_ms=None
    )
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            start_time = datetime.now()
            response = await client.get(test_url)
            end_time = datetime.now()
            
            analysis.status_code = response.status_code
            analysis.response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            analysis.is_accessible = response.status_code == 200
            analysis.has_ssl = test_url.startswith('https://')
            
            if response.status_code == 200:
                # Parse HTML for basic SEO elements
                html_content = response.text.lower()
                
                # Extract title
                title_start = html_content.find('<title>')
                if title_start != -1:
                    title_start += 7
                    title_end = html_content.find('</title>', title_start)
                    if title_end != -1:
                        analysis.page_title = response.text[title_start:title_end].strip()
                
                # Extract meta description
                meta_desc_pos = html_content.find('name="description"')
                if meta_desc_pos != -1:
                    content_start = html_content.find('content="', meta_desc_pos)
                    if content_start != -1:
                        content_start += 9
                        content_end = html_content.find('"', content_start)
                        if content_end != -1:
                            analysis.meta_description = response.text[content_start:content_end].strip()
                            
    except Exception as e:
        # Log error but return analysis with failed status
        print(f"Domain analysis failed for {domain}: {str(e)}")
    
    return analysis


def get_project_stats(project: Project, db: Session) -> ProjectStats:
    """Get statistics for a project"""
    
    # Count keywords
    keywords_count = db.query(Keyword).filter(
        Keyword.project_id == project.id,
        Keyword.is_active == True
    ).count()
    
    # Get average position from latest rankings
    avg_position_result = db.execute("""
        SELECT AVG(latest_rankings.position) as avg_pos
        FROM (
            SELECT DISTINCT ON (k.id) k.id, r.position
            FROM keywords k
            LEFT JOIN rankings r ON k.id = r.keyword_id
            WHERE k.project_id = %s
            AND k.is_active = true
            ORDER BY k.id, r.recorded_at DESC
        ) as latest_rankings
        WHERE latest_rankings.position IS NOT NULL
    """, (str(project.id),))
    
    avg_position = avg_position_result.fetchone()
    avg_position = float(avg_position[0]) if avg_position and avg_position[0] else 0.0
    
    # Count top 10 keywords
    top_10_result = db.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT ON (k.id) k.id, r.position
            FROM keywords k
            LEFT JOIN rankings r ON k.id = r.keyword_id
            WHERE k.project_id = %s
            AND k.is_active = true
            ORDER BY k.id, r.recorded_at DESC
        ) as latest_rankings
        WHERE latest_rankings.position <= 10
    """, (str(project.id),))
    
    top_10_count = int(top_10_result.fetchone()[0])
    
    # Total rankings
    total_rankings = db.query(Ranking).join(Keyword).filter(
        Keyword.project_id == project.id
    ).count()
    
    # Last updated
    last_ranking = db.query(Ranking).join(Keyword).filter(
        Keyword.project_id == project.id
    ).order_by(desc(Ranking.recorded_at)).first()
    
    return ProjectStats(
        keywords_count=keywords_count,
        avg_position=round(avg_position, 1),
        top_10_count=top_10_count,
        total_rankings=total_rankings,
        last_updated=last_ranking.recorded_at if last_ranking else None
    )


@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_stats: bool = Query(False, description="Include project statistics"),
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of projects to return")
):
    """Get all projects for the current user's organization"""
    
    projects = db.query(Project).filter(
        Project.org_id == current_user.org_id
    ).order_by(desc(Project.updated_at)).offset(skip).limit(limit).all()
    
    result = []
    for project in projects:
        project_data = ProjectResponse(
            id=str(project.id),
            name=project.name,
            domain=project.domain,
            description=project.description,
            settings=project.settings or {},
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
        if include_stats:
            project_data.stats = get_project_stats(project, db)
        
        result.append(project_data)
    
    return result


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    
    # Check if project with same domain already exists for this org
    existing_project = db.query(Project).filter(
        Project.org_id == current_user.org_id,
        Project.domain == project_data.domain,
        Project.is_active == True
    ).first()
    
    if existing_project:
        raise HTTPException(
            status_code=400,
            detail="Project with this domain already exists"
        )
    
    # Create project
    project = Project(
        org_id=current_user.org_id,
        name=project_data.name,
        domain=project_data.domain,
        description=project_data.description,
        settings=project_data.settings
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Schedule domain analysis in background
    background_tasks.add_task(analyze_project_domain, str(project.id), project_data.domain)
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        domain=project.domain,
        description=project.description,
        settings=project.settings or {},
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_stats: bool = Query(True, description="Include project statistics")
):
    """Get a specific project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == current_user.org_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = ProjectResponse(
        id=str(project.id),
        name=project.name,
        domain=project.domain,
        description=project.description,
        settings=project.settings or {},
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at
    )
    
    if include_stats:
        project_data.stats = get_project_stats(project, db)
    
    return project_data


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == current_user.org_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        domain=project.domain,
        description=project.description,
        settings=project.settings or {},
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project (soft delete)"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == current_user.org_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Soft delete
    project.is_active = False
    project.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/analyze", response_model=DomainAnalysis)
async def analyze_project_domain_endpoint(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze the domain for a project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.org_id == current_user.org_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    analysis = await analyze_domain(project.domain)
    
    # Store analysis results in project settings
    if not project.settings:
        project.settings = {}
    
    project.settings["domain_analysis"] = {
        "last_analyzed": datetime.utcnow().isoformat(),
        "is_accessible": analysis.is_accessible,
        "has_ssl": analysis.has_ssl,
        "status_code": analysis.status_code,
        "response_time_ms": analysis.response_time_ms,
        "page_title": analysis.page_title,
        "meta_description": analysis.meta_description
    }
    
    project.updated_at = datetime.utcnow()
    db.commit()
    
    return analysis


async def analyze_project_domain(project_id: str, domain: str):
    """Background task to analyze project domain"""
    # This would be called as a background task
    # For now, just a placeholder - in production this would 
    # update the database with analysis results
    try:
        analysis = await analyze_domain(domain)
        print(f"Domain analysis completed for {domain}: {analysis.is_accessible}")
    except Exception as e:
        print(f"Background domain analysis failed: {str(e)}")