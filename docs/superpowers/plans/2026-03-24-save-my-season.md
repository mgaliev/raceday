# Save & My Season — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bookmark save button to each race card (localStorage), a "My Season" counter link in the header, and a new `saved.html` page that renders saved races and supports URL-based sharing.

**Architecture:** `saved.html` is self-contained — it duplicates `fetchAll`, `renderCard`, `badgeStyle`, and localStorage helpers from `index.html`. No shared modules. Both pages link the same `styles.css`. State lives entirely in `localStorage['savedRaces']` (JSON array of Airtable record ID strings) and URL `?races=` parameter.

**Tech Stack:** Plain HTML/CSS/JavaScript, Airtable REST API (client-side fetch), GitHub Pages, no build tools, no frameworks.

**Spec:** `docs/superpowers/specs/2026-03-24-save-my-season-design.md`

---

## Task 1: CSS Foundations

**Files:**
- Modify: `styles.css` — append after line 396 (end of file)

- [ ] **Step 1: Add save button styles**

Append to the end of `styles.css`:

```css
/* ── Save button ─────────────────────────── */

.race-save-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  color: var(--text-3);
  flex-shrink: 0;
  line-height: 1;
  border-radius: 6px;
  transition: color 0.15s;
}

.race-save-btn:hover { color: var(--text-2); }

.race-save-btn.saved { color: var(--accent); }

.race-save-btn svg {
  display: block;
  fill: none;
  transition: fill 0.15s;
}

.race-save-btn.saved svg { fill: currentColor; }

/* ── Shared season banner ────────────────── */

.season-banner {
  background: #fffbe6;
  border-bottom: 1px solid #ffe58f;
  padding: 10px 0;
  text-align: center;
  font-size: 0.875rem;
  color: var(--text);
  line-height: 1.8;
}

.season-banner-actions {
  display: inline-flex;
  gap: 8px;
  margin-left: 10px;
  align-items: center;
}

.season-banner-btn {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1.5px solid var(--accent);
  background: none;
  color: var(--accent);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.season-banner-btn:hover {
  background: var(--accent);
  color: #fff;
}

.season-banner-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-3);
  font-size: 1rem;
  line-height: 1;
  padding: 4px;
  font-family: inherit;
  transition: color 0.15s;
}

.season-banner-close:hover { color: var(--text); }

/* ── Share button ────────────────────────── */

.share-wrap {
  text-align: center;
  padding: 24px 0 8px;
}

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
  font-family: inherit;
  transition: background 0.15s;
}

.share-btn:hover { background: #003DB3; }

.share-btn.copied { background: #2e7d32; }

/* ── saved.html hero ─────────────────────── */

.saved-hero {
  padding: 36px 0 20px;
}

.saved-hero h1 {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}

.saved-hero p {
  color: var(--text-2);
  font-size: 0.9375rem;
}

/* ── Empty state (saved page) ────────────── */

.saved-empty {
  text-align: center;
  padding: 64px 20px;
  color: var(--text-3);
}

.saved-empty-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
}

.saved-empty h2 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-2);
  margin-bottom: 20px;
}

.saved-empty-cta {
  display: inline-flex;
  align-items: center;
  padding: 10px 20px;
  background: var(--accent);
  color: #fff;
  text-decoration: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  transition: background 0.15s;
}

.saved-empty-cta:hover { background: #003DB3; }
```

- [ ] **Step 2: Verify CSS loaded**

Open `index.html` in browser DevTools → Sources. Confirm `styles.css` contains `.race-save-btn`. No visual changes on page yet (class not used).

- [ ] **Step 3: Commit**

```bash
git add styles.css
git commit -m "feat: add save button, banner, share button CSS classes"
```

---

## Task 2: localStorage Helpers + Header Link in index.html

**Files:**
- Modify: `index.html` — script block (after line 184, before constants) and header (lines 118–127)

- [ ] **Step 1: Add localStorage helper functions**

In `index.html`, inside the `<script>` tag, add these functions **immediately after** the `const AIRTABLE_TABLE = 'Races';` line (after line 184):

