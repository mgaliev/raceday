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
| `styles.css` | Add `.race-save-btn`, `.race-save-btn.saved` styles; `.header-season` for header link |
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
- Smooth `transition: color 0.15s, fill 0.15s`

### localStorage Schema

```
key:   'savedRaces'
value: JSON array of Airtable record ID strings
       e.g. ["recABC123", "recXYZ456"]
```

### Helper Functions (in index.html `<script>`)

```js
function getSaved()          // returns string[] from localStorage, [] on error
function isSaved(id)         // boolean
function toggleSaved(id)     // add or remove id, persist, update UI
function updateSeasonCount() // refresh header counter
```

All localStorage access wrapped in `try/catch` — falls back to `[]` in private browsing.

### Header Link

Added to `.header-nav` in index.html:

```html
<a href="saved.html" class="header-link header-season" id="seasonLink">Мой сезон</a>
```

- When count > 0: shows "Мой сезон (N)"
- When count === 0: shows "Мой сезон" (no number)
- Updated on every `toggleSaved` call and on page load

---

## Feature 2 — saved.html "My Season" Page

### Page Structure

```
<header>            — identical to index.html header (logo + nav with "My Season" link)
[banner?]           — "Это чужой сезон" banner (conditionally rendered)
<section.hero-like> — "Мой сезон" title + subtitle
<main.calendar>     — race cards (same classes as index.html)
[share button]      — "Поделиться сезоном" (only in own-season mode)
<footer>            — identical to index.html footer
```

### Data Loading Logic

On page load, `saved.html` runs:

1. Fetch all three Airtable tables in parallel (Races, Disciplines, Locations)
2. Build `disciplineMap` and `locationMap`
3. Read `urlIds` from `?races=` URL parameter (split by `,`, filter empty)
4. Read `localIds` from `localStorage['savedRaces']`
5. Determine mode:
   - `urlIds.length > 0` → **shared mode**: display races matching `urlIds`
   - otherwise → **own mode**: display races matching `localIds`
   - both empty → **empty state**

### Shared Season Banner (shown in shared mode)

```
┌─────────────────────────────────────────────────────────┐
│ Это чужой сезон — хочешь добавить все эти гонки в свой? │
│                          [Добавить все]  [✕]            │
└─────────────────────────────────────────────────────────┘
```

- "Добавить все" → merges `urlIds` into `localStorage['savedRaces']`, hides banner, switches to own mode
- "✕" → dismisses banner only (no action on data)

### Share Button (shown in own mode only)

Position: below the race list (above footer), centered.

Behavior on click:
1. Build `window.location.origin + '/saved.html?races=' + localIds.join(',')`
2. Copy to clipboard via `navigator.clipboard.writeText()`
3. Fallback if clipboard unavailable: `prompt('Скопируй ссылку:', url)`
4. Button text changes to "Ссылка скопирована ✓" for 2 seconds, then resets

### Bookmark Buttons on saved.html Cards

Each card on saved.html also has the save button (same as index.html).
Clicking unsave removes the race from the list immediately (reactive render).

### Empty State

Shown when no races to display (no localStorage, no URL param, or all removed):

```
[Bicycle emoji or icon]
У тебя пока нет сохранённых гонок

[Смотреть календарь →]   (links to index.html)
```

---

## CSS Additions (styles.css)

```css
/* Save button on race card */
.race-save-btn { }          /* base: ghost button, text-3 color */
.race-save-btn.saved { }    /* accent color, filled SVG */
.race-save-btn:hover { }    /* slight color shift */

/* "My Season" header link — same as .header-link, no extra styles needed */

/* Shared season banner */
.season-banner { }

/* Share button */
.share-btn { }
.share-btn.copied { }
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

---

## Constraints

- No frameworks, no build tools
- No server-side routing (GitHub Pages compatible)
- Airtable read-only public token already in index.html — same token reused in saved.html (acceptable: it is already public)
- Reuse existing CSS card classes: `.race-card`, `.race-card-main`, `.race-name`, `.race-meta`, `.race-badge`, `.race-date`, `.race-place`, `.race-link`, `.race-link-empty`
- All code works without a server (file:// and https://)
