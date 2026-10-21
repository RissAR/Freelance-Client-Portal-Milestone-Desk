"""Contextual Inline keyboards for client, guest, and admin flows."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from src.core.config import settings
from src.models import Project


def get_client_project_inline_keyboard(project: Project) -> InlineKeyboardMarkup:
    """Generates client dashboard inline keyboard with active project links."""
    web_app_url = settings.WEBAPP_URL.rstrip("/") + "/app"
    admin_contact_url = f"https://t.me/{settings.ADMIN_USERNAME}" if settings.ADMIN_USERNAME else "https://t.me"

    keyboard_rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="Відкрити кабінет проекту",
                web_app=WebAppInfo(url=web_app_url),
            )
        ]
    ]

    # Quick links row (Staging & Figma) if configured
    quick_links: list[InlineKeyboardButton] = []
    if project.staging_url:
        quick_links.append(
            InlineKeyboardButton(
                text="Тестовий стенд",
                url=project.staging_url,
            )
        )
    if project.figma_url:
        quick_links.append(
            InlineKeyboardButton(
                text="Figma",
                url=project.figma_url,
            )
        )
    if quick_links:
        keyboard_rows.append(quick_links)

    # Service row
    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="Детальний статус",
                callback_data="client_detailed_status",
            ),
            InlineKeyboardButton(
                text="Написати розробнику",
                url=admin_contact_url,
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


def get_guest_inline_keyboard() -> InlineKeyboardMarkup:
    """Generates guest/portfolio visitor keyboard with demo cabinet and FAQ."""
    demo_url = settings.WEBAPP_URL.rstrip("/") + "/app?demo=true"
    admin_contact_url = f"https://t.me/{settings.ADMIN_USERNAME}" if settings.ADMIN_USERNAME else "https://t.me"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити демо-кабінет",
                    web_app=WebAppInfo(url=demo_url),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Обговорити проект / Замовити",
                    url=admin_contact_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Як це працює",
                    callback_data="guest_faq_how_it_works",
                ),
                InlineKeyboardButton(
                    text="Чому не Trello/Jira?",
                    callback_data="guest_faq_advantages",
                ),
            ],
        ]
    )


def get_admin_dashboard_inline_keyboard(m_count: int = 0, t_count: int = 0) -> InlineKeyboardMarkup:
    """Generates administrative dashboard inline keyboard."""
    web_app_url = settings.WEBAPP_URL.rstrip("/") + "/app"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити адмін-кабінет",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Очікують підтвердження ({m_count})",
                    callback_data="admin_waiting_milestones",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Відкриті тікети ({t_count})",
                    callback_data="admin_open_tickets",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Список проектів",
                    callback_data="admin_all_projects",
                ),
                InlineKeyboardButton(
                    text="Оновити",
                    callback_data="admin_refresh_dashboard",
                ),
            ],
        ]
    )


def get_remind_client_inline_keyboard(milestone_id: int) -> InlineKeyboardMarkup:
    """Generates inline button for sending a reminder to client about milestone."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Нагадати клієнту",
                    callback_data=f"admin_remind_client:{milestone_id}",
                )
            ]
        ]
    )


def get_admin_back_inline_keyboard() -> InlineKeyboardMarkup:
    """Generates back button returning to the main admin dashboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад до панелі",
                    callback_data="admin_refresh_dashboard",
                )
            ]
        ]
    )
