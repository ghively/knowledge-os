"""Chat Router - Agent chat and messaging"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.services.openclaw import openclaw_service
from app.services.websocket_manager import websocket_manager, WebSocketEvents
from app.services.embedding import embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{agent_name}")
async def get_chat_history(
    agent_name: str,
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get chat history for an agent"""
    client = qdrant_manager.get_async_client()
    
    # Build filter
    query_filter = {
        "must": [
            {"key": "agent_name", "match": {"value": agent_name}}
        ]
    }
    
    if session_id:
        query_filter["must"].append(
            {"key": "session_id", "match": {"value": session_id}}
        )
    
    # Scroll through collection using async client
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


@router.post("/{agent_name}")
async def send_message(agent_name: str, data: dict):
    """Send a message to an agent"""
    client = qdrant_manager.get_async_client()
    
    content = data.get("content", "")
    session_id = data.get("session_id")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # Store user message
    message_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Get embedding for the message
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
                "agent_name": agent_name,
                "session_id": session_id,
                "timestamp": timestamp
            }
        }]
    )
    
    # Send to agent via OpenClaw
    try:
        response = await openclaw_service.send_message(agent_name, content)
        
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
                    "agent_name": agent_name,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": response.get("metadata", {})
                }
            }]
        )
        
        # Broadcast event
        await websocket_manager.broadcast(
            WebSocketEvents.agent_message(agent_name, response_content)
        )
        
        logger.info(f"Chat message sent to {agent_name}")
        
        return {
            "message_id": message_id,
            "response_id": response_id,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Failed to send message to {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
