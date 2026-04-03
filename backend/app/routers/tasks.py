"""Tasks Router - Task management and agent assignment"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.models.objects import TaskStatus, Priority
from app.models.tasks import TaskAssignment, TaskStatusUpdate, TaskContext
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.openclaw import openclaw_service
from app.services.context_builder import context_builder
from app.services.embedding import embedding_service

router = APIRouter()


@router.get("")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[Priority] = None,
    assigned_to: Optional[str] = None
):
    """List tasks with optional filtering"""
    client = qdrant_manager.get_client()
    
    # Build filter
    must_conditions = [{"key": "type", "match": {"value": "task"}}]
    
    if status:
        must_conditions.append({"key": "properties.status", "match": {"value": status}})
    
    if priority:
        must_conditions.append({"key": "properties.priority", "match": {"value": priority}})
    
    if assigned_to:
        must_conditions.append({"key": "properties.assigned_to", "match": {"value": assigned_to}})
    
    # Query
    results = client.scroll(
        collection_name="objects",
        scroll_filter={"must": must_conditions},
        limit=1000,
        with_payload=True
    )[0]
    
    tasks = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        tasks.append(payload)
    
    # Sort by priority and due date
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    tasks.sort(key=lambda t: (
        priority_order.get(t.get("properties", {}).get("priority", "medium"), 2),
        t.get("properties", {}).get("due_date") or "9999-12-31"
    ))
    
    # Count by status and priority
    by_status = {}
    by_priority = {}
    for task in tasks:
        s = task.get("properties", {}).get("status", "unknown")
        p = task.get("properties", {}).get("priority", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        by_priority[p] = by_priority.get(p, 0) + 1
    
    return {
        "tasks": tasks,
        "total": len(tasks),
        "by_status": by_status,
        "by_priority": by_priority
    }


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a single task by ID"""
    client = qdrant_manager.get_client()
    
    result = client.retrieve(
        collection_name="objects",
        ids=[task_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    payload = result[0].payload
    payload["id"] = result[0].id
    return payload


@router.post("/{task_id}/assign")
async def assign_task(task_id: str, assignment: TaskAssignment):
    """Assign a task to an agent"""
    client = qdrant_manager.get_client()
    
    # Get task
    result = client.retrieve(
        collection_name="objects",
        ids=[task_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = result[0].payload
    
    # Update task properties
    task["properties"]["assigned_to"] = assignment.agent_name
    task["properties"]["priority"] = assignment.priority
    task["properties"]["status"] = "todo"
    task["properties"]["updated_at"] = datetime.now().isoformat()
    
    # Update in Qdrant
    client.set_payload(
        collection_name="objects",
        payload=task,
        points=[task_id]
    )
    
    # Determine assignment method based on priority
    if assignment.priority in [Priority.LOW]:
        # Low priority: write to HEARTBEAT.md
        success = await openclaw_service.write_to_heartbeat(
            assignment.agent_name,
            {"id": task_id, "title": task["title"], "content": task.get("content", "")}
        )
        assignment_type = "heartbeat"
    else:
        # Medium/High/Urgent: direct assignment with full context
        if assignment.include_context:
            # Build context
            parent_id = task.get("properties", {}).get("parent_object_id")
            additional = assignment.additional_context or []
            
            context = await context_builder.build_task_context(
                task_id=task_id,
                object_id=task_id,
                parent_object_id=parent_id,
                additional_object_ids=additional
            )
            context["priority"] = assignment.priority.value
        else:
            context = {
                "task_id": task_id,
                "task_title": task["title"],
                "task_content": task.get("content", ""),
                "priority": assignment.priority.value
            }
        
        # Send to agent
        success = await openclaw_service.assign_task(
            task_id=task_id,
            agent_name=assignment.agent_name,
            context=context
        )
        assignment_type = "direct"
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to assign task to agent")
    
    # Broadcast event
    await websocket_manager.broadcast(
        WebSocketEvents.task_assigned(
            task_id=task_id,
            agent_name=assignment.agent_name,
            priority=assignment.priority.value,
            assignment_type=assignment_type
        )
    )
    
    return {
        "message": "Task assigned",
        "task_id": task_id,
        "agent_name": assignment.agent_name,
        "assignment_type": assignment_type
    }


@router.post("/{task_id}/status")
async def update_task_status(task_id: str, update: TaskStatusUpdate):
    """Update task status (called by agent via skill)"""
    client = qdrant_manager.get_client()
    
    # Get task
    result = client.retrieve(
        collection_name="objects",
        ids=[task_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = result[0].payload
    old_status = task["properties"].get("status", "todo")
    
    # Update status
    task["properties"]["status"] = update.status
    task["properties"]["current_action"] = update.current_action
    task["properties"]["updated_at"] = datetime.now().isoformat()
    
    if update.notes:
        task["properties"]["notes"] = update.notes
    
    if update.status == TaskStatus.DONE:
        task["properties"]["completed_at"] = datetime.now().isoformat()
    
    # Update in Qdrant
    client.set_payload(
        collection_name="objects",
        payload=task,
        points=[task_id]
    )
    
    # Broadcast event
    if update.status == TaskStatus.DONE:
        await websocket_manager.broadcast(
            WebSocketEvents.task_completed(
                task_id=task_id,
                agent_name=update.agent_name,
                notes=update.notes
            )
        )
    else:
        await websocket_manager.broadcast(
            WebSocketEvents.task_status_changed(
                task_id=task_id,
                old_status=old_status,
                new_status=update.status,
                agent_name=update.agent_name,
                current_action=update.current_action
            )
        )
    
    return {"message": "Status updated", "task_id": task_id, "status": update.status}


@router.get("/{task_id}/context")
async def get_task_context(task_id: str):
    """Get the context that would be sent to an agent"""
    client = qdrant_manager.get_client()
    
    # Get task
    result = client.retrieve(
        collection_name="objects",
        ids=[task_id],
        with_payload=True,
        with_vectors=False
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = result[0].payload
    parent_id = task.get("properties", {}).get("parent_object_id")
    
    # Build context
    context = await context_builder.build_task_context(
        task_id=task_id,
        object_id=task_id,
        parent_object_id=parent_id
    )
    
    return context
