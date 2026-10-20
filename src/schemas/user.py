"""Pydantic schemas for User entity."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.models.enums import UserRole


class UserOut(BaseModel):
    """Public user response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    role: UserRole
    full_name: str
    username: str | None = None
    created_at: datetime
