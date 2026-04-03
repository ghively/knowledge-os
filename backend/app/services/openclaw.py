"""OpenClaw Gateway Integration Service"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.config import settings
from app.services.websocket_manager import websocket_manager, WebSocketEvents


class OpenClawService:
    """Service for interacting with OpenClaw Gateway"""
    
    def __init__(self):
        self.base_url = settings.openclaw_gateway_url
        self.token = settings.openclaw_gateway_token
        self.enabled = settings.openclaw_enabled
        self.client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize HTTP client"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=60.0
        )
    
    async def test_connection(self) -> bool:
        """Test connection to OpenClaw Gateway"""
        if not self.enabled:
            return False
        
        try:
            await self.initialize()
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            print(f"OpenClaw connection failed: {e}")
            return False
    
    async def send_message(self, agent_name: str, message: str, 
                          session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to an agent via OpenClaw Gateway"""
        if not self.enabled or not self.client:
            return {"error": "OpenClaw not enabled"}
        
        try:
            payload = {
                "content": message,
                "sessionId": session_id or "main"
            }
            
            response = await self.client.post(
                "/api/sessions/main/messages",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"OpenClaw error: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"Error sending message to OpenClaw: {e}")
            return {"error": str(e)}
    
    async def assign_task(self, task_id: str, agent_name: str, 
                          context: Dict[str, Any]) -> bool:
        """Assign a task to an agent via OpenClaw Gateway"""
        if not self.enabled or not self.client:
            return False
        
        # Build task message with context
        message = self._build_task_message(task_id, agent_name, context)
        
        result = await self.send_message(agent_name, message)
        
        if "error" not in result:
            # Broadcast task assigned event
            await websocket_manager.broadcast(
                WebSocketEvents.task_assigned(
                    task_id=task_id,
                    agent_name=agent_name,
                    priority=context.get("priority", "medium"),
                    assignment_type="direct"
                )
            )
            return True
        
        return False
    
    def _build_task_message(self, task_id: str, agent_name: str, 
                           context: Dict[str, Any]) -> str:
        """Build task message with full context"""
        lines = [
            f"🎯 NEW TASK ASSIGNED",
            f"",
            f"Task: {context.get('task_title', 'Untitled')}",
            f"Priority: {context.get('priority', 'medium').upper()}",
            f"Task ID: {task_id}",
            f"",
            f"📋 DESCRIPTION:",
            context.get('task_content', 'No description provided.'),
            f"",
        ]
        
        # Parent object context
        if context.get('parent_object'):
            parent = context['parent_object']
            lines.extend([
                f"📁 PARENT CONTEXT:",
                f"Title: {parent.get('title', 'Unknown')}",
                f"Type: {parent.get('type', 'unknown')}",
                f"",
            ])
        
        # Linked objects
        if context.get('linked_objects'):
            lines.append(f"🔗 LINKED OBJECTS:")
            for obj in context['linked_objects'][:5]:  # Limit to 5
                lines.append(f"  • {obj.get('title', 'Untitled')} ({obj.get('type', 'unknown')})")
            lines.append(f"")
        
        # Related files
        if context.get('related_files'):
            lines.append(f"📎 RELATED FILES:")
            for file in context['related_files'][:5]:
                lines.append(f"  • {file.get('filename', 'Unknown')}")
            lines.append(f"")
        
        # Relevant memories
        if context.get('relevant_memories'):
            lines.append(f"🧠 YOUR RELEVANT MEMORIES:")
            for memory in context['relevant_memories'][:3]:
                lines.append(f"  • {memory.get('content', '')[:100]}...")
            lines.append(f"")
        
        # Qdrant pointers
        if context.get('qdrant_pointers'):
            lines.extend([
                f"📍 QDRANT POINTERS (query for more context):",
                f"  • Task object: {context['qdrant_pointers'].get('task_object_id')}",
                f"  • Parent object: {context['qdrant_pointers'].get('parent_object_id')}",
                f"",
            ])
        
        # Instructions
        lines.extend([
            f"📋 INSTRUCTIONS:",
            f"1. Update task status as you progress",
            f"2. Use the knowledge-os skill to update status",
            f"3. Create notes for your findings",
            f"4. Ask for clarification if needed",
            f"",
            f"Good luck! 🚀"
        ])
        
        return "\n".join(lines)
    
    async def write_to_heartbeat(self, agent_name: str, task_info: Dict[str, Any]) -> bool:
        """Write a low-priority task to agent's HEARTBEAT.md"""
        # This would require file system access to OpenClaw's workspace
        # For now, we'll just send a message indicating it's a background task
        message = f"""
📌 BACKGROUND TASK (Low Priority)

When you have free time, please work on:

Task: {task_info.get('title', 'Untitled')}
Task ID: {task_info.get('id')}

{task_info.get('content', 'No description.')}

This is a low-priority task. Work on it when you're not busy with other tasks.
"""
        result = await self.send_message(agent_name, message)
        return "error" not in result
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get agent status from OpenClaw"""
        if not self.enabled or not self.client:
            return {"status": "unknown"}
        
        try:
            response = await self.client.get(f"/api/agents/{agent_name}/status")
            if response.status_code == 200:
                return response.json()
            return {"status": "unknown"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global instance
openclaw_service = OpenClawService()
