"""Pydantic schemas for Ticket entity."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.enums import TicketStatus, TicketType


class TicketCreateIn(BaseModel):
    """Payload for creating a revision, bug, or question ticket."""

    milestone_id: int | None = Field(default=None, description="Optional milestone link")
    type: TicketType = Field(default=TicketType.REVISION, description="Ticket type")
    message: str = Field(..., min_length=3, max_length=5000, description="Ticket details")
    attachment_url: str | None = Field(default=None, max_length=512)

    @field_validator("attachment_url")
    @classmethod
    def validate_attachment_url(cls, v: str | None) -> str | None:
        if v is not None and v.strip() != "":
            v = v.strip()
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("attachment_url must start with http:// or https://")
        return v


class TicketUpdateStatusIn(BaseModel):
    """Payload for admin ticket status transition."""

    status: TicketStatus


class TicketOut(BaseModel):
    """Public ticket response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    milestone_id: int | None = None
    type: TicketType
    status: TicketStatus
    message: str
    attachment_url: str | None = None
    created_at: datetime
