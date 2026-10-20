"""Pydantic schemas for Project entity."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.models.enums import ProjectStatus
from src.schemas.milestone import MilestoneOut
from src.schemas.ticket import TicketOut


class ProjectOut(BaseModel):
    """Basic project summary schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    client_id: int
    status: ProjectStatus
    budget: float
    currency: str
    staging_url: str | None = None
    figma_url: str | None = None
    created_at: datetime


class ProjectDetailOut(BaseModel):
    """Detailed project schema with computed progress, milestones, and tickets."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    client_id: int
    status: ProjectStatus
    budget: float
    currency: str
    staging_url: str | None = None
    figma_url: str | None = None
    progress_percentage: float
    milestones: list[MilestoneOut]
    tickets: list[TicketOut]
    created_at: datetime
