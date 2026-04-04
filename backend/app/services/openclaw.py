"""OpenClaw Service - Integration with OpenClaw gateway."""
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.database.sqlite import sqlite_manager

logger = logging.getLogger(__name__)


class OpenClawService:
    """Service for communicating with OpenClaw."""

    async def _runtime_settings(self) -> Dict[str, Any]:
        return {
            "openclaw_url": await sqlite_manager.get_setting("openclaw_url", settings.openclaw_url),
            "openclaw_token": await sqlite_manager.get_setting("openclaw_token", settings.openclaw_token),
            "openclaw_enabled": await sqlite_manager.get_setting("openclaw_enabled", True),
        }

    async def _request(self, method: str, path: str, payload: Optional[dict] = None) -> Dict[str, Any]:
        runtime = await self._runtime_settings()
        if not runtime["openclaw_enabled"]:
            return {"status": "disabled", "content": "OpenClaw integration disabled", "metadata": {}}

        headers = {"Content-Type": "application/json"}
        if runtime["openclaw_token"]:
            headers["Authorization"] = f"Bearer {runtime['openclaw_token']}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                f"{runtime['openclaw_url'].rstrip('/')}{path}",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json() if response.content else {}

    async def send_message(self, agent_name: str, content: str, session_id: str = "main") -> Dict[str, Any]:
        payload = {
            "agent": agent_name,
            "messages": [{"role": "user", "content": content}],
        }
        try:
            return await self._request("POST", f"/api/sessions/{session_id}/messages", payload)
        except Exception as exc:
            logger.error("OpenClaw send_message failed: %s", exc)
            return {"status": "error", "content": str(exc), "metadata": {}}

    async def assign_task(self, agent_name: str, task_id: str, task_content: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        payload = {
            "agent": agent_name,
            "messages": [{
                "role": "user",
                "content": f"Task {task_id}\n\n{task_content}\n\nContext:\n{context or {}}",
            }],
        }
        try:
            return await self._request("POST", "/api/sessions/main/messages", payload)
        except Exception as exc:
            logger.error("OpenClaw assign_task failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        try:
            response = await self._request("GET", "/api/sessions")
            sessions = response if isinstance(response, list) else response.get("sessions", [])
            for session in sessions:
                if session.get("agent") == agent_name or session.get("agent_name") == agent_name:
                    return {
                        "status": session.get("status", "idle"),
                        "current_action": session.get("current_action"),
                        "last_seen": session.get("updated_at") or session.get("last_seen"),
                    }
        except Exception as exc:
            logger.debug("OpenClaw get_agent_status fallback for %s: %s", agent_name, exc)
        return {"status": "offline"}


openclaw_service = OpenClawService()
