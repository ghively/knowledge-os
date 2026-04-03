"""OpenClaw Service - Integration with OpenClaw agent system"""
import logging
from typing import Optional, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OpenClawService:
    """Service for communicating with OpenClaw"""
    
    def __init__(self):
        self.base_url = settings.openclaw_url
        self.token = settings.openclaw_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def send_message(self, agent_name: str, content: str) -> Dict[str, Any]:
        """Send a message to an agent"""
        url = f"{self.base_url}/agents/{agent_name}/message"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json={"content": content},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"OpenClaw error: {response.status_code} - {response.text}")
                    return {"content": f"Error: {response.status_code}", "metadata": {}}
                    
        except Exception as e:
            logger.error(f"Error sending message to OpenClaw: {e}")
            return {"content": f"Error: {str(e)}", "metadata": {}}
    
    async def assign_task(self, agent_name: str, task_id: str, task_content: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Assign a task to an agent"""
        url = f"{self.base_url}/agents/{agent_name}/tasks"
        
        payload = {
            "task_id": task_id,
            "content": task_content,
            "context": context or {}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"OpenClaw error: {response.status_code} - {response.text}")
                    return {"status": "error", "message": f"{response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error assigning task via OpenClaw: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get agent status"""
        url = f"{self.base_url}/agents/{agent_name}/status"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"status": "unknown"}
                    
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {"status": "offline"}


# Global OpenClaw service instance
openclaw_service = OpenClawService()
