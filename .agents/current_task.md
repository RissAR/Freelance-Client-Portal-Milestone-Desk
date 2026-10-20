# Технічне завдання: Безпечний REST API, initData Криптографія, RBAC, Race Condition Lock & Make Dispatcher (Фаза 2)

## 1. Загальний контекст
У Фазах 0 та 1 було створено каркас, SQLite WAL базу даних, SQLAlchemy моделі та сід-скрипт.
Мета Фази 2 — створити безпечний, надійний REST API для клієнтського порталу Telegram Mini App (TMA).
Головні вимоги: криптографічна валідація Telegram `initData` (HMAC-SHA256), рольовий доступ (RBAC: Client vs Admin), захист від гонки станів при підписанні етапів (Race Condition / Idempotency), і фоновий неблокуючий диспетчер вебхуків у Make.com.

---

## 2. КРИТИЧНЕ ПРАВИЛО БЕЗПЕКИ (Zero Secrets Leak)
- **ЖОДНИХ реальних токенів у коді або репозиторії!**
- У `src/core/config.py` дефолтні значення для `BOT_TOKEN` та `MAKE_WEBHOOK_URL` мають бути суворо порожніми рядками `""`.
- Усі значення читаються тільки з файлу `.env` (який додано до `.gitignore`).
- Оновити `.env.example` плейсхолдерами:
  ```env
  BOT_TOKEN=
  MAKE_WEBHOOK_URL=
  ```
- **Обов'язкова перевірка перед комітом:** `git status` та `git diff --cached` не повинні містити `.env` або реальних секретів.

---

## 3. Цільові файли для створення/модифікації
- `src/core/config.py` (очищення дефолтів від секретів, додавання `MAKE_WEBHOOK_URL`)
- `.env.example` (додавання плейсхолдера для `MAKE_WEBHOOK_URL`)
- `src/core/security.py` (валідація Telegram initData через HMAC-SHA256 за стандартом Telegram)
- `src/api/deps.py` (FastAPI dependencies: `get_current_user`, `require_admin`, `require_client`)
- `src/schemas/`
  - `src/schemas/user.py` (UserOut)
  - `src/schemas/milestone.py` (MilestoneOut, MilestoneApproveIn)
  - `src/schemas/project.py` (ProjectOut, ProjectDetailOut з прогресом і списком етапів)
  - `src/schemas/ticket.py` (TicketCreateIn, TicketUpdateStatusIn, TicketOut)
- `src/services/make_dispatcher.py` (асинхронний відправник подій у Make.com з graceful fallback)
- `src/api/routes/client_routes.py` (ендпоінти для клієнта: отримання проекту, підписання етапу, створення тікету)
- `src/api/routes/admin_routes.py` (ендпоінти для адміна: список проектів, зміна статусів етапів і тікетів)
- `main.py` (підключення клієнтського та адмінського роутерів)
- `src/scripts/test_phase2_api.py` (автоматизований тест-сьют для перевірки всіх ендпоінтів та безпеки)

---

## 4. Детальні вимоги до реалізації

### 4.1. Криптографія initData (`src/core/security.py`)
- Функція `validate_telegram_init_data(init_data: str, bot_token: str) -> dict`:
  1. Парсить query string у ключ-значення.
  2. Витягує `hash`.
  3. Сортує всі інші ключі за алфавітом і об'єднує у формат `key=value\n`.
  4. Обчислює `secret_key = HMAC_SHA256(b"WebAppData", bot_token.encode())`.
  5. Обчислює `calculated_hash = HMAC_SHA256(secret_key, data_check_string.encode()).hexdigest()`.
  6. Перевіряє через `hmac.compare_digest(calculated_hash, received_hash)`.
  7. Якщо `settings.DEBUG == True` та передано dev-mock заголовки (наприклад, `mock_client` або `mock_admin`), дозволяти безпечний байпас для локальної розробки без живого бота.
  8. Повертає словник розпарсених даних користувача (id, username, first_name, тощо).

