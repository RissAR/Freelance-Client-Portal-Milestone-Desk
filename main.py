"""Application entrypoint: parallel execution of FastAPI and aiogram bot via asyncio.gather."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from aiogram.exceptions import TelegramUnauthorizedError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.admin_routes import router as admin_router
from src.api.routes.app_routes import router as app_router
from src.api.routes.client_routes import router as client_router
from src.bot.bot import create_bot_and_dispatcher
from src.core.config import settings
from src.core.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for database initialization and cleanup."""
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title="Client Portal & Milestone Desk API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Enable CORS for Telegram Web App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include application routers
app.include_router(app_router)
app.include_router(client_router)
app.include_router(admin_router)


async def run_bot() -> None:
    """Runs aiogram bot polling if a valid BOT_TOKEN is configured."""
    token = settings.BOT_TOKEN.strip()
    if not token or token in ("dummy_token", "your_bot_token_here"):
        logger.warning(
            "BOT_TOKEN is not configured. Telegram bot polling disabled. "
            "Set BOT_TOKEN in .env to enable polling."
        )
        while True:
            await asyncio.sleep(3600)

    logger.info("Starting Telegram bot polling...")
    bot, dp = create_bot_and_dispatcher()
    try:
        await dp.start_polling(bot)
    except TelegramUnauthorizedError:
        logger.error(
            "Telegram Unauthorized: Provided BOT_TOKEN is invalid. "
            "Bot polling stopped, FastAPI server will continue running."
        )
        while True:
            await asyncio.sleep(3600)
    finally:
        await bot.session.close()


async def run_server() -> None:
    """Runs Uvicorn web server."""
    config = uvicorn.Config(
        app=app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info" if not settings.DEBUG else "debug",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    """Launches FastAPI backend and aiogram bot concurrently."""
    logger.info("Starting application on %s:%d...", settings.HOST, settings.PORT)
    await asyncio.gather(
        run_server(),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
