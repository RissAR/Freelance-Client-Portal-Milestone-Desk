# Технічне завдання: Візуальний полішинг у стилі Apple Pro / FinTech Dark — Глибина шарів (Layering), Палітра без "спалахів", Табулярні цифри та Преміум-акти

## 1. Загальний контекст
Ергономічний каркас (сегментовані таби, лінійні кнопки, дедлайни) успішно протестовано та впроваджено.
Мета цього завдання — виконати якісний візуальний полішинг інтерфейсу Telegram Mini App у стилі **Apple Pro / FinTech Dark** (орієнтир на стилістику Apple Wallet, Linear, Revolut):
1. **Усунути «ефект спалаху»:** замінити різкі суцільні білі кнопки (`+ Додати правку`, `Позначити як вирішено`) на благородний стриманий акцент **iOS System Blue / Electric Indigo** (`#0A84FF` / `#4F46E5`) та матові статусні кнопки.
2. **Створити трирівневу глибину шарів (Elevation Layering):**
   - Рівень 0 (Фон сторінки): глибокий оксамитовий чорний `#0A0A0C` (OLED-ready).
   - Рівень 1 (Картки блоків): темно-графітовий `#141418` з надтонкою напівпрозорою лінією `border border-white/[0.08]` та радіусом `rounded-2xl`.
   - Рівень 2 (Таби, інпути, чіпси): внутрішній графіт `#1C1C22` або `#22222A`.
3. **Гармонізація бейджів (Badges & Pills):** єдиний розмір (висота 22px, шрифт 10–11px, `rounded-md` або `rounded-full`), акуратні пастельні напівпрозорі фони (10% opacity) та тонкі рамки (20% opacity).
4. **Благородний прогрес-бар:** заміна білої смуги на плавний градієнт (індиго $\to$ блакитний/смарагдовий) із заокругленими краями.
5. **Фінансова типографіка:** суми (`$2,500 USD`, `$750 USD`) відображати з увімкненим `tabular-nums` для ідеального вирівнювання цифр.
6. **Оформлення «Акта робіт»:** сертифікатний вигляд з окремою рамкою для підпису на чистому світлому/контрастному полі та поміткою про цифрову верифікацію.

---

## 2. КРИТИЧНЕ ПРАВИЛО БЕЗПЕКИ ТА ДИСЦИПЛІНИ
- **Zero Secrets Leak:** Жодних токенів чи паролів у коді чи репозиторії.
- **Zero Emojis:** Суворе дотримання правила нуль емодзі. Використовувати виключно акуратні SVG-іконки `lucide-react` та чисту українську типографіку.
- **Rules of Hooks:** Усі React-хуки оголошуються суворо на самому початку функціональних компонентів.
- Перед комітом обов'язково запустити `python3 scripts/security_check.py`.

---

