"""Bot handlers module package."""

from src.bot.handlers.admin_handlers import router as admin_router
from src.bot.handlers.client_handlers import router as client_router

__all__ = ["admin_router", "client_router"]
