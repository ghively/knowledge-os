"""WebSocket Manager for Real-Time Updates"""
from fastapi import WebSocket
from typing import List, Dict, Set
import json
import asyncio


class WebSocketManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all subscriptions
        for channel in self.subscriptions.values():
            channel.discard(websocket)
        
        print(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe WebSocket to a channel"""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(websocket)
        
        await websocket.send_json({
            "type": "subscribed",
            "channel": channel
        })
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to specific channel"""
        if channel not in self.subscriptions:
            return
        
        disconnected = []
        for connection in self.subscriptions[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to channel: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending to client: {e}")
            self.disconnect(websocket)


# Global instance
websocket_manager = WebSocketManager()


# Event types for broadcasting
class WebSocketEvents:
    """WebSocket event types"""
    
    @staticmethod
    def object_created(object_id: str, obj_type: str, title: str):
        return {
            "type": "object.created",
            "data": {
                "object_id": object_id,
                "type": obj_type,
                "title": title
            }
        }
    
    @staticmethod
    def object_updated(object_id: str, changes: List[str]):
        return {
            "type": "object.updated",
            "data": {
                "object_id": object_id,
                "changes": changes
            }
        }
    
    @staticmethod
    def object_deleted(object_id: str):
        return {
            "type": "object.deleted",
            "data": {"object_id": object_id}
        }
    
    @staticmethod
    def block_created(block_id: str, object_id: str):
        return {
            "type": "block.created",
            "data": {
                "block_id": block_id,
                "object_id": object_id
            }
        }
    
    @staticmethod
    def block_updated(block_id: str, content: str = None):
        return {
            "type": "block.updated",
            "data": {
                "block_id": block_id,
                "content": content
            }
        }
    
    @staticmethod
    def task_assigned(task_id: str, agent_name: str, priority: str, assignment_type: str = "direct"):
        return {
            "type": "task.assigned",
            "data": {
                "task_id": task_id,
                "agent_name": agent_name,
                "priority": priority,
                "assignment_type": assignment_type
            }
        }
    
    @staticmethod
    def task_status_changed(task_id: str, old_status: str, new_status: str, 
                            agent_name: str, current_action: str = None):
        return {
            "type": "task.status_changed",
            "data": {
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status,
                "agent_name": agent_name,
                "current_action": current_action
            }
        }
    
    @staticmethod
    def task_progress_update(task_id: str, agent_name: str, update: str):
        return {
            "type": "task.progress_update",
            "data": {
                "task_id": task_id,
                "agent_name": agent_name,
                "update": update,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def task_completed(task_id: str, agent_name: str, notes: str = None, artifacts: List[str] = None):
        return {
            "type": "task.completed",
            "data": {
                "task_id": task_id,
                "agent_name": agent_name,
                "notes": notes,
                "artifacts_created": artifacts or []
            }
        }
    
    @staticmethod
    def agent_status_changed(agent_name: str, old_status: str, new_status: str):
        return {
            "type": "agent.status_changed",
            "data": {
                "agent_name": agent_name,
                "old_status": old_status,
                "new_status": new_status
            }
        }
    
    @staticmethod
    def agent_current_action(agent_name: str, action: str, task_id: str = None):
        return {
            "type": "agent.current_action",
            "data": {
                "agent_name": agent_name,
                "action": action,
                "task_id": task_id
            }
        }
    
    @staticmethod
    def chat_message(session_id: str, agent_name: str, message_type: str, content: str):
        return {
            "type": "chat.message",
            "data": {
                "session_id": session_id,
                "agent_name": agent_name,
                "message_type": message_type,
                "content": content,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def file_indexed(file_id: str, file_path: str, object_id: str):
        return {
            "type": "file.indexed",
            "data": {
                "file_id": file_id,
                "file_path": file_path,
                "object_id": object_id
            }
        }
    
    @staticmethod
    def pong():
        return {"type": "pong"}
