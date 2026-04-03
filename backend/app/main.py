"""Knowledge OS - FastAPI Backend"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.config import settings
from app.database.qdrant_client import qdrant_manager
from app.database.sqlite import sqlite_manager
from app.services.websocket_manager import websocket_manager
from app.services.file_watcher import file_watcher_service
from app.services.backup import backup_service
from app.services.openclaw import openclaw_service
from app.routers import objects, blocks, tasks, search, agents, chat, files, settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 Starting Knowledge OS Backend...")
    
    # Initialize databases
    await qdrant_manager.initialize()
    await sqlite_manager.initialize()
    
    # Start background services
    await file_watcher_service.start()
    await backup_service.start()
    
    # Test OpenClaw connection
    if settings.openclaw_enabled:
        connected = await openclaw_service.test_connection()
        if connected:
            print("✅ OpenClaw gateway connected")
        else:
            print("⚠️ OpenClaw gateway not available")
    
    print(f"✅ Knowledge OS running on http://{settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await file_watcher_service.stop()
    await backup_service.stop()
    await qdrant_manager.close()
    await sqlite_manager.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(objects.router, prefix="/api/objects", tags=["objects"])
app.include_router(blocks.router, prefix="/api/blocks", tags=["blocks"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe":
                # Client subscribing to specific events
                channel = data.get("channel")
                await websocket_manager.subscribe(websocket, channel)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        ws_ping_interval=20,
        ws_ping_timeout=20
    )
