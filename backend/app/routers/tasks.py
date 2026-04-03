"""Tasks Router - Task management and assignment"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.models.tasks import Task, TaskCreate, TaskUpdate, TaskListResponse, TaskStatus, Priority
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service
from app.services.openclaw import openclaw_service
from app.services.context_builder import context_builder
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(50, ge=1, le=1000)
):
    """List tasks with optional filtering"""
    client = qdrant_manager.get_async_client()
    
    # Build filter
    query_filter = {"must": [{"key": "type", "match": {"value": "task"}}]}
    
    if status:
        query_filter["must"].append({"key": "properties.status", "match": {"value": status}})
    
    if priority:
        query_filter["must"].append({"key": "properties.priority", "match": {"value": priority}})
    
    if assigned_to:
        query_filter["must"].append({"key": "properties.assigned_to", "match": {"value": assigned_to}})
    
    results = await client.scroll(
        collection_name="objects",
        scroll_filter=query_filter,
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    
    tasks = []
    for result in results[0]:
        payload = result.payload
        payload["id"] = result.id
        tasks.append(payload)
    
    return TaskListResponse(tasks=tasks)


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a single task"""
    client = qdrant_manager.get_async_client()
    
    results = await client.retrieve(
        collection_name="objects",
        ids=[task_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="Task not found")
    
    payload = results[0].payload
    payload["id"] = results[0].id
    
    return payload


@router.post("/{task_id}/assign")
async def assign_task(task_id: str, data: dict, background_tasks: BackgroundTasks):
    """Assign a task to an agent"""
    client = qdrant_manager.get_async_client()
    
    agent_name = data.get("agent_name")
    priority = data.get("priority", "medium")
    include_context = data.get("include_context", True)
    additional_context = data.get("additional_context", [])
    
    if not agent_name:
        raise HTTPException(status_code=400, detail="agent_name is required")
    
    # Get task
    task_result = await client.retrieve(
        collection_name="objects",
        ids=[task_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_result[0].payload
    
    # Build context if requested
    context = None
    if include_context:
        context = await context_builder.build_task_context(
            task_id=task_id,
            additional_objects=additional_context
        )
    
    # Route based on priority
    if priority in ["urgent", "high", "medium"]:
        # Direct API call
        logger.info(f"Assigning task {task_id} to {agent_name} via direct API")
        
        try:
            response = await openclaw_service.assign_task(
                agent_name=agent_name,
                task_id=task_id,
                task_content=task.get("content", ""),
                context=context
            )
            
            # Update task status
            task["properties"]["status"] = "in-progress"
            task["properties"]["assigned_to"] = agent_name
            task["properties"]["assigned_at"] = datetime.now().isoformat()
            
            await client.set_payload(
                collection_name="objects",
                payload=task,
                points=[task_id]
            )
            
            return {
                "message": "Task assigned via direct API",
                "task_id": task_id,
                "agent": agent_name,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Failed to assign task via API: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")
    
    else:
        # Low priority - write to HEARTBEAT.md
        logger.info(f"Assigning task {task_id} to {agent_name} via HEARTBEAT.md")
        
        # Write to heartbeat file
        heartbeat_entry = f"""
## Task Assignment - {datetime.now().isoformat()}

**Task ID:** {task_id}
**Agent:** {agent_name}
**Priority:** {priority}
**Content:** {task.get('content', '')}

{context if context else ''}

---
"""
        # Store in agent_memories collection instead of file
        memory_id = str(uuid.uuid4())
        embedding = await embedding_service.embed_text(task.get("content", ""))
        
        await client.upsert(
            collection_name="agent_memories",
            points=[{
                "id": memory_id,
                "vector": embedding.tolist(),
                "payload": {
                    "id": memory_id,
                    "agent_name": agent_name,
                    "task_id": task_id,
                    "content": heartbeat_entry,
                    "type": "heartbeat_task",
                    "timestamp": datetime.now().isoformat()
                }
            }]
        )
        
        # Update task status
        task["properties"]["status"] = "queued"
        task["properties"]["assigned_to"] = agent_name
        
        await client.set_payload(
            collection_name="objects",
            payload=task,
            points=[task_id]
        )
        
        return {
            "message": "Task queued in agent memories",
            "task_id": task_id,
            "agent": agent_name,
            "memory_id": memory_id
        }


@router.post("/{task_id}/status")
async def update_task_status(task_id: str, data: dict):
    """Update task status (called by agents)"""
    client = qdrant_manager.get_async_client()
    
    agent_name = data.get("agent_name")
    status = data.get("status")
    current_action = data.get("current_action")
    notes = data.get("notes")
    
    if not status:
        raise HTTPException(status_code=400, detail="status is required")
    
    # Validate status
    valid_statuses = ["todo", "in-progress", "blocked", "review", "done"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Get task
    task_result = await client.retrieve(
        collection_name="objects",
        ids=[task_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_result[0].payload
    
    # Update status
    task["properties"]["status"] = status
    
    if current_action:
        task["properties"]["current_action"] = current_action
    
    if notes:
        task["properties"]["notes"] = notes
    
    if status == "done":
        task["properties"]["completed_at"] = datetime.now().isoformat()
    
    await client.set_payload(
        collection_name="objects",
        payload=task,
        points=[task_id]
    )
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.task_status_changed(task_id, status, agent_name)
    )
    
    logger.info(f"Task {task_id} status updated to {status} by {agent_name}")
    
    return {"message": "Status updated", "task_id": task_id, "status": status}


@router.get("/{task_id}/context")
async def get_task_context(task_id: str):
    """Get context for a task"""
    context = await context_builder.build_task_context(task_id=task_id)
    return {"context": context}
