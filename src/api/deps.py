"""Authentication and RBAC dependencies for FastAPI routes."""

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.security import validate_telegram_init_data
from src.models import User, UserRole

logger = logging.getLogger(__name__)


async def get_current_user(
    x_telegram_init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticates request using Telegram WebApp initData header.

    Finds existing user or registers a new user with proper RBAC role assignment
    based on settings.ADMIN_TELEGRAM_ID.
    """
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Telegram-Init-Data header",
        )

    try:
        user_info = validate_telegram_init_data(x_telegram_init_data)
    except ValueError as exc:
        logger.warning("Telegram initData validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {exc}",
        ) from exc

    telegram_id = user_info["telegram_id"]
    is_admin = settings.ADMIN_TELEGRAM_ID is not None and telegram_id == settings.ADMIN_TELEGRAM_ID
    target_role = UserRole.ADMIN if is_admin else UserRole.CLIENT

    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Register new user with designated role
        user = User(
            telegram_id=telegram_id,
            role=target_role,
            full_name=user_info["full_name"],
            username=user_info.get("username"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Created new user id=%d (tg_id=%d, role=%s)", user.id, telegram_id, user.role)
    else:
        # Keep profile updated if name, username or admin role changed
        updated = False
        if is_admin and user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            updated = True
        if user.full_name != user_info["full_name"]:
            user.full_name = user_info["full_name"]
            updated = True
        if user_info.get("username") and user.username != user_info["username"]:
            user.username = user_info["username"]
            updated = True
        if updated:
            await db.commit()
            await db.refresh(user)

    return user


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency verifying that authenticated user has ADMIN role."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admins only",
        )
    return user


async def require_client(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency verifying that authenticated user has CLIENT role."""
    if user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Clients only",
        )
    return user
