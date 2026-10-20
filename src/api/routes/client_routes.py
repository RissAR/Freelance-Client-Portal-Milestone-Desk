"""Client-facing API endpoints for projects, milestone approvals, and tickets."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import require_client
from src.api.routes.app_routes import apply_anti_cache_headers
from src.bot.bot import get_bot
from src.core.database import get_db
from src.models import Milestone, MilestoneStatus, Project, ProjectStatus, Ticket, TicketStatus, User
from src.schemas import MilestoneApproveIn, MilestoneOut, ProjectDetailOut, TicketCreateIn, TicketOut
from src.services.make_dispatcher import send_make_event
from src.services.notification_service import (
    notify_admin_milestone_approved,
    notify_admin_ticket_created,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client", tags=["client"])


@router.get("/projects/active", response_model=ProjectDetailOut)
async def get_active_project(
    response: Response,
    current_user: Annotated[User, Depends(require_client)],
    db: AsyncSession = Depends(get_db),
) -> ProjectDetailOut:
    """Returns current active project for the authenticated client with progress and milestones."""
    apply_anti_cache_headers(response)

    stmt = (
        select(Project)
        .where(
            Project.client_id == current_user.id,
            Project.status == ProjectStatus.ACTIVE,
        )
        .options(
            selectinload(Project.milestones),
            selectinload(Project.tickets),
        )
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active project found for this client",
        )

    milestones = project.milestones
    total_milestones = len(milestones)
    approved_count = sum(1 for m in milestones if m.status == MilestoneStatus.APPROVED)
    progress_percentage = (
        round((approved_count / total_milestones) * 100, 1)
        if total_milestones > 0
        else 0.0
    )

    return ProjectDetailOut(
        id=project.id,
        title=project.title,
        client_id=project.client_id,
        status=project.status,
        budget=project.budget,
        currency=project.currency,
        staging_url=project.staging_url,
        figma_url=project.figma_url,
        progress_percentage=progress_percentage,
        milestones=milestones,
        tickets=project.tickets,
        created_at=project.created_at,
    )


@router.post("/milestones/{milestone_id}/approve", response_model=MilestoneOut)
async def approve_milestone(
    milestone_id: int,
    payload: MilestoneApproveIn,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_client)],
    db: AsyncSession = Depends(get_db),
) -> Milestone:
    """Client approves milestone with digital canvas signature.

    Includes race-condition protection (409 Conflict if already approved),
    unlocks the subsequent locked milestone, and triggers Telegram and Make.com notifications.
    """
    stmt = (
        select(Milestone)
        .join(Project, Milestone.project_id == Project.id)
        .where(
            Milestone.id == milestone_id,
            Project.client_id == current_user.id,
        )
        .options(selectinload(Milestone.project))
    )
    result = await db.execute(stmt)
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found or does not belong to your project",
        )

    # 1. Race condition check
    if milestone.status == MilestoneStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Milestone is already approved",
        )

    # 2. Update milestone status and signature
    milestone.status = MilestoneStatus.APPROVED
    milestone.signature_data = payload.signature_data

    # 3. Auto-advance next locked milestone to IN_PROGRESS
    next_stmt = (
        select(Milestone)
        .where(
            Milestone.project_id == milestone.project_id,
            Milestone.order_index > milestone.order_index,
            Milestone.status == MilestoneStatus.LOCKED,
        )
        .order_by(Milestone.order_index.asc())
    )
    next_milestone = (await db.execute(next_stmt)).scalars().first()
    if next_milestone:
        next_milestone.status = MilestoneStatus.IN_PROGRESS
        logger.info(
            "Auto-advanced milestone #%d (id=%d) to IN_PROGRESS",
            next_milestone.order_index,
            next_milestone.id,
        )

    await db.commit()
    await db.refresh(milestone)

    # 4. Trigger Make.com webhook via BackgroundTasks
    background_tasks.add_task(
        send_make_event,
        event_name="milestone_approved",
        payload={
            "project_id": milestone.project_id,
            "project_title": milestone.project.title,
            "milestone_id": milestone.id,
            "milestone_title": milestone.title,
            "amount": milestone.amount,
            "client_name": current_user.full_name,
            "signature_data": milestone.signature_data,
        },
    )

    # 5. Trigger Telegram admin notification via BackgroundTasks
    bot = get_bot()
    background_tasks.add_task(
        notify_admin_milestone_approved,
        bot=bot,
        milestone_id=milestone.id,
        milestone_title=milestone.title,
        amount=milestone.amount,
        currency=milestone.project.currency,
        project_title=milestone.project.title,
        client_name=current_user.full_name,
        next_milestone_id=next_milestone.id if next_milestone else None,
    )

    return milestone


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreateIn,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_client)],
    db: AsyncSession = Depends(get_db),
) -> Ticket:
    """Creates a new client ticket (revision/bug/question) linked to active project."""
    # Find client's active project
    p_stmt = select(Project).where(
        Project.client_id == current_user.id,
        Project.status == ProjectStatus.ACTIVE,
    )
    project = (await db.execute(p_stmt)).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active project found for this client",
        )

    if payload.milestone_id is not None:
        m_stmt = select(Milestone).where(
            Milestone.id == payload.milestone_id,
            Milestone.project_id == project.id,
        )
        milestone = (await db.execute(m_stmt)).scalar_one_or_none()
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified milestone does not belong to active project",
            )

    ticket = Ticket(
        project_id=project.id,
        milestone_id=payload.milestone_id,
        type=payload.type,
        status=TicketStatus.OPEN,
        message=payload.message,
        attachment_url=payload.attachment_url,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    # Trigger Make.com webhook in background
    background_tasks.add_task(
        send_make_event,
        event_name="ticket_created",
        payload={
            "ticket_id": ticket.id,
            "project_title": project.title,
            "type": ticket.type.value,
            "message": ticket.message,
            "attachment_url": ticket.attachment_url,
            "client_name": current_user.full_name,
        },
    )

    # Trigger Telegram admin notification in background
    bot = get_bot()
    background_tasks.add_task(
        notify_admin_ticket_created,
        bot=bot,
        ticket_id=ticket.id,
        ticket_type=ticket.type.value,
        message_text=ticket.message,
        project_title=project.title,
        client_name=current_user.full_name,
        attachment_url=ticket.attachment_url,
    )

    return ticket
