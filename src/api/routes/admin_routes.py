"""Admin-facing API endpoints for managing projects, milestones, and tickets."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import require_admin
from src.api.routes.app_routes import apply_anti_cache_headers
from src.core.database import get_db
from src.models import Milestone, MilestoneStatus, Project, Ticket, User
from src.schemas import (
    MilestoneOut,
    MilestoneStatusUpdateIn,
    ProjectDetailOut,
    TicketOut,
    TicketUpdateStatusIn,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/projects", response_model=list[ProjectDetailOut])
async def list_all_projects(
    response: Response,
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> list[ProjectDetailOut]:
    """Lists all agency projects with progress, milestones, and tickets."""
    apply_anti_cache_headers(response)

    stmt = select(Project).options(
        selectinload(Project.milestones),
        selectinload(Project.tickets),
    ).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    detail_list: list[ProjectDetailOut] = []
    for p in projects:
        total_m = len(p.milestones)
        approved_m = sum(1 for m in p.milestones if m.status == MilestoneStatus.APPROVED)
        progress = round((approved_m / total_m) * 100, 1) if total_m > 0 else 0.0

        detail_list.append(
            ProjectDetailOut(
                id=p.id,
                title=p.title,
                client_id=p.client_id,
                status=p.status,
                budget=p.budget,
                currency=p.currency,
                staging_url=p.staging_url,
                figma_url=p.figma_url,
                progress_percentage=progress,
                milestones=p.milestones,
                tickets=p.tickets,
                created_at=p.created_at,
            )
        )

    return detail_list


@router.patch("/milestones/{milestone_id}/status", response_model=MilestoneOut)
async def update_milestone_status(
    milestone_id: int,
    payload: MilestoneStatusUpdateIn,
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> Milestone:
    """Admin overrides milestone status."""
    stmt = select(Milestone).where(Milestone.id == milestone_id)
    milestone = (await db.execute(stmt)).scalar_one_or_none()

    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    milestone.status = payload.status
    await db.commit()
    await db.refresh(milestone)
    logger.info("Admin %s updated milestone %d to %s", current_user.id, milestone_id, payload.status)

    return milestone


@router.patch("/tickets/{ticket_id}/status", response_model=TicketOut)
async def update_ticket_status(
    ticket_id: int,
    payload: TicketUpdateStatusIn,
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> Ticket:
    """Admin transitions ticket status (OPEN -> IN_REVIEW -> RESOLVED)."""
    stmt = select(Ticket).where(Ticket.id == ticket_id)
    ticket = (await db.execute(stmt)).scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    ticket.status = payload.status
    await db.commit()
    await db.refresh(ticket)
    logger.info("Admin %s updated ticket %d to %s", current_user.id, ticket_id, payload.status)

    return ticket
