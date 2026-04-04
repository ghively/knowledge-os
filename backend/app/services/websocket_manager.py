"""WebSocket Manager - Handles real-time communication."""
from __future__ import annotations
import json
import logging
from collections import defaultdict
from typing import DefaultDict, List, Set

from fastapi import WebSocket
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message validation model."""
    type: str
    data: dict = {}


class WebSocketEvents:
    """WebSocket event factory."""

    @staticmethod
    def object_created(object_id: str, object_type: str, title: str):
        return {"type": "object.created", "channel": "objects", "data": {"id": object_id, "type": object_type, "title": title}}

    @staticmethod
    def object_updated(object_id: str, changes: List[str]):
        return {"type": "object.updated", "channel": "objects", "data": {"id": object_id, "changes": changes}}

    @staticmethod
    def object_deleted(object_id: str):
        return {"type": "object.deleted", "channel": "objects", "data": {"id": object_id}}

    @staticmethod
    def block_created(block_id: str, object_id: str):
        return {"type": "block.created", "channel": f"object:{object_id}", "data": {"id": block_id, "object_id": object_id}}

    @staticmethod
    def block_updated(block_id: str, object_id: str):
        return {"type": "block.updated", "channel": f"object:{object_id}", "data": {"id": block_id, "object_id": object_id}}

    @staticmethod
    def block_deleted(block_id: str, object_id: str):
        return {"type": "block.deleted", "channel": f"object:{object_id}", "data": {"id": block_id, "object_id": object_id}}

    @staticmethod
    def task_assigned(task_id: str, agent_name: str, priority: str, route: str):
        return {"type": "task.assigned", "channel": "tasks", "data": {"id": task_id, "agent": agent_name, "priority": priority, "route": route}}

    @staticmethod
    def task_status_changed(task_id: str, status: str, agent_name: str):
        return {"type": "task.status_changed", "channel": "tasks", "data": {"id": task_id, "status": status, "agent": agent_name}}

    @staticmethod
    def task_progress_update(task_id: str, current_action: str, agent_name: str):
        return {"type": "task.progress_update", "channel": "tasks", "data": {"id": task_id, "current_action": current_action, "agent": agent_name}}

    @staticmethod
    def task_completed(task_id: str, agent_name: str):
        return {"type": "task.completed", "channel": "tasks", "data": {"id": task_id, "agent": agent_name}}

    @staticmethod
    def agent_status_changed(agent_name: str, status: str):
        return {"type": "agent.status_changed", "channel": "agents", "data": {"agent": agent_name, "status": status}}

    @staticmethod
    def agent_current_action(agent_name: str, current_action: str, task_id: str | None = None):
        return {"type": "agent.current_action", "channel": "agents", "data": {"agent": agent_name, "current_action": current_action, "task_id": task_id}}

    @staticmethod
    def chat_message(agent_name: str, content: str, session_id: str | None = None):
        return {"type": "chat.message", "channel": f"agent:{agent_name}", "data": {"agent": agent_name, "content": content, "session_id": session_id}}

    @staticmethod
    def file_indexed(file_id: str, path: str):
        return {"type": "file.indexed", "channel": "files", "data": {"id": file_id, "path": path}}

    @staticmethod
    def file_reindexed(file_id: str, path: str):
        return {"type": "file.indexed", "channel": "files", "data": {"id": file_id, "path": path, "reindexed": True}}


class WebSocketManager:
    """Manages WebSocket connections and channel subscriptions."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: DefaultDict[WebSocket, Set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket].add("system")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)

    async def broadcast(self, message: dict):
        disconnected = set()
        channel = message.get("channel")
        for websocket in self.active_connections:
            subscriptions = self.subscriptions.get(websocket, {"system"})
            if channel and channel not in subscriptions and "system" not in subscriptions:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        for websocket in disconnected:
            self.disconnect(websocket)

    async def handle_message(self, websocket: WebSocket, data: str):
        try:
            raw = json.loads(data)
            message = WebSocketMessage(**raw)
        except json.JSONDecodeError:
            await websocket.send_json({"type": "error", "data": {"message": "Invalid JSON"}})
            return
        except ValidationError:
            await websocket.send_json({"type": "error", "data": {"message": "Invalid message format"}})
            return

        if message.type == "ping":
            await websocket.send_json({"type": "pong", "data": {}})
            return

        if message.type == "subscribe":
            channels = message.data.get("channels", [])
            for channel in channels:
                self.subscriptions[websocket].add(channel)
            await websocket.send_json({"type": "subscribed", "data": {"channels": sorted(self.subscriptions[websocket])}})
            return

        if message.type == "unsubscribe":
            channels = message.data.get("channels", [])
            for channel in channels:
                self.subscriptions[websocket].discard(channel)
            await websocket.send_json({"type": "unsubscribed", "data": {"channels": channels}})


websocket_manager = WebSocketManager()