```javascript
// ── Saved races (localStorage) ──────────────────────────────
function getSaved() {
  try { return JSON.parse(localStorage.getItem('savedRaces') || '[]'); }
  catch { return []; }
}
function isSaved(id) { return getSaved().includes(id); }
function toggleSaved(id) {
  let saved = getSaved();
  if (saved.includes(id)) {
    saved = saved.filter(x => x !== id);
  } else {
    saved.push(id);
  }
  try { localStorage.setItem('savedRaces', JSON.stringify(saved)); } catch {}
  // Update button on this card
  const card = document.querySelector(`.race-card[data-race-id="${id}"]`);
  if (card) {
    const btn = card.querySelector('.race-save-btn');
    const nowSaved = saved.includes(id);
    btn.classList.toggle('saved', nowSaved);
    btn.setAttribute('aria-label', nowSaved ? 'Убрать из сохранённых' : 'Сохранить');
  }
  updateSeasonCount();
}
function updateSeasonCount() {
  const count = getSaved().length;
  const link = document.getElementById('seasonLink');
  if (link) link.textContent = count > 0 ? `Мой сезон (${count})` : 'Мой сезон';
}
// ────────────────────────────────────────────────────────────
```

- [ ] **Step 2: Add "Мой сезон" link to header nav**

Find the `<nav class="header-nav">` block (lines 118–127). Add the season link **before** the closing `</nav>` tag, after the email link:

```html
        <a href="saved.html" class="header-link" id="seasonLink">Мой сезон</a>
```

The nav block should now read:
```html
      <nav class="header-nav">
        <a href="#calendar" class="header-link">Все старты</a>
        <a href="mailto:r4ceday@yandex.com" class="header-link header-email">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="2" y="4" width="20" height="16" rx="2"/>
            <polyline points="2,4 12,13 22,4"/>
          </svg>
          <span class="header-email-text">r4ceday@yandex.com</span>
        </a>
        <a href="saved.html" class="header-link" id="seasonLink">Мой сезон</a>
      </nav>
```

- [ ] **Step 3: Call updateSeasonCount() at end of init()**

Find the `init()` function. It ends with `render();` (around line 396). Add `updateSeasonCount();` on the line immediately after `render();`:

```javascript
    render();
    updateSeasonCount();   // ← add this line
```

- [ ] **Step 4: Verify in browser**

