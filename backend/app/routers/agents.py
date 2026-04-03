"""Agents Router - Agent management and chat"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.services.openclaw import openclaw_service
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service

router = APIRouter()


@router.get("")
async def list_agents():
    """List all agents (from agent objects)"""
    client = qdrant_manager.get_client()
    
    results = client.scroll(
        collection_name="objects",
        scroll_filter={
            "must": [{"key": "type", "match": {"value": "agent"}}]
        },
        limit=100,
        with_payload=True
    )[0]
    
    agents = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        agents.append(payload)
    
    return {"agents": agents}


@router.get("/{agent_name}")
async def get_agent(agent_name: str):
    """Get agent details"""
    client = qdrant_manager.get_client()
    
    # Search by agent_name property
    results = client.scroll(
        collection_name="objects",
        scroll_filter={
            "must": [
                {"key": "type", "match": {"value": "agent"}},
                {"key": "properties.agent_name", "match": {"value": agent_name}}
            ]
        },
        limit=1,
        with_payload=True
    )[0]
    
    if not results:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    payload = results[0].payload
    payload["id"] = results[0].id
    
    # Get agent status from OpenClaw
    status = await openclaw_service.get_agent_status(agent_name)
    payload["live_status"] = status
    
    return payload


@router.get("/{agent_name}/tasks")
async def get_agent_tasks(agent_name: str, status: Optional[str] = None):
    """Get tasks assigned to an agent"""
    client = qdrant_manager.get_client()
    
    must_conditions = [
        {"key": "type", "match": {"value": "task"}},
        {"key": "properties.assigned_to", "match": {"value": agent_name}}
    ]
    
    if status:
        must_conditions.append({"key": "properties.status", "match": {"value": status}})
    
    results = client.scroll(
        collection_name="objects",
        scroll_filter={"must": must_conditions},
        limit=100,
        with_payload=True
    )[0]
    
    tasks = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        tasks.append(payload)
    
    return {"tasks": tasks}


@router.post("/{agent_name}/chat")
async def chat_with_agent(agent_name: str, message: dict):
    """Send a message to an agent"""
    content = message.get("content", "")
    session_id = message.get("session_id", "main")
    
    if not content:
        raise HTTPException(status_code=400, detail="Message content required")
    
    # Send to OpenClaw
    result = await openclaw_service.send_message(
        agent_name=agent_name,
        message=content,
        session_id=session_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Store chat log in Qdrant
    await _store_chat_message(
        session_id=session_id,
        agent_name=agent_name,
        message_type="user",
        content=content
    )
    
    # Store agent response
    agent_content = result.get("content", "")
    if agent_content:
        await _store_chat_message(
            session_id=session_id,
            agent_name=agent_name,
            message_type="agent",
            content=agent_content,
            metadata={
                "tools_used": result.get("tools_used", []),
                "agent_thoughts": result.get("thoughts", "")
            }
        )
    
    # Broadcast chat message
    await websocket_manager.broadcast(
        WebSocketEvents.chat_message(
            session_id=session_id,
            agent_name=agent_name,
            message_type="agent",
            content=agent_content
        )
    )
    
    return result


@router.get("/{agent_name}/chat")
async def get_chat_history(agent_name: str, session_id: Optional[str] = None):
    """Get chat history with an agent"""
    client = qdrant_manager.get_client()
    
    must_conditions = [
        {"key": "agent_name", "match": {"value": agent_name}}
    ]
    
    if session_id:
        must_conditions.append({"key": "session_id", "match": {"value": session_id}})
    
    results = client.scroll(
        collection_name="chat_logs",
        scroll_filter={"must": must_conditions},
        limit=100,
        with_payload=True
    )[0]
    
    messages = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        messages.append(payload)
    
    # Sort by timestamp
    messages.sort(key=lambda m: m.get("timestamp", ""))
    
    return {"messages": messages}


@router.get("/{agent_name}/memories")
async def get_agent_memories(agent_name: str, query: Optional[str] = None):
    """Get agent memories, optionally filtered by query"""
    client = qdrant_manager.get_client()
    
    if query:
        # Semantic search
        embedding = await embedding_service.embed_text(query)
        
        results = client.search(
            collection_name="agent_memories",
            query_vector=embedding.tolist(),
            query_filter={
                "must": [{"key": "agent_name", "match": {"value": agent_name}}]
            },
            limit=20,
            with_payload=True
        )
        
        memories = []
        for result in results:
            payload = result.payload
            payload["id"] = result.id
            payload["score"] = result.score
            memories.append(payload)
    else:
        # Get all memories
        results = client.scroll(
            collection_name="agent_memories",
            scroll_filter={
                "must": [{"key": "agent_name", "match": {"value": agent_name}}]
            },
            limit=100,
            with_payload=True
        )[0]
        
        memories = []
        for result in results:
            payload = result.payload
            payload["id"] = result.id
            memories.append(payload)
        
        # Sort by timestamp
        memories.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
    
    return {"memories": memories}


async def _store_chat_message(session_id: str, agent_name: str, 
                               message_type: str, content: str,
                               metadata: dict = None):
    """Store a chat message in Qdrant"""
    client = qdrant_manager.get_client()
    
    message_id = str(__import__('uuid').uuid4())
    
    # Generate embedding
    embedding = await embedding_service.embed_text(content)
    
    payload = {
        "id": message_id,
        "session_id": session_id,
        "agent_name": agent_name,
        "message_type": message_type,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    client.upsert(
        collection_name="chat_logs",
        points=[{
            "id": message_id,
            "vector": embedding.tolist(),
            "payload": payload
        }]
    )
