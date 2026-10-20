"""Seed script creating realistic commercial project data for testing."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.core.config import settings
from src.core.database import async_session_factory, init_db
from src.models import (
    Milestone,
    MilestoneStatus,
    Project,
    ProjectStatus,
    Ticket,
    TicketStatus,
    TicketType,
    User,
    UserRole,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def seed_data() -> None:
    """Seeds database with admin, client, commercial project, milestones, and ticket."""
    logger.info("Initializing database tables...")
    await init_db()

    admin_telegram_id = settings.ADMIN_TELEGRAM_ID or 8607080614
    admin_username = settings.ADMIN_USERNAME or "freelance_lead"

    async with async_session_factory() as session:
        # Check if project already exists to ensure idempotency
        stmt = select(Project).where(Project.title == "Розробка E-commerce Mini App")
        existing_project = (await session.execute(stmt)).scalar_one_or_none()

        if existing_project:
            logger.info("Test project already exists. Ensuring admin role is aligned...")
            # Check if user with admin_telegram_id already exists
            user_by_tg = (
                await session.execute(select(User).where(User.telegram_id == admin_telegram_id))
            ).scalar_one_or_none()
            if user_by_tg:
                user_by_tg.role = UserRole.ADMIN
                if admin_username:
                    user_by_tg.username = admin_username
                await session.commit()
                logger.info("Aligned existing user %d to ADMIN role", admin_telegram_id)
            else:
                existing_admin = (
                    await session.execute(select(User).where(User.role == UserRole.ADMIN))
                ).scalar_one_or_none()
                if existing_admin:
                    existing_admin.telegram_id = admin_telegram_id
                    if admin_username:
                        existing_admin.username = admin_username
                    await session.commit()
                    logger.info("Updated admin record telegram_id to %d", admin_telegram_id)
            return

        logger.info("Seeding users...")
        admin = User(
            telegram_id=admin_telegram_id,
            role=UserRole.ADMIN,
            full_name="Freelance Lead (Admin)",
            username=admin_username,
        )
        client = User(
            telegram_id=222222222,
            role=UserRole.CLIENT,
            full_name="Alex Client",
            username="alex_client",
        )
        session.add_all([admin, client])
        await session.flush()

        logger.info("Seeding project 'Розробка E-commerce Mini App' ($2,500)...")
        project = Project(
            title="Розробка E-commerce Mini App",
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
            budget=2500.0,
            currency="USD",
            staging_url="https://staging.clientportal.dev",
            figma_url="https://figma.com/file/sample-ecommerce-design",
        )
        session.add(project)
        await session.flush()

        logger.info("Seeding 3 milestones...")
        now = datetime.now(timezone.utc)
        test_signature_data = (
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWAQMAAABFqHqAAAAABlBMVEUAAAD"
            "///+l2Z/dAAAAAXRSTlMAQObYZgAAADRJREFUeN7twTEBAAAAwqD1T20LL6AAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAeDE0AAAB42398AAAAABJRU5ErkJggg=="
        )

        milestone1 = Milestone(
            project_id=project.id,
            order_index=1,
            title="UX/UI дизайн та архітектура",
            description="Розробка вайрфреймів, дизайн-системи Figma та структури бази даних.",
            amount=750.0,
            status=MilestoneStatus.APPROVED,
            signature_data=test_signature_data,
            due_date=now - timedelta(days=5),
        )

        milestone2 = Milestone(
            project_id=project.id,
            order_index=2,
            title="Розробка Frontend та Telegram SDK",
            description="Інтеграція Telegram WebApp SDK, каталог товарів, кошик та Canvas цифровий підпис.",
            amount=1000.0,
            status=MilestoneStatus.WAITING_APPROVAL,
            signature_data=None,
            due_date=now + timedelta(days=7),
        )

        milestone3 = Milestone(
            project_id=project.id,
            order_index=3,
            title="Інтеграція Make, генерація PDF та реліз",
            description="Вебхуки Make.com, формування PDF актів виконаних робіт, сповіщення та реліз у прод.",
            amount=750.0,
            status=MilestoneStatus.LOCKED,
            signature_data=None,
            due_date=now + timedelta(days=21),
        )

        session.add_all([milestone1, milestone2, milestone3])
        await session.flush()

        logger.info("Seeding open ticket for milestone 2...")
        ticket = Ticket(
            project_id=project.id,
            milestone_id=milestone2.id,
            type=TicketType.REVISION,
            status=TicketStatus.OPEN,
            message="Потрібно збільшити розмір поля підпису на мобільних пристроях з малою діагоналлю.",
            attachment_url="https://cdn.clientportal.dev/attachments/ticket-mobile-view.png",
        )
        session.add(ticket)

        await session.commit()
        logger.info("Data seeding completed successfully!")


def main() -> None:
    """Entrypoint for seed script."""
    asyncio.run(seed_data())


if __name__ == "__main__":
    main()
