"""
Automation API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json

from core.database import get_db, Project, WorkflowExecution
from api.auth import get_current_user, User
from core.redis_client import redis_client

router = APIRouter()

# Pydantic models
class WorkflowCreate(BaseModel):
    name: str
    description: str
    steps: List[Dict[str, Any]]
    schedule: Optional[str] = None  # cron expression
    enabled: bool = True

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    schedule: Optional[str]
    enabled: bool
    created_at: datetime

class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    output_data: Dict[str, Any]

class BulkOperationRequest(BaseModel):
    operation_type: str
    items: List[Dict[str, Any]]
    batch_size: int = 100

# Helper functions
def get_user_project(project_id: str, user: User, db: Session):
    """Get project and verify user access"""
    project = db.query(Project).filter(
        and_(Project.id == project_id, Project.org_id == user.org_id)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

async def execute_workflow_step(step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single workflow step"""
    
    action = step.get("action")
    parameters = step.get("parameters", {})
    
    # Mock workflow execution for different action types
    if action == "keyword_research":
        return {
            "success": True,
            "message": f"Analyzed {parameters.get('keyword_count', 10)} keywords",
            "data": {
                "keywords_found": 25,
                "avg_difficulty": 45.2
            }
        }
    
    elif action == "content_optimization":
        return {
            "success": True,
            "message": f"Optimized {parameters.get('page_count', 5)} pages",
            "data": {
                "pages_updated": 5,
                "seo_score_improvement": 15.3
            }
        }
    
    elif action == "rank_tracking":
        return {
            "success": True,
            "message": f"Tracked rankings for {parameters.get('keyword_count', 20)} keywords",
            "data": {
                "positions_checked": 20,
                "improvements": 8,
                "declines": 3
            }
        }
    
    elif action == "backlink_analysis":
        return {
            "success": True,
            "message": f"Analyzed backlinks for {parameters.get('domain', 'domain')}",
            "data": {
                "new_backlinks": 12,
                "lost_backlinks": 2,
                "domain_rating": 65
            }
        }
    
    elif action == "technical_audit":
        return {
            "success": True,
            "message": "Completed technical SEO audit",
            "data": {
                "issues_found": 15,
                "critical_issues": 3,
                "warnings": 12
            }
        }
    
    else:
        return {
            "success": False,
            "message": f"Unknown action: {action}",
            "data": {}
        }