## 3. Цільові файли для модифікації
- `frontend/src/index.css` (базовий фон `#0A0A0C`, утиліти `tabular-nums`, плавні переходи)
- `frontend/src/App.jsx` (оновлення стилів головного контейнера, тостів та фону)
- `frontend/src/components/Header.jsx` (картка проекту: кольори `#141418`, прогрес-бар з градієнтом `from-indigo-500 to-blue-400`, чіпси Figma/Стенд)
- `frontend/src/components/SegmentedTabs.jsx` (Apple iOS таб-бар: плавний перемикач, м'яка тінь активного табу `#22222A`, делікатна крапка лічильника)
- `frontend/src/components/MilestonesTimeline.jsx` (картки етапів: оновлені кольори статусів, дата дедлайну з календарем, естетична кнопка підпису)
- `frontend/src/components/SignedActModal.jsx` (преміальний вигляд акта: контрастне поле підпису, верифікаційний штамп)
- `frontend/src/components/TicketsSection.jsx` (кнопка «+ Додати правку» у стилі iOS Blue `#0A84FF`, гармонійні бейджі правок без візуального шуму)
- `frontend/src/components/AdminDashboard.jsx` (кнопка вирішення тікета у витонченому смарагдовому матовому стилі замість білого спалаху)

---

## 4. Детальні вимоги до візуальних змін

### 4.1. Колірна палітра та стилістичні токени (`index.css` & Tailwind)
- Сторінка: `bg-[#0A0A0C] text-zinc-100`
- Картки: `bg-[#141418] border border-white/[0.08] shadow-sm rounded-2xl`
- Внутрішні елементи (інпути, чіпси): `bg-[#1C1C22] border border-white/[0.06]`
- Основна дія (Primary Action):
  - Кнопка `[ + Додати правку / повідомити про баг ]`:
    `bg-[#0A84FF] hover:bg-[#0077ED] text-white font-medium shadow-md shadow-blue-500/20 rounded-xl min-h-[44px] transition-all`
  - Кнопка `[ Підписати етап ]`:
    `bg-white text-zinc-950 hover:bg-zinc-100 font-semibold shadow-sm rounded-xl min-h-[44px] transition-all`
  - Кнопка адміна `[ Позначити як вирішено ]`:
    `bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 font-medium rounded-xl min-h-[40px] transition-all`

### 4.2. Статусні бейджі (Unified Micro-Badges)
- Висота 22px, шрифт 10–11px `font-medium`, відступи `px-2 py-0.5`, радіус `rounded-md`:
  - **Затверджено / Вирішено:** `bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`
  - **В роботі:** `bg-blue-500/10 text-blue-400 border border-blue-500/20`
  - **Очікує підтвердження:** `bg-amber-500/10 text-amber-400 border border-amber-500/20`
  - **Черга / Заблоковано:** `bg-zinc-500/10 text-zinc-400 border border-zinc-500/20`
  - **Баг:** `bg-rose-500/10 text-rose-400 border border-rose-500/20`
  - **Правка:** `bg-amber-500/10 text-amber-400 border border-amber-500/20`
  - **Запитання:** `bg-sky-500/10 text-sky-400 border border-sky-500/20`
  - **Етап #X:** `bg-zinc-800/80 text-zinc-300 border border-white/[0.06]`

### 4.3. Картка проекту та Прогрес-бар (`Header.jsx`)
- Картка: `bg-[#141418] border border-white/[0.08] p-4 rounded-2xl`
- Чіпси Figma / Стенд: `bg-[#1C1C22] hover:bg-[#252530] text-zinc-300 text-xs font-medium px-2.5 py-1 rounded-lg border border-white/[0.06] transition-colors`
- Прогрес-бар:
  - Трек: `h-1.5 w-full bg-white/[0.06] rounded-full overflow-hidden`
  - Заповнення: `bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 rounded-full transition-all duration-700`

### 4.4. Сегментований перемикач (`SegmentedTabs.jsx`)
- Контейнер: `bg-[#141418] border border-white/[0.08] p-1 rounded-xl`
- Активна вкладка: `bg-[#22222A] text-white shadow-sm border border-white/[0.06] rounded-lg font-medium text-xs py-2`
- Неактивна вкладка: `text-zinc-400 hover:text-zinc-200 text-xs py-2`
- Крапка-індикатор: `w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50`

### 4.5. Преміальне модальне вікно Акта (`SignedActModal.jsx`)
- Оформлення як фінансового сертифіката:
  - Шапка: назва етапу, сума (з `tabular-nums`), статус «Верифіковано».
  - Поле підпису: контрастне світле або глибоке графітове полотно `bg-zinc-900 border border-white/[0.1] rounded-xl p-3 flex items-center justify-center min-h-[110px]`.
  - Футер: мітка «Цифровий підпис верифіковано через Telegram HMAC • Акт #{order_index}».

---

## 5. Критерії готовності (Definition of Done)
1. Усунено різкі білі спалахи кнопок у табі правок та адмінці.
2. Реалізовано трирівневу глибину шарів: `#0A0A0C` $\to$ `#141418` $\to$ `#1C1C22`.
3. Усі бейджі приведені до єдиної напівпрозорої палітри без візуального шуму.
4. Прогрес-бар отримав акуратний градієнт.
5. Усі грошові показники вирівняно з `tabular-nums`.
6. Фронтенд успішно компілюється командою `npm run build` у `frontend/dist`.
7. `python3 scripts/security_check.py` проходить із кодом 0 (без секретів).
8. Надано звіт та команду git commit.
