"""Agents Router - Agent management and chat"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service
from app.services.openclaw import openclaw_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def list_agents():
    """List all registered agents"""
    # This would typically come from OpenClaw or a local registry
    # For now, return a placeholder list
    agents = [
        {
            "id": "agent-1",
            "name": "researcher",
            "description": "Research and information gathering agent",
            "status": "idle",
            "capabilities": ["search", "summarize", "analyze"]
        },
        {
            "id": "agent-2",
            "name": "writer",
            "description": "Content writing and editing agent",
            "status": "idle",
            "capabilities": ["write", "edit", "format"]
        }
    ]
    
    return {"agents": agents}


@router.get("/{name}")
async def get_agent(name: str):
    """Get agent details"""
    # Placeholder - would fetch from OpenClaw
    return {
        "id": f"agent-{name}",
        "name": name,
        "description": f"Agent {name}",
        "status": "idle",
        "capabilities": []
    }


@router.get("/{name}/tasks")
async def get_agent_tasks(
    name: str,
    status: Optional[str] = None
):
    """Get tasks assigned to an agent"""
    client = qdrant_manager.get_async_client()
    
    query_filter = {
        "must": [
            {"key": "type", "match": {"value": "task"}},
            {"key": "properties.assigned_to", "match": {"value": name}}
        ]
    }
    
    if status:
        query_filter["must"].append(
            {"key": "properties.status", "match": {"value": status}}
        )
    
    results = await client.scroll(
        collection_name="objects",
        scroll_filter=query_filter,
        limit=100,
        with_payload=True,
        with_vectors=False
    )
    
    tasks = []
    for result in results[0]:
        payload = result.payload
        payload["id"] = result.id
        tasks.append(payload)
    
    return {"tasks": tasks}


@router.post("/{name}/chat")
async def chat_with_agent(name: str, data: dict):
    """Send a message to an agent"""
    client = qdrant_manager.get_async_client()
    
    content = data.get("content", "")
    session_id = data.get("session_id")
    
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    
    # Store user message
    message_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    embedding = await embedding_service.embed_text(content)
    
    await client.upsert(
        collection_name="chat_logs",
        points=[{
            "id": message_id,
            "vector": embedding.tolist(),
            "payload": {
                "id": message_id,
                "role": "user",
                "content": content,
                "agent_name": name,
                "session_id": session_id,
                "timestamp": timestamp
            }
        }]
    )
    
    # Send to agent
    try:
        response = await openclaw_service.send_message(name, content)
        
        # Store agent response
        response_id = str(uuid.uuid4())
        response_content = response.get("content", "")
        response_embedding = await embedding_service.embed_text(response_content)
        
        await client.upsert(
            collection_name="chat_logs",
            points=[{
                "id": response_id,
                "vector": response_embedding.tolist(),
                "payload": {
                    "id": response_id,
                    "role": "agent",
                    "content": response_content,
                    "agent_name": name,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": response.get("metadata", {})
                }
            }]
        )
        
        # Broadcast event
        await websocket_manager.broadcast(
            WebSocketEvents.agent_message(name, response_content)
        )
        
        return {
            "message_id": message_id,
            "response_id": response_id,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Error sending message to agent {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/{name}/chat")
async def get_chat_history(
    name: str,
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get chat history with an agent"""
    client = qdrant_manager.get_async_client()
    
    query_filter = {
        "must": [{"key": "agent_name", "match": {"value": name}}]
    }
    
    if session_id:
        query_filter["must"].append(
            {"key": "session_id", "match": {"value": session_id}}
        )
    
    results = await client.scroll(
        collection_name="chat_logs",
        scroll_filter=query_filter,
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    
    messages = []
    for result in results[0]:
        payload = result.payload
        payload["id"] = result.id
        messages.append(payload)
    
    # Sort by timestamp
    messages.sort(key=lambda x: x.get("timestamp", ""))
    
    return {"messages": messages}


@router.get("/{name}/memories")
async def get_agent_memories(
    name: str,
    query: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Get memories for an agent"""
    client = qdrant_manager.get_async_client()
    
    if query:
        # Semantic search
        query_embedding = await embedding_service.embed_text(query)
        
        results = await client.search(
            collection_name="agent_memories",
            query_vector=query_embedding.tolist(),
            query_filter={
                "must": [{"key": "agent_name", "match": {"value": name}}]
            },
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        memories = []
        for result in results:
            payload = result.payload
            payload["id"] = result.id
            payload["score"] = result.score
            memories.append(payload)
    else:
        # Get all memories
        results = await client.scroll(
            collection_name="agent_memories",
            scroll_filter={
                "must": [{"key": "agent_name", "match": {"value": name}}]
            },
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        memories = []
        for result in results[0]:
            payload = result.payload
            payload["id"] = result.id
            memories.append(payload)
    
    return {"memories": memories}
