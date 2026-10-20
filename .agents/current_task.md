# Технічне завдання: Комплексний аудит безпеки та надійності кодової бази (Security & Code Correctness Audit)

## 1. Загальний контекст
Після реалізації бази даних (Фаза 1), REST API з RBAC (Фаза 2) та Telegram-бота зі сповіщеннями (Фаза 3) проводиться окремий позачерговий аудит безпеки.
Мета аудиту — закрити потенційні вразливості (Replay attacks, Telegram HTML Injection, IDOR, переповнення пам'яті підписом Canvas, race conditions), зміцнити валідацію вхідних даних та створити автоматичний скрипт аудиту для регулярних перевірок.

---

## 2. КРИТИЧНЕ ПРАВИЛО БЕЗПЕКИ (Zero Secrets Leak)
- **Сувора заборона на будь-які секрети чи токени в коді.**
- Навіть у тестових скриптах заборонено створювати рядки, схожі на токени (шаблон `[0-9]{8,12}:[a-zA-Z0-9_-]{30,40}`). Використовувати тільки безпечні моки (наприклад, `"mock_test_token"`).
- Перед комітом обов'язково запустити `python3 scripts/security_check.py`.

---

## 3. Цільові файли для аудиту та доопрацювання
- `src/core/security.py` (додавання перевірки `auth_date` на захист від Replay-атак)
- `src/services/notification_service.py` (екранування HTML-символів через `html.escape` для запобігання падінням aiogram)
- `src/schemas/milestone.py` (обмеження максимального розміру підпису `signature_data` до 200 КБ та валідація префіксу)
- `src/schemas/ticket.py` (валідація протоколів `http://` / `https://` для `attachment_url` проти небезпечних URI)
- `src/api/routes/client_routes.py` (перевірка обробки транзакцій та IDOR)
- `src/scripts/audit_security_and_code.py` (новий комплексний скрипт перевірки всіх 6 векторів безпеки)

---

## 4. Детальні вимоги аудиту за векторами

### Вектор 1. Захист від Replay Attacks у Telegram `initData` (`src/core/security.py`)
- **Проблема:** Перехоплений валідний `initData` може повторно використовуватися зловмисником безкінечно.
- **Вимога:**
  - Додати параметр `max_age_seconds: int = 86400` (24 години) у `validate_telegram_init_data`.
  - Отримувати `auth_date` із параметрів. Якщо `auth_date` відсутній або `current_time - auth_date > max_age_seconds` $\to$ викидати `ValueError("Telegram initData is expired (older than 24 hours)")`.
  - Якщо `auth_date > current_time + 60` (мітка з майбутнього) $\to$ викидати `ValueError("Telegram initData timestamp is in the future")`.
  - Для локальних тестів із `mock_client` чи `DEBUG=True` дозволити пропуск перевірки `auth_date`.

### Вектор 2. Захист від Telegram HTML Injection та збоїв парсера (`src/services/notification_service.py`)
- **Проблема:** Якщо клієнт напише повідомлення із символами `<`, `>`, `&` (наприклад, `"Перевірте a < b & c > d"`), aiogram впаде з помилкою `TelegramBadRequest: can't parse entities: Unexpected token` і сповіщення адміну не дійде.
- **Вимога:**
  - Імпортувати `import html` у `notification_service.py`.
  - Усі користувацькі змінні, що підставляються у повідомлення з `parse_mode="HTML"` (`project_title`, `client_name`, `message_text`, `milestone_title`), обов'язково обгортати у `html.escape()`.

### Вектор 3. Захист від переповнення пам'яті через Canvas підпис (`src/schemas/milestone.py`)
- **Проблема:** Поле `signature_data` має лише `min_length=10`. Зловмисник може надіслати 50 МБ довільного тексту і роздути пам'ять сервера або БД.
- **Вимога:**
  - Встановити суворе обмеження: `max_length=200_000` (200 КБ — з головою вистачає для стиснутого Base64 PNG підпису).
  - Додати Pydantic validator: рядок повинен починатися з `data:image/` або бути валідним хешем/base64.

### Вектор 4. Безпека URL вкладень у тікетах (`src/schemas/ticket.py`)
- **Проблема:** Поле `attachment_url` може містити небезпечні схеми на кшталт `javascript:alert(1)`.
- **Вимога:**
  - Додати валідатор, який дозволяє лише протоколи `http://` або `https://` (або `None`). Будь-які інші значення повинні повертати помилку валідації 422.

### Вектор 5. Захист від IDOR та Race Conditions
- Перевірити у `client_routes.py`:
  - Клієнт не може підписати етап іншого клієнта (повертає 404).
  - При спробі повторного підписання етапу у статусі `APPROVED` повертається суворо `409 Conflict`.
  - Автоматичне розблокування наступного етапу (`LOCKED` $\to$ `IN_PROGRESS`) відбувається в межах однієї транзакції.

### Вектор 6. Автоматичний скрипт аудиту (`src/scripts/audit_security_and_code.py`)
- Створити виконуваний тестовий скрипт, який перевіряє:
  1. **Replay Attack Test:** Спроба входу із `auth_date`, старшим за 25 годин $\to$ повертає 401 Unauthorized.
  2. **HTML Injection Test:** Відправка тікету з текстом `<b>Test</b> & <script>alert(1)</script> <fail>` $\to$ формується валідне екрановане повідомлення без помилок aiogram.
  3. **Signature Payload Limit Test:** Відправка підпису розміром 250 КБ $\to$ повертає 422 Unprocessable Entity.
  4. **Malicious URL Test:** Відправка тікету з `attachment_url="javascript:attack()"` $\to$ повертає 422.
  5. **IDOR Test:** Спроба клієнта затвердити етап із неіснуючим ID або чужого проекту $\to$ повертає 404 Not Found.
  6. **Security Scanner Run:** Виклик `scripts/security_check.py` $\to$ повертає код 0 (жодних витоків).

---

## 5. Критерії готовності (Definition of Done)
1. Усі 5 виправлень безпеки внесено до відповідних файлів.
2. Скрипт `python3 -m src.scripts.audit_security_and_code` успішно виконує всі 6 тестів на 100%.
3. `python3 scripts/security_check.py` проходить успішно.
4. Попередні тести `test_phase2_api` та `test_phase3_bot` не поламані та проходять без помилок.
5. Надано звіт та фінальну команду git commit.
