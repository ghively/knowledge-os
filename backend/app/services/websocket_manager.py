"""WebSocket Manager - Handles real-time communication"""
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message validation model"""
    type: str
    data: dict


class WebSocketEvents:
    """WebSocket event types"""
    
    @staticmethod
    def object_created(object_id: str, object_type: str, title: str):
        return {
            "type": "object_created",
            "data": {"id": object_id, "type": object_type, "title": title}
        }
    
    @staticmethod
    def object_updated(object_id: str, changes: List[str]):
        return {
            "type": "object_updated",
            "data": {"id": object_id, "changes": changes}
        }
    
    @staticmethod
    def object_deleted(object_id: str):
        return {
            "type": "object_deleted",
            "data": {"id": object_id}
        }
    
    @staticmethod
    def block_created(block_id: str, object_id: str):
        return {
            "type": "block_created",
            "data": {"id": block_id, "object_id": object_id}
        }
    
    @staticmethod
    def block_updated(block_id: str):
        return {
            "type": "block_updated",
            "data": {"id": block_id}
        }
    
    @staticmethod
    def block_deleted(block_id: str):
        return {
            "type": "block_deleted",
            "data": {"id": block_id}
        }
    
    @staticmethod
    def task_status_changed(task_id: str, status: str, agent_name: str):
        return {
            "type": "task_status_changed",
            "data": {"id": task_id, "status": status, "agent": agent_name}
        }
    
    @staticmethod
    def agent_message(agent_name: str, content: str):
        return {
            "type": "agent_message",
            "data": {"agent": agent_name, "content": content}
        }
    
    @staticmethod
    def agent_status(agent_name: str, status: str):
        return {
            "type": "agent_status",
            "data": {"agent": agent_name, "status": status}
        }
    
    @staticmethod
    def file_indexed(file_id: str, path: str):
        return {
            "type": "file_indexed",
            "data": {"id": file_id, "path": path}
        }
    
    @staticmethod
    def file_reindexed(file_id: str, path: str):
        return {
            "type": "file_reindexed",
            "data": {"id": file_id, "path": path}
        }


class WebSocketManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)
    
    async def handle_message(self, websocket: WebSocket, data: str):
        """Handle incoming WebSocket message with validation"""
        try:
            # Parse JSON
            parsed = json.loads(data)
            
            # Validate message structure
            try:
                message = WebSocketMessage(**parsed)
            except ValidationError as e:
                logger.warning(f"Invalid message format: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid message format"}
                })
                return
            
            # Handle different message types
            if message.type == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.type == "subscribe":
                # Handle subscription
                pass
            else:
                logger.debug(f"Received message: {message.type}")
                
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON")
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Invalid JSON"}
            })
        except Exception as e:
            logger.error(f"Error handling message: {e}")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
