"""Legacy chat router maintained for compatibility."""
from fastapi import APIRouter, Query

from app.routers import agents

router = APIRouter()


@router.get("/{agent_name}")
async def get_chat_history(agent_name: str, session_id: str | None = None, limit: int = Query(50, ge=1, le=200)):
    return await agents.get_chat_history(agent_name, session_id=session_id, limit=limit)


@router.post("/{agent_name}")
async def send_message(agent_name: str, data: dict):
    return await agents.chat_with_agent(agent_name, data)
