"""Chat Router - Agent chat and messaging"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.database.qdrant_client import qdrant_manager
from app.services.openclaw import openclaw_service
from app.services.websocket_manager import websocket_manager, WebSocketEvents

router = APIRouter()


@router.get("/{agent_name}")
async def get_chat_history(
    agent_name: str,
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get chat history for an agent"""
    client = qdrant_manager.get_client()
    
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
    
    # Scroll through collection
    results, _ = client.scroll(
        collection_name="chat_logs",
        scroll_filter=query_filter,
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    
    messages = []
    for result in results:
        payload = result.payload
        payload["id"] = result.id
        messages.append(payload)
    
    # Sort by timestamp
    messages.sort(key=lambda x: x.get("timestamp", ""))
    
    return {"messages": messages}


@router.post("/{agent_name}")
async def send_message(agent_name: str, data: dict):
    """Send a message to an agent"""
    content = data.get("content", "")
    session_id = data.get("session_id")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # Store user message
    client = qdrant_manager.get_client()
    import uuid
    
    message_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Get embedding for the message
    from app.services.embedding import embedding_service
    embedding = await embedding_service.embed_text(content)
    
    client.upsert(
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
        response_embedding = await embedding_service.embed_text(response.get("content", ""))
        
        client.upsert(
            collection_name="chat_logs",
            points=[{
                "id": response_id,
                "vector": response_embedding.tolist(),
                "payload": {
                    "id": response_id,
                    "role": "agent",
                    "content": response.get("content", ""),
                    "agent_name": agent_name,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": response.get("metadata", {})
                }
            }]
        )
        
        # Broadcast event
        await websocket_manager.broadcast(
            WebSocketEvents.agent_message(agent_name, response.get("content", ""))
        )
        
        return {
            "message_id": message_id,
            "response_id": response_id,
            "response": response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