### 4.2. Рольова модель RBAC (`src/api/deps.py`)
- Заголовок `X-Telegram-Init-Data` перевіряється в `get_current_user`:
  - Знаходить або створює користувача в базі даних.
- `require_admin`: якщо `user.role != UserRole.ADMIN` $\to$ `HTTPException(403, "Access denied: Admins only")`.
- `require_client`: якщо `user.role != UserRole.CLIENT` $\to$ `HTTPException(403, "Access denied: Clients only")`.

### 4.3. Make Webhook Dispatcher (`src/services/make_dispatcher.py`)
- Метод `send_make_event(event_name: str, payload: dict)`:
  - Працює через `httpx.AsyncClient`.
  - Якщо `settings.MAKE_WEBHOOK_URL` не вказано або порожній $\to$ логує `WARNING` і завершує роботу без викидання помилки (щоб API не падало без налаштованого Make).
  - Події для відправки:
    - `"milestone_approved"`: містить `project_id`, `project_title`, `milestone_id`, `milestone_title`, `amount`, `client_name`, `signature_data`.
    - `"ticket_created"`: містить `ticket_id`, `project_title`, `type`, `message`, `attachment_url`, `client_name`.

### 4.4. Клієнтські ендпоінти (`src/api/routes/client_routes.py`)
- `GET /api/client/projects/active`:
  - Повертає активний проект поточного клієнта (`ProjectDetailOut`):
  - Розраховує `progress_percentage` (кількість `APPROVED` етапів / загальна кількість * 100).
  - Включає список усіх етапів та відкритих тікетів.
- `POST /api/client/milestones/{milestone_id}/approve`:
  - Приймає `MilestoneApproveIn` (`signature_data: str`, `device_info: Optional[dict]`).
  - Перевіряє, що етап належить проекту клієнта.
  - **Захист від повторного підписання (Race condition):**
    - Якщо статус уже `APPROVED` $\to$ повертає `409 Conflict` ("Milestone is already approved").
  - Встановлює статус `APPROVED`, зберігає `signature_data`.
  - **Авто-перехід наступного етапу:** знаходить наступний етап за `order_index` зі статусом `LOCKED` і переводить його в `IN_PROGRESS`.
  - Запускає `send_make_event` через `BackgroundTasks`.
- `POST /api/client/tickets`:
  - Приймає `TicketCreateIn` (`milestone_id`, `type`, `message`, `attachment_url`).
  - Створює запис `Ticket` зі статусом `OPEN`.
  - Запускає `send_make_event` через `BackgroundTasks`.

### 4.5. Адмінські ендпоінти (`src/api/routes/admin_routes.py`)
- `GET /api/admin/projects`: список усіх проектів у системі.
- `PATCH /api/admin/milestones/{milestone_id}/status`: примусова зміна статусу етапу адміном.
- `PATCH /api/admin/tickets/{ticket_id}/status`: зміна статусу тікету (`OPEN` $\to$ `IN_REVIEW` $\to$ `RESOLVED`).

### 4.6. Автотест (`src/scripts/test_phase2_api.py`)
- Запуск: `python -m src.scripts.test_phase2_api`
- Перевіряє:
  1. Відхилення невалідного `initData` (401 Unauthorized).
  2. Успішну автентифікацію через валідні дані.
  3. Отримання активного проекту клієнта.
  4. Підписання етапу №2 (`WAITING_APPROVAL` $\to$ `APPROVED`), розблокування етапу №3 (`LOCKED` $\to$ `IN_PROGRESS`).
  5. Повторне підписання етапу №2 $\to$ перевірка отримання `409 Conflict`.
  6. Створення тікету.
  7. Роботу Make Dispatcher у фоновому режимі без помилок.

---

## 5. Критерії готовності (Definition of Done)
1. Усі нові роутери підключено в `main.py` під відповідними префіксами.
2. Жодних захардкоджених секретів (перевірено через `git status` та `git diff --cached`).
3. Тест `python -m src.scripts.test_phase2_api` проходить на 100% без збоїв.
4. Надано звіт та фінальну команду git commit.