# API endpoints
@router.get("/workflows/{project_id}", response_model=List[WorkflowResponse])
async def get_workflows(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflows for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get workflows from Redis (in production, use database)
    workflows_key = f"workflows:{project_id}"
    workflows_data = await redis_client.get_json(workflows_key)
    
    if not workflows_data:
        workflows_data = []
    
    return [
        WorkflowResponse(
            id=wf["id"],
            name=wf["name"],
            description=wf["description"],
            steps=wf["steps"],
            schedule=wf.get("schedule"),
            enabled=wf.get("enabled", True),
            created_at=datetime.fromisoformat(wf["created_at"])
        )
        for wf in workflows_data
    ]

@router.post("/workflows/{project_id}", response_model=WorkflowResponse)
async def create_workflow(
    project_id: str,
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new workflow"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Create workflow
    workflow = {
        "id": str(uuid.uuid4()),
        "name": workflow_data.name,
        "description": workflow_data.description,
        "steps": workflow_data.steps,
        "schedule": workflow_data.schedule,
        "enabled": workflow_data.enabled,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store in Redis
    workflows_key = f"workflows:{project_id}"
    existing_workflows = await redis_client.get_json(workflows_key) or []
    existing_workflows.append(workflow)
    await redis_client.set(workflows_key, existing_workflows)
    
    return WorkflowResponse(
        id=workflow["id"],
        name=workflow["name"],
        description=workflow["description"],
        steps=workflow["steps"],
        schedule=workflow["schedule"],
        enabled=workflow["enabled"],
        created_at=datetime.fromisoformat(workflow["created_at"])
    )

@router.post("/workflows/{project_id}/{workflow_id}/execute")
async def execute_workflow(
    project_id: str,
    workflow_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a workflow"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get workflow
    workflows_key = f"workflows:{project_id}"
    workflows_data = await redis_client.get_json(workflows_key) or []
    
    workflow = next((wf for wf in workflows_data if wf["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create execution record
    execution = WorkflowExecution(
        project_id=project_id,
        workflow_name=workflow["name"],
        status="pending",
        input_data={"workflow_id": workflow_id}
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Execute workflow in background
    background_tasks.add_task(
        run_workflow_execution,
        str(execution.id),
        workflow,
        project_id
    )
    
    return {
        "execution_id": str(execution.id),
        "message": "Workflow execution started",
        "status": "pending"
    }

@router.get("/executions/{project_id}", response_model=List[WorkflowExecutionResponse])
async def get_workflow_executions(
    project_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow executions for a project"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Get executions
    executions = db.query(WorkflowExecution).filter(
        WorkflowExecution.project_id == project_id
    ).order_by(WorkflowExecution.started_at.desc()).limit(limit).all()
    
    return [
        WorkflowExecutionResponse(
            id=str(execution.id),
            workflow_name=execution.workflow_name,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            output_data=execution.output_data or {}
        )
        for execution in executions
    ]

@router.get("/executions/{execution_id}/status")
async def get_execution_status(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of a workflow execution"""
    
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Verify access
    get_user_project(str(execution.project_id), current_user, db)
    
    return {
        "id": str(execution.id),
        "status": execution.status,
        "started_at": execution.started_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "output_data": execution.output_data or {},
        "error_log": execution.error_log
    }

@router.post("/bulk-operations/{project_id}")
async def create_bulk_operation(
    project_id: str,
    request: BulkOperationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and execute a bulk operation"""
    
    # Verify project access
    project = get_user_project(project_id, current_user, db)
    
    # Create execution record
    execution = WorkflowExecution(
        project_id=project_id,
        workflow_name=f"Bulk {request.operation_type}",
        status="pending",
        input_data={
            "operation_type": request.operation_type,
            "item_count": len(request.items),
            "batch_size": request.batch_size
        }
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Execute bulk operation in background
    background_tasks.add_task(
        run_bulk_operation,
        str(execution.id),
        request.operation_type,
        request.items,
        request.batch_size
    )
    
    return {
        "execution_id": str(execution.id),
        "message": f"Bulk operation started for {len(request.items)} items",
        "status": "pending"
    }

@router.get("/templates")
async def get_workflow_templates():
    """Get predefined workflow templates"""
    
    templates = [
        {
            "id": "weekly_seo_audit",
            "name": "Weekly SEO Audit",
            "description": "Comprehensive weekly SEO audit with automated fixes",
            "steps": [
                {
                    "name": "Technical Audit",
                    "action": "technical_audit",
                    "parameters": {"depth": "comprehensive"}
                },
                {
                    "name": "Rank Tracking",
                    "action": "rank_tracking",
                    "parameters": {"keyword_count": 50}
                },
                {
                    "name": "Backlink Analysis",
                    "action": "backlink_analysis",
                    "parameters": {"check_quality": True}
                }
            ],
            "schedule": "0 2 * * 1",  # Every Monday at 2 AM
            "category": "audit"
        },
        {
            "id": "content_optimization",
            "name": "Content Optimization Pipeline",
            "description": "Identify and optimize underperforming content",
            "steps": [
                {
                    "name": "Content Analysis",
                    "action": "content_optimization",
                    "parameters": {"min_traffic": 100, "max_score": 70}
                },
                {
                    "name": "Keyword Research",
                    "action": "keyword_research",
                    "parameters": {"related_keywords": True}
                }
            ],
            "schedule": None,
            "category": "content"
        },
        {
            "id": "competitor_monitoring",
            "name": "Competitor Monitoring",
            "description": "Track competitor rankings and identify opportunities",
            "steps": [
                {
                    "name": "Competitor Rank Check",
                    "action": "rank_tracking",
                    "parameters": {"include_competitors": True}
                },
                {
                    "name": "Backlink Monitoring",
                    "action": "backlink_analysis",
                    "parameters": {"competitor_check": True}
                }
            ],
            "schedule": "0 6 * * *",  # Daily at 6 AM
            "category": "competitor"
        }
    ]
    
    return {"templates": templates}

# Background task functions
async def run_workflow_execution(execution_id: str, workflow: Dict[str, Any], project_id: str):
    """Execute workflow steps in sequence"""
    
    from core.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Get execution record
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            return
        
        # Update status to running
        execution.status = "running"
        db.commit()
        
        # Execute steps
        context = {"project_id": project_id}
        output_data = {}
        
        for i, step in enumerate(workflow["steps"]):
            step_name = step.get("name", f"Step {i+1}")
            
            try:
                # Execute step
                result = await execute_workflow_step(step, context)
                output_data[step_name] = result
                
                # Update context with result
                context[f"step_{i}"] = result
                
                if not result.get("success", True):
                    # Step failed
                    execution.status = "failed"
                    execution.error_log = result.get("message", "Step failed")
                    break
                    
            except Exception as e:
                execution.status = "failed"
                execution.error_log = f"Error in step '{step_name}': {str(e)}"
                break
        
        # Update execution record
        if execution.status != "failed":
            execution.status = "completed"
        
        execution.output_data = output_data
        execution.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Handle any unexpected errors
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if execution:
            execution.status = "failed"
            execution.error_log = f"Unexpected error: {str(e)}"
            execution.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()

async def run_bulk_operation(execution_id: str, operation_type: str, items: List[Dict], batch_size: int):
    """Execute bulk operation in batches"""
    
    from core.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Get execution record
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            return
        
        # Update status to running
        execution.status = "running"
        db.commit()
        
        # Process items in batches
        processed = 0
        failed = 0
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch (mock implementation)
            for item in batch:
                try:
                    # Simulate processing
                    await asyncio.sleep(0.1)  # Simulate work
                    processed += 1
                except Exception:
                    failed += 1
        
        # Update execution record
        execution.status = "completed"
        execution.output_data = {
            "processed": processed,
            "failed": failed,
            "total": len(items)
        }
        execution.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Handle any unexpected errors
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if execution:
            execution.status = "failed"
            execution.error_log = f"Bulk operation error: {str(e)}"
            execution.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()