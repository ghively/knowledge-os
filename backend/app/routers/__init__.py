"""Routers package"""
from .objects import router as objects_router
from .blocks import router as blocks_router
from .tasks import router as tasks_router
from .search import router as search_router
from .agents import router as agents_router
from .chat import router as chat_router
from .files import router as files_router
from .settings import router as settings_router

__all__ = [
    'objects_router',
    'blocks_router',
    'tasks_router',
    'search_router',
    'agents_router',
    'chat_router',
    'files_router',
    'settings_router',
]
