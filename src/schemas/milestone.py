"""Pydantic schemas for Milestone entity."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import MilestoneStatus


class MilestoneOut(BaseModel):
    """Public milestone response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    order_index: int
    title: str
    description: str | None = None
    amount: float
    status: MilestoneStatus
    signature_data: str | None = None
    due_date: datetime | None = None
    created_at: datetime


class MilestoneApproveIn(BaseModel):
    """Input payload for client milestone approval via digital signature."""

    signature_data: str = Field(
        ...,
        description="Canvas signature base64 data URL or hash string",
        min_length=10,
    )
    device_info: dict[str, Any] | None = Field(
        default=None,
        description="Optional client telemetry/device metadata",
    )


class MilestoneStatusUpdateIn(BaseModel):
    """Input payload for admin status update."""

    status: MilestoneStatus