Open `index.html`. Check:
- Header shows "Мой сезон" link (no number, since localStorage empty)
- DevTools Console: call `toggleSaved('testId')` → header updates to "Мой сезон (1)"
- Call `toggleSaved('testId')` again → back to "Мой сезон"
- Call `getSaved()` → returns `[]`

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: add localStorage helpers and My Season header link"
```

---

## Task 3: Update renderCard() — data-race-id + Save Button

**Files:**
- Modify: `index.html` — `renderCard()` function at lines 309–329

- [ ] **Step 1: Replace renderCard() body**

Find `function renderCard(r) {` (line 309). Replace the entire function with:

```javascript
    function renderCard(r) {
      const f = r.fields;
      const discipline = resolveDiscipline(f['Discipline']);
      const location   = resolveLocation(f['Location']);
      const link = f['Registration Link'];
      const hasLink = link && link !== '-' && link !== '';
      const saved = isSaved(r.id);
      return `
        <div class="race-card" data-race-id="${r.id}">
          <div class="race-card-main">
            <div class="race-name">${f['Race Name'] || '—'}</div>
            <div class="race-meta">
              <span class="race-badge" style="${badgeStyle(discipline)}">${discipline}</span>
              <span class="race-date">${f['Date'] || ''}</span>
              <span class="race-place">${location}</span>
            </div>
          </div>
          ${hasLink
            ? `<a class="race-link" href="${link}" target="_blank" rel="noopener">Регистрация →</a>`
            : `<span class="race-link-empty">Скоро</span>`}
          <button class="race-save-btn${saved ? ' saved' : ''}"
                  onclick="toggleSaved('${r.id}')"
                  aria-label="${saved ? 'Убрать из сохранённых' : 'Сохранить'}">
            <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
            </svg>
          </button>
        </div>`;
    }
```

- [ ] **Step 2: Verify in browser**

Open `index.html`. Check:
- Each race card has a small bookmark icon on the right
- Click a bookmark → icon fills blue, header shows "Мой сезон (1)"
- Click again → icon outline grey, header back to "Мой сезон"
- Reload page → saved race bookmark stays filled (persisted in localStorage)
- DevTools → Application → Local Storage → key `savedRaces` shows the array

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add save bookmark button to race cards"
```

---

## Task 4: Create saved.html — Core Page with Card Rendering

**Files:**
- Create: `saved.html` (new file in repo root)

- [ ] **Step 1: Create saved.html**

Create `/Users/maratgaliev/Projects/raceday/saved.html` with the full content below.

This file duplicates the Airtable fetching and rendering logic from `index.html` (intentional — no shared modules per architecture decision).

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <!-- Yandex.Metrika counter -->
  <script type="text/javascript">
    (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();
    for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
    k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
    (window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=107730862', 'ym');
    ym(107730862, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
  </script>
  <noscript><div><img src="https://mc.yandex.ru/watch/107730862" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
  <!-- /Yandex.Metrika counter -->

  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Мой сезон — RaceDay</title>
  <meta name="description" content="Мои сохранённые велогонки на 2026 год — персональный календарь стартов.">
  <meta property="og:title" content="Мой сезон — RaceDay">
  <meta property="og:description" content="Персональный календарь любительских велогонок России 2026.">
  <meta property="og:url" content="https://raceday-russia.ru/saved.html">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
</head>
<body>

  <!-- Shared season banner (hidden by default, shown in shared mode) -->
  <div class="season-banner" id="seasonBanner" style="display:none">
    <span>Это чужой сезон — хочешь добавить все эти гонки в свой?</span>
    <span class="season-banner-actions">
      <button class="season-banner-btn" onclick="addAllToSeason()">Добавить все</button>
      <button class="season-banner-close" onclick="dismissBanner()" aria-label="Закрыть">✕</button>
    </span>
  </div>

  <header class="header">
    <div class="container header-inner">
      <a href="index.html" class="logo" style="text-decoration:none">RaceDay</a>
      <nav class="header-nav">
        <a href="index.html" class="header-link">Все старты</a>
        <a href="mailto:r4ceday@yandex.com" class="header-link header-email">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="2" y="4" width="20" height="16" rx="2"/>
            <polyline points="2,4 12,13 22,4"/>
          </svg>
          <span class="header-email-text">r4ceday@yandex.com</span>
        </a>
        <a href="saved.html" class="header-link" id="seasonLink">Мой сезон</a>
      </nav>
    </div>
  </header>

  <section class="saved-hero">
    <div class="container">
      <h1>Мой сезон</h1>
      <p id="savedSubtitle">Загрузка…</p>
    </div>
  </section>

  <main class="calendar" id="calendar">
    <div class="container">
      <div id="savedContent">
        <!-- skeleton while loading -->
        <div class="skeleton-wrap">
          <div class="skeleton-month"></div>
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
        </div>
      </div>
      <!-- share button (own mode, hidden until ready) -->
      <div class="share-wrap" id="shareWrap" style="display:none">
        <button class="share-btn" id="shareBtn" onclick="shareMySeason()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
          </svg>
          Поделиться сезоном
        </button>
      </div>
    </div>
  </main>

  <footer class="footer">
    <div class="container">
      <p>Данные обновляются вручную. Перед регистрацией проверяйте актуальность на сайте организатора.</p>
      <p>© 2026 RaceDay</p>
    </div>
  </footer>

  <script>
    const AIRTABLE_TOKEN = 'patAljGLbreWlHUVA.f5816ce1d7b4e0de450f040b88df2e16a817fe82e966555006c02115f8256ffd';
    const AIRTABLE_BASE  = 'app2Ho3VmHJhOW63x';

    // ── localStorage helpers ─────────────────────────────────
    function getSaved() {
      try { return JSON.parse(localStorage.getItem('savedRaces') || '[]'); }
      catch { return []; }
    }
    function isSaved(id) { return getSaved().includes(id); }
    function toggleSaved(id) {
      let saved = getSaved();
      if (saved.includes(id)) {
        saved = saved.filter(x => x !== id);
      } else {
        saved.push(id);
      }
      try { localStorage.setItem('savedRaces', JSON.stringify(saved)); } catch {}
      const card = document.querySelector(`.race-card[data-race-id="${id}"]`);
      if (card) {
        const btn = card.querySelector('.race-save-btn');
        const nowSaved = saved.includes(id);
        btn.classList.toggle('saved', nowSaved);
        btn.setAttribute('aria-label', nowSaved ? 'Убрать из сохранённых' : 'Сохранить');
        // In own mode: remove card from DOM on unsave
        if (currentMode === 'own' && !nowSaved) {
          card.closest('.race-list') && card.remove();
          checkEmptyAfterRemoval();
        }
      }
      updateSeasonCount();
    }
    function updateSeasonCount() {
      const count = getSaved().length;
      const link = document.getElementById('seasonLink');
      if (link) link.textContent = count > 0 ? `Мой сезон (${count})` : 'Мой сезон';
    }
    // ────────────────────────────────────────────────────────

    // ── Airtable fetch ───────────────────────────────────────
    async function fetchAll(tableName) {
      const base = `https://api.airtable.com/v0/${AIRTABLE_BASE}/${encodeURIComponent(tableName)}`;
      const headers = { Authorization: `Bearer ${AIRTABLE_TOKEN}` };
      let records = [], offset = null;
      do {
        const params = new URLSearchParams({ pageSize: '100' });
        if (offset) params.set('offset', offset);
        const res = await fetch(`${base}?${params}`, { headers });
        if (!res.ok) throw new Error(`${tableName}: ${res.status}`);
        const data = await res.json();
        records = records.concat(data.records);
        offset = data.offset || null;
      } while (offset);
      return records;
    }
    // ────────────────────────────────────────────────────────

    // ── Lookup maps ──────────────────────────────────────────
    let disciplineMap = {};
    let locationMap   = {};
    let allRaces      = [];

    function resolveDiscipline(ids) {
      if (!ids || !ids.length) return '';
      return ids.map(id => disciplineMap[id] || id).join(', ');
    }
    function resolveLocation(ids) {
      if (!ids || !ids.length) return '';
      return ids.map(id => locationMap[id] || id).join(', ');
    }
    // ────────────────────────────────────────────────────────

    // ── Badge styles ─────────────────────────────────────────
    const DISCIPLINE_COLORS = [
      { key: 'гревел',      bg: '#e8f5e9', color: '#2e7d32' },
      { key: 'mtb',         bg: '#fff3e0', color: '#e65100' },
      { key: 'гран фондо',  bg: '#e3f2fd', color: '#1565c0' },
      { key: 'шоссе',       bg: '#e3f2fd', color: '#1565c0' },
      { key: 'велокросс',   bg: '#f3e5f5', color: '#6a1b9a' },
      { key: 'многодневка', bg: '#fce4ec', color: '#c62828' },
      { key: 'байкпакинг',  bg: '#e0f7fa', color: '#00695c' },
      { key: 'бревет',      bg: '#f1f8e9', color: '#558b2f' },
    ];
    function badgeStyle(discipline) {
      if (!discipline) return 'background:#f5f5f5;color:#666';
      const d = discipline.toLowerCase();
      for (const { key, bg, color } of DISCIPLINE_COLORS) {
        if (d.includes(key)) return `background:${bg};color:${color}`;
      }
      return 'background:#f5f5f5;color:#666';
    }
    // ────────────────────────────────────────────────────────

    // ── Render card ──────────────────────────────────────────
    function renderCard(r) {
      const f = r.fields;
      const discipline = resolveDiscipline(f['Discipline']);
      const location   = resolveLocation(f['Location']);
      const link = f['Registration Link'];
      const hasLink = link && link !== '-' && link !== '';
      const saved = isSaved(r.id);
      return `
        <div class="race-card" data-race-id="${r.id}">
          <div class="race-card-main">
            <div class="race-name">${f['Race Name'] || '—'}</div>
            <div class="race-meta">
              <span class="race-badge" style="${badgeStyle(discipline)}">${discipline}</span>
              <span class="race-date">${f['Date'] || ''}</span>
              <span class="race-place">${location}</span>
            </div>
          </div>
          ${hasLink
            ? `<a class="race-link" href="${link}" target="_blank" rel="noopener">Регистрация →</a>`
            : `<span class="race-link-empty">Скоро</span>`}
          <button class="race-save-btn${saved ? ' saved' : ''}"
                  onclick="toggleSaved('${r.id}')"
                  aria-label="${saved ? 'Убрать из сохранённых' : 'Сохранить'}">
            <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
            </svg>
          </button>
        </div>`;
    }
    // ────────────────────────────────────────────────────────

    // ── Date helpers (for sort) ──────────────────────────────
    const MONTHS_ORDER = [
      'январь','февраль','март','апрель','май','июнь',
      'июль','август','сентябрь','октябрь','ноябрь','декабрь'
    ];
    const MONTH_STEMS = [
      ['январ','январь'], ['феврал','февраль'], ['март','март'],
      ['апрел','апрель'], ['мая','май'],         ['июн','июнь'],
      ['июл','июль'],     ['август','август'],   ['сентябр','сентябрь'],
      ['октябр','октябрь'],['ноябр','ноябрь'],  ['декабр','декабрь'],
    ];
    const MONTHS_DISPLAY = {
      'январь':'Январь','февраль':'Февраль','март':'Март',
      'апрель':'Апрель','май':'Май','июнь':'Июнь',
      'июль':'Июль','август':'Август','сентябрь':'Сентябрь',
      'октябрь':'Октябрь','ноябрь':'Ноябрь','декабрь':'Декабрь',
      'без даты':'Дата уточняется'
    };
    function getMonth(dateStr) {
      if (!dateStr) return 'без даты';
      const s = dateStr.toLowerCase();
      for (const [stem, canonical] of MONTH_STEMS) {
        if (s.includes(stem)) return canonical;
      }
      return 'без даты';
    }
    function monthIdx(m) {
      const i = MONTHS_ORDER.indexOf(m);
      return i === -1 ? 999 : i;
    }
    function getDay(dateStr) {
      if (!dateStr) return 999;
      const m = dateStr.match(/(\d+)/);
      return m ? parseInt(m[1], 10) : 999;
    }
    // ────────────────────────────────────────────────────────

    // ── Render race list ─────────────────────────────────────
    function renderRaces(races) {
      const content = document.getElementById('savedContent');
      if (races.length === 0) {
        showEmpty();
        return;
      }
      const byMonth = {};
      for (const r of races) {
        const m = getMonth(r.fields['Date']);
        if (!byMonth[m]) byMonth[m] = [];
        byMonth[m].push(r);
      }
      const sortedMonths = Object.keys(byMonth).sort((a, b) => monthIdx(a) - monthIdx(b));
      content.innerHTML = sortedMonths.map(m => `
        <div class="month-group">
          <div class="month-header">${MONTHS_DISPLAY[m] || m}</div>
          <div class="race-list">${byMonth[m]
            .slice()
            .sort((a, b) => getDay(a.fields['Date']) - getDay(b.fields['Date']))
            .map(r => renderCard(r)).join('')}</div>
        </div>`
      ).join('');
    }

    function showEmpty() {
      document.getElementById('savedContent').innerHTML = `
        <div class="saved-empty">
          <div class="saved-empty-icon">🚴</div>
          <h2>У тебя пока нет сохранённых гонок</h2>
          <a href="index.html" class="saved-empty-cta">Смотреть календарь →</a>
        </div>`;
      document.getElementById('shareWrap').style.display = 'none';
    }

    function checkEmptyAfterRemoval() {
      const remaining = document.querySelectorAll('.race-card');
      if (remaining.length === 0) showEmpty();
    }
    // ────────────────────────────────────────────────────────

    // ── Mode state ───────────────────────────────────────────
    let currentMode = 'own'; // 'shared' | 'own' | 'empty'
    let urlIds = [];

    function getUrlIds() {
      const params = new URLSearchParams(window.location.search);
      const races = params.get('races');
      if (!races || !races.trim()) return [];
      return races.split(',').filter(Boolean);
    }
    // ────────────────────────────────────────────────────────

    // ── Banner actions ───────────────────────────────────────
    function dismissBanner() {
      document.getElementById('seasonBanner').style.display = 'none';
    }

    function addAllToSeason() {
      let saved = getSaved();
      urlIds.forEach(id => { if (!saved.includes(id)) saved.push(id); });
      try { localStorage.setItem('savedRaces', JSON.stringify(saved)); } catch {}
      history.replaceState({}, '', window.location.pathname);
      urlIds = [];
      currentMode = 'own';
      dismissBanner();
      updateSeasonCount();
      const ownRaces = allRaces.filter(r => getSaved().includes(r.id));
      renderRaces(ownRaces);
      updateSubtitle(ownRaces.length, 'own');
      updateShareButton(ownRaces.length);
    }
    // ────────────────────────────────────────────────────────

    // ── Share button ─────────────────────────────────────────
    function shareMyseason() {
      const ids = getSaved();
      const url = window.location.origin + window.location.pathname + '?races=' + ids.join(',');
      const btn = document.getElementById('shareBtn');
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
          btn.textContent = 'Ссылка скопирована ✓';
          btn.classList.add('copied');
          setTimeout(() => {
            btn.textContent = '';
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg> Поделиться сезоном`;
            btn.classList.remove('copied');
          }, 2000);
        });
      } else {
        prompt('Скопируй ссылку:', url);
      }
    }
    // ────────────────────────────────────────────────────────

    // ── Subtitle & share button helpers ─────────────────────
    function updateSubtitle(count, mode) {
      const el = document.getElementById('savedSubtitle');
      if (mode === 'shared') {
        el.textContent = `${count} ${pluralRaces(count)} — чужой сезон`;
      } else if (count > 0) {
        el.textContent = `${count} ${pluralRaces(count)} в твоём сезоне`;
      } else {
        el.textContent = 'Сохраняй гонки из календаря — они появятся здесь';
      }
    }
    function updateShareButton(count) {
      document.getElementById('shareWrap').style.display = count > 0 ? '' : 'none';
    }
    function pluralRaces(n) {
      if (n % 10 === 1 && n % 100 !== 11) return 'гонка';
      if ([2,3,4].includes(n % 10) && ![12,13,14].includes(n % 100)) return 'гонки';
      return 'гонок';
    }
    // ────────────────────────────────────────────────────────

    // ── Init ─────────────────────────────────────────────────
    async function init() {
      urlIds = getUrlIds();
      const localIds = getSaved();

      if (urlIds.length > 0) {
        currentMode = 'shared';
      } else if (localIds.length === 0) {
        currentMode = 'empty';
      } else {
        currentMode = 'own';
      }

      try {
        const [disciplines, locations, races] = await Promise.all([
          fetchAll('Disciplines'),
          fetchAll('Locations'),
          fetchAll('Races'),
        ]);

        disciplines.forEach(r => { disciplineMap[r.id] = r.fields['Discipline Name'] || ''; });
        locations.forEach(r => { locationMap[r.id] = r.fields['City'] || r.fields['Location Name'] || ''; });
        allRaces = races;

        if (currentMode === 'empty') {
          showEmpty();
          updateSubtitle(0, 'own');
          updateSeasonCount();
          return;
        }

        const ids = currentMode === 'shared' ? urlIds : localIds;
        const filtered = allRaces.filter(r => ids.includes(r.id));

        renderRaces(filtered);
        updateSubtitle(filtered.length, currentMode);
        updateSeasonCount();

        if (currentMode === 'shared') {
          document.getElementById('seasonBanner').style.display = '';
          document.getElementById('shareWrap').style.display = 'none';
        } else {
          updateShareButton(filtered.length);
        }

      } catch (err) {
        document.getElementById('savedContent').innerHTML =
          `<div class="empty"><p>Не удалось загрузить данные. Обновите страницу.</p></div>`;
        console.error('Airtable error:', err);
      }
    }

    init();
  </script>

</body>
</html>
```

- [ ] **Step 2: Verify function name consistency**

The share button HTML uses `onclick="shareMyseason()"` (lowercase 's' in 'season'). The JS function must be defined as `function shareMyseason()` — same casing. Verify both match in your editor before opening in browser. If there is any mismatch, rename both to `shareMyseason` (lowercase 's').

- [ ] **Step 3: Verify saved.html in browser — own mode**

1. In index.html, save 2-3 races by clicking their bookmarks
2. Click "Мой сезон" header link → opens saved.html
3. Check: saved races appear as cards with bookmark buttons filled blue
4. Check: subtitle shows "N гонок в твоём сезоне"
5. Check: "Поделиться сезоном" button is visible
6. Click unsave on a card → card disappears from list immediately
7. Unsave all cards → empty state shows with "Смотреть календарь →" CTA

- [ ] **Step 4: Verify saved.html — empty state**

1. Clear localStorage: DevTools → Application → Local Storage → Delete All
2. Open saved.html directly
3. Check: 🚴 emoji, "У тебя пока нет сохранённых гонок", CTA button

- [ ] **Step 5: Commit**

```bash
git add saved.html
git commit -m "feat: create saved.html with own-mode card rendering and empty state"
```

---

## Task 5: Share Button + Shared Season Mode

**Files:**
- Modify: `saved.html` — verify share and banner behavior end-to-end

Note: the share button and banner logic are already in the `saved.html` created in Task 4. This task is verification-only.

- [ ] **Step 1: Verify share button**

1. Open saved.html (with 2+ saved races)
2. Click "Поделиться сезоном"
3. Check: button turns green with "Ссылка скопирована ✓"
4. After 2 seconds: button resets to original text
5. Check clipboard: URL ends with `?races=recXXX,recYYY,...`

- [ ] **Step 2: Verify shared mode (banner)**

1. Copy the share URL from Step 1
2. Clear localStorage (DevTools → Local Storage → Delete All)
3. Open the copied URL in browser
4. Check: yellow banner appears: "Это чужой сезон — хочешь добавить все эти гонки в свой?"
5. Check: "Поделиться сезоном" button is NOT visible (shared mode)
6. Check: subtitle says "N гонок — чужой сезон"
7. Click ✕ → banner disappears, cards remain visible
8. Reload page → banner reappears (expected: URL still has `?races=`)

- [ ] **Step 3: Verify "Добавить все"**

1. Open shared URL (from Step 2)
2. Click "Добавить все"
3. Check: banner disappears
4. Check: URL no longer has `?races=` (address bar updated by `history.replaceState`)
5. Check: "Поделиться сезоном" button NOW appears (switched to own mode)
6. Check: header shows "Мой сезон (N)" with correct count
7. Reload page → no banner (URL is clean), cards shown as own-mode

- [ ] **Step 4: Commit**

```bash
git commit --allow-empty -m "feat: verify share and shared-season banner — no code changes needed"
```

(If you made any bug fixes in this task, stage those files instead of using `--allow-empty`.)

---

## Task 6: End-to-End Verification & Commit to Main

- [ ] **Step 1: Full flow test**

Run through all scenarios:

| Scenario | Expected |
|----------|----------|
| Fresh visit to index.html | Header: "Мой сезон" (no number) |
| Save 1 race | Header: "Мой сезон (1)", bookmark filled |
| Unsave the race | Header: "Мой сезон", bookmark outline |
| Save 3 races, open saved.html | 3 cards shown, subtitle "3 гонки в твоём сезоне" |
| Click share, open URL in incognito | Banner shown, no share button |
| Click "Добавить все" | Banner gone, URL clean, share button visible |
| Unsave all on saved.html | Empty state + CTA |
| Reload index.html | Saved state persists from localStorage |

- [ ] **Step 2: Check mobile (resize to 375px)**

- Header links don't overflow (email text hides on ≤600px, "Мой сезон" stays)
- Race cards: bookmark button doesn't crowd registration button
- Banner text wraps cleanly

- [ ] **Step 3: Final commit**

```bash
git add index.html styles.css saved.html
git commit -m "feat: Save & My Season — bookmark races, share URL, saved.html page"
```

- [ ] **Step 4: Push and open PR**

```bash
git push origin HEAD
gh pr create --title "feat: Save & My Season" --body "Bookmark races to localStorage, My Season page, URL sharing with shared-season banner."
```

---

## Reference: Key File Locations

| What | Where |
|------|-------|
| renderCard() | `index.html` line 309 |
| Header nav | `index.html` lines 118–127 |
| init() | `index.html` line 380 |
| AIRTABLE_TOKEN | `index.html` line 182 |
| DISCIPLINE_COLORS | `index.html` lines 218–227 |
| MONTH_STEMS / MONTHS_ORDER | `index.html` lines 186–205 |
| Footer CSS | `styles.css` lines 377–396 |
| New CSS classes | `styles.css` lines 397+ (appended in Task 1) |
