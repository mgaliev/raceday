# Design: Save & My Season

**Date:** 2026-03-24
**Status:** Approved

## Overview

Two connected zero-backend features for RaceDay that allow users to bookmark races and share their personal race calendar with others.

- **Feature 1** — Save button on each race card (localStorage)
- **Feature 2** — saved.html "My Season" page (localStorage + URL sharing)

No backend, no frameworks, no architecture changes. Works on GitHub Pages.

---

## Architecture

### Files Changed / Created

| File | Change |
|------|--------|
| `index.html` | Add save button to each card; add "My Season (N)" link to header; add save helper functions |
| `styles.css` | Add `.race-save-btn`, `.race-save-btn.saved`, `.season-banner`, `.share-btn` styles |
| `saved.html` | New self-contained page. Duplicates fetchAll + renderCard + badgeStyle from index.html |

`styles.css` is shared between both pages via `<link rel="stylesheet">`.

No new JS files. No shared modules. `saved.html` is fully self-contained.

---

## Feature 1 — Save Button

### UI

A bookmark icon button appended to each race card, to the right of the "Регистрация" or "Скоро" element.

- **Default state:** SVG bookmark outline, `color: var(--text-3)` (#999)
- **Saved state:** SVG bookmark filled, `color: var(--accent)` (#0057FF)
- Square icon button, no text, `aria-label="Сохранить"` / `aria-label="Убрать из сохранённых"`
- Smooth `transition: color 0.15s`

### renderCard() — required data attribute

`renderCard()` must add `data-race-id="${r.id}"` to the `.race-card` root div:

```html
<div class="race-card" data-race-id="recABC123">
```

This enables reactive DOM updates (toggling button state, removing card on unsave) by querying `document.querySelector('.race-card[data-race-id="recXYZ"]')`.

### localStorage Schema

```
key:   'savedRaces'
value: JSON array of Airtable record ID strings
       e.g. ["recABC123", "recXYZ456"]
```

### Helper Functions (in index.html `<script>`, duplicated in saved.html)

```js
function getSaved()            // returns string[] from localStorage, [] on error
function isSaved(id)           // boolean
function toggleSaved(id)       // add or remove id, persist, update UI
function updateSeasonCount()   // refresh header "Мой сезон (N)" text
```

All localStorage access wrapped in `try/catch` — falls back to `[]` in private browsing.

`updateSeasonCount()` is called:
- On page load (both index.html and saved.html)
- After every `toggleSaved()` call

### Header Link

Added to `.header-nav` in both index.html and saved.html:

```html
<a href="saved.html" class="header-link" id="seasonLink">Мой сезон</a>
```

- When count > 0: shows "Мой сезон (N)"
- When count === 0: shows "Мой сезон" (no parenthetical)
- Updated on every `toggleSaved` call and on page load

---

## Feature 2 — saved.html "My Season" Page

### Page Structure

```
<header>            — identical to index.html header (logo + nav with "My Season" link)
[banner?]           — "Это чужой сезон" banner (conditionally rendered, in shared mode only)
<section.hero-like> — "Мой сезон" title + subtitle
<main.calendar>     — race cards (same classes as index.html)
[share button]      — "Поделиться сезоном" (own mode only, hidden when 0 races)
<footer>            — identical to index.html footer
```

### Meta & Analytics

`saved.html` includes:
- `<title>Мой сезон — RaceDay</title>`
- Yandex.Metrika counter (same counter ID as index.html)
- Basic static OG tags: `og:title`, `og:description`, `og:url` (static values — dynamic per-user OG is not feasible on a static host)

### Data Loading Logic

On page load, `saved.html` runs:

1. Fetch all three Airtable tables in parallel (Races, Disciplines, Locations)
2. Build `disciplineMap` and `locationMap`
3. Read `urlIds` from `?races=` URL parameter (split by `,`, filter empty strings)
4. Read `localIds` from `localStorage['savedRaces']`
5. Determine mode:
   - `urlIds.length > 0` → **shared mode**: display races matching `urlIds`
   - otherwise → **own mode**: display races matching `localIds`
   - `localIds.length === 0` and no URL param → **empty state**

### Sort Order

In both modes, races are displayed chronologically (same sort as index.html), grouped by month. Ungrouped races (no date) shown at the end.

### Shared Season Banner (shown in shared mode only)

Rendered below the header, above the hero title.

```
┌─────────────────────────────────────────────────────────┐
│ Это чужой сезон — хочешь добавить все эти гонки в свой? │
│                          [Добавить все]  [✕]            │
└─────────────────────────────────────────────────────────┘
```

**"Добавить все" behavior:**
1. Merges `urlIds` into `localStorage['savedRaces']` (deduplicating)
2. Calls `history.replaceState({}, '', window.location.pathname)` to strip `?races=` from URL (uses `window.location.pathname` not a hardcoded string, for portability)
3. Clears `urlIds = []` in memory and sets `mode = 'own'`
4. Hides banner
5. Re-renders cards from updated `localIds` (own mode)

After this, bookmark buttons on cards operate in own-mode logic (unsave removes card from DOM). This prevents the banner from reappearing on page refresh after merging.

**"✕" behavior:** Dismisses banner only. No changes to localStorage or URL. Cards remain showing `urlIds`.

### Bookmark Buttons on saved.html Cards

Each card on saved.html has the save button (same as index.html).

**In own mode:**
- Unsave → removes card from the visible list immediately (reactive: remove `.race-card[data-race-id]` from DOM); updates `updateSeasonCount()`
- Save (if somehow unsaved) → adds to localStorage, updates button state

**In shared mode:**
- Save → adds that individual race to `localStorage['savedRaces']`; button turns filled/blue
- Unsave → removes from localStorage; button returns to outline
- Cards are NOT removed from the visible list in shared mode (they stay visible regardless of localStorage state)

### Share Button

Shown in **own mode only**. Hidden (not rendered) when `localIds.length === 0`.

Position: below the race list (above footer), centered.

Behavior on click:
1. Build URL: `window.location.origin + '/saved.html?races=' + localIds.join(',')`
2. Copy to clipboard via `navigator.clipboard.writeText()`
3. Fallback if clipboard API unavailable: `prompt('Скопируй ссылку:', url)`
4. Button text changes to "Ссылка скопирована ✓" for 2 seconds, then resets

**URL length:** Airtable record IDs are 17 characters (`rec` + 14 chars). At 100 saved races the URL is ~1900 chars — within safe browser limits. No truncation or warning needed for typical usage.

### Empty State

Shown when no races to display:

```
🚴
У тебя пока нет сохранённых гонок

[Смотреть календарь →]   (links to index.html)
```

---

## CSS Additions (styles.css)

### `.race-save-btn`

```css
/* Ghost icon button, sits to the right of .race-link/.race-link-empty */
.race-save-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  color: var(--text-3);
  flex-shrink: 0;
  line-height: 1;
  transition: color 0.15s;
  border-radius: 6px;
}
.race-save-btn:hover { color: var(--text-2); }
.race-save-btn.saved { color: var(--accent); }
```

### `.season-banner`

```css
/* Full-width info bar below header */
.season-banner {
  background: #fffbe6;            /* warm yellow, distinct from page */
  border-bottom: 1px solid #ffe58f;
  padding: 10px 0;
  text-align: center;
  font-size: 0.875rem;
  color: var(--text);
}
```

### `.share-btn`

```css
/* Centered CTA button below race list */
.share-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.share-btn:hover { background: #003DB3; }    /* --accent-dark already in styles.css as #003DB3 */
.share-btn.copied { background: #2e7d32; }   /* green confirmation */
```

---

## Error Handling

| Situation | Behavior |
|-----------|----------|
| Airtable unreachable | Error message: "Не удалось загрузить данные. Обновите страницу." |
| URL contains non-existent race IDs | Silently filtered out — no render, no error |
| localStorage unavailable (private mode) | `try/catch` everywhere, falls back to `[]` |
| `navigator.clipboard` unavailable | Fallback: `prompt()` with URL for manual copy |
| All saved races removed on saved.html | Empty state shown immediately without reload |
| `?races=` present but empty string | Treated as no parameter, falls back to localStorage |
| Last race removed in own mode | Share button hidden, empty state shown |

## Out of Scope (MVP)

- Cross-tab localStorage sync (`storage` event) — not supported; single-tab use assumed
- Dynamic OG meta tags per user season — not feasible on static host
- Truncation/warning for very large saved lists (>100 races) — not needed at current data volume

---

## Constraints

- No frameworks, no build tools
- No server-side routing (GitHub Pages compatible)
- Airtable read-only public token already in index.html — same token reused in saved.html (acceptable: already public)
- Reuse existing CSS card classes: `.race-card`, `.race-card-main`, `.race-name`, `.race-meta`, `.race-badge`, `.race-date`, `.race-place`, `.race-link`, `.race-link-empty`
- All code works without a server (file:// and https://)
