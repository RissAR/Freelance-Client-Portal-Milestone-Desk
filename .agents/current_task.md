# Технічне завдання: Freelance Client Portal & Milestone Desk (Фаза 0 та Фаза 1)

## 1. Загальний контекст
Створення комерційного Telegram Mini App + Telegram Bot для фрілансерів/діджитал-агенцій: "Client Portal & Milestone Desk".
Клієнти мають особистий кабінет у Telegram, де бачать живий таймлайн проекту, затверджують етапи через цифровий підпис на Canvas, залишають структурований фідбек (тікети/баги), а ключові події через вебхуки запускають сценарії в Make.com (генерація PDF актів, сповіщення в боті, синхронізація з Linear/Trello).

---

## 2. Цільові файли для створення/модифікації
- `docker-compose.yaml` (FastAPI backend + bot + volume mounts)
- `Dockerfile` (мультистейдж для Python бекенду)
- `requirements.txt` (FastAPI, uvicorn, aiogram 3.x, sqlalchemy, aiosqlite, pydantic, pydantic-settings, httpx)
- `src/core/config.py` (налаштування через pydantic-settings, змінні середовища, BOT_TOKEN, WEBAPP_URL)
- `src/core/database.py` (Async SQLAlchemy engine, session maker, увімкнення SQLite WAL-режиму)
- `src/models/`
  - `src/models/user.py` (User: telegram_id, role [CLIENT, ADMIN], full_name, username)
  - `src/models/project.py` (Project: title, client_id, status, budget, currency, staging_url, figma_url)
  - `src/models/milestone.py` (Milestone: project_id, order_index, title, description, amount, status, signature_data, due_date)
  - `src/models/ticket.py` (Ticket: project_id, milestone_id, type [BUG, REVISION, QUESTION], status, message, attachment_url)
- `src/api/routes/app_routes.py` (Роути з anti-cache заголовками no-cache, no-store для TMA)
- `src/scripts/seed_initial_data.py` (Сід-скрипт із реалістичним проектом, готовим для тестування)
- `main.py` (Точка входу: паралельний запуск FastAPI та aiogram бота через asyncio.gather)

---

## 3. Детальні кроки виконання

### Крок 0: Каркас проекту та Anti-Cache фундамент
1. Організувати структуру директорій:
   ```
   /data              # Для SQLite бази даних
   /backups           # Для резервних копій
   /src               # Бекенд (FastAPI + aiogram)
     /api             # Роутери та залежності
     /core            # Конфігурація, база даних
     /models          # Моделі SQLAlchemy
     /schemas         # Pydantic-схеми
     /services        # Бізнес-логіка та Make Dispatcher
     /bot             # Хендлери бота aiogram
     /scripts         # Сід-скрипти
   /frontend          # Mini App (буде створено у Фазі 4)
   /make_blueprints   # Експорти сценаріїв Make
   ```
2. У `src/api/routes/app_routes.py` реалізувати роут роздачі веб-додатка з суворими заголовками:
   - `Cache-Control: no-cache, no-store, must-revalidate`
   - `Pragma: no-cache`
   - `Expires: 0`
   - Версіонування статики через `v=1.0.0` у конфігурації.

### Крок 1: База даних та FSM етапів робіт
1. Налаштувати SQLite з асинхронним драйвером `aiosqlite` та обов'язковим виконанням `PRAGMA journal_mode=WAL;` та `PRAGMA foreign_keys=ON;` при підключенні.
2. Реалізувати моделі SQLAlchemy 2.0 (з `Mapped` та `mapped_column`):
   - **Enums:**
     - `UserRole`: `CLIENT`, `ADMIN`
     - `ProjectStatus`: `ACTIVE`, `PAUSED`, `COMPLETED`
     - `MilestoneStatus`: `LOCKED`, `IN_PROGRESS`, `WAITING_APPROVAL`, `APPROVED`
     - `TicketType`: `BUG`, `REVISION`, `QUESTION`
     - `TicketStatus`: `OPEN`, `IN_REVIEW`, `RESOLVED`
   - **Індекси:**
     - `users.telegram_id` (Unique)
     - `(milestones.project_id, milestones.order_index)` (Composite index)
3. Створити `src/scripts/seed_initial_data.py`:
   - Створює адміністратора (фрілансера) та клієнта.
   - Створює тестовий комерційний проект: *"Розробка E-commerce Mini App"* (\$2,500).
   - Створює 3 етапи:
     - Етап 1: *"UX/UI дизайн та архітектура"* (\$750, статус `APPROVED`, з тестовим хешем підпису).
     - Етап 2: *"Розробка Frontend та Telegram SDK"* (\$1,000, статус `WAITING_APPROVAL`, готовий для тестування затвердження).
     - Етап 3: *"Інтеграція Make, генерація PDF та реліз"* (\$750, статус `LOCKED`).
   - Створює 1 відкритий тікет/правку у 2-му етапі.

### Крок 2: Перевірка працездатності
1. Запустити ініціалізацію бази даних та виконати `seed_initial_data.py`.
2. Переконатися, що база в `/data/app.db` створюється без помилок і містить коректні зв'язки.

---

## 4. Критерії готовності (Definition of Done)
1. Усі вказані файли створені з дотриманням типізації та асинхронності.
2. Немає циклічних імпортів між моделями та конфігами.
3. Сід-скрипт успішно запускається консольною командою `python -m src.scripts.seed_initial_data` і створює всі тестові сутності в SQLite WAL базі.
4. Звіт містить список файлів та єдину команду git commit.
