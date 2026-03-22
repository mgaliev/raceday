# RaceDay — MVP Календарь велогонок

## Project Goal
MVP-агрегатор любительских велогонок России. Данные собираются вручную в Airtable, отображаются на статическом лендинге. Цель: проверить retention и реальный спрос на агрегатор.

Предыстория: фейк-дор лендинг дал ~9% CTR, но нулевую конверсию в Google Form. Вывод — спрос есть, ценность только у реального продукта с данными.

## Domain & Branding
- Service name: **RaceDay**
- Domain: **raceday-russia.ru**
- No email configured yet

## Tech Stack
- Static HTML/CSS/JavaScript (single page, no frameworks)
- GitHub Pages for hosting
- Airtable REST API для данных (fetch из браузера)
- Yandex Metrika для аналитики (counter ID: 107730862)
- No build tools

## Airtable
- Base ID: `app2Ho3VmHJhOW63x`
- Table: `Races`
- Fields: `Race Name`, `Discipline`, `Location`, `Date`, `Registration Link`
- Token хранится в index.html (read-only, публичный репо — ок)

## File Structure
```
/
├── index.html       — лендинг + JS (всё в одном файле)
├── styles.css       — стили
├── races_2026.md    — исходник данных (Markdown)
├── races_2026.csv   — исходник данных (CSV для импорта)
└── CLAUDE.md
```

## Структура лендинга
1. **Header** — лого RaceDay, ссылка на #calendar
2. **Hero** — заголовок, подзаголовок, счётчик стартов
3. **Filter bar** (sticky) — chips по дисциплине, dropdown регион + месяц
4. **Calendar timeline** — гонки сгруппированы по месяцам, карточки с бейджем дисциплины
5. **Footer** — email, дисклеймер

## Design
- Шрифт: Inter
- Палитра: белый фон, акцент `#0057FF`, текст `#0d0d0d`
- Бейджи дисциплин: цветовая кодировка (гравел — зелёный, MTB — оранжевый, шоссе — синий и т.д.)
- Mobile-first, протестировать на 375px

## Implementation Notes
- Данные загружаются через fetch при открытии страницы (без сервера)
- Пагинация Airtable обрабатывается (pageSize=100, offset)
- Фильтрация: по дисциплине (chips), региону (dropdown), месяцу (dropdown)
- Состояния: skeleton при загрузке, empty state при пустом фильтре, error state
- Google Form удалена полностью
