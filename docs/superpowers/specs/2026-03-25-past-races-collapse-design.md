# Past Races Collapse — Design Spec

## Context

When a user opens the calendar, the race list starts from January and they must scroll past months of already-completed races to reach upcoming events. This creates friction for the primary use case: finding what's next.

The goal is to make the current month the default starting point, while keeping past races fully accessible with one click.

## Behaviour

- On page load and on every filter change, past months are collapsed by default
- A toggle button above the upcoming months shows: `▾ Прошедшие старты · {N}` where N is the total number of races in past months
- Clicking the button expands/collapses the past months section; the chevron rotates 180° to indicate state
- If no past months exist in the current filtered result, the toggle button is not rendered
- "Без даты" races are treated as upcoming (not past)
- Collapsed state is not persisted — resets on every render (page load or filter change)

## Definition of "Past"

A month is past if `MONTHS_ORDER.indexOf(monthName) < new Date().getMonth()` (0-based index). This uses the client's local time.

## Code Changes

### `index.html`

**New helper: `renderMonthGroup(m, races)`**
Extracts the existing month group HTML template to avoid duplication between past and upcoming rendering.

```js
function renderMonthGroup(m, races) {
  return `
    <div class="month-group">
      <div class="month-header">${MONTHS_DISPLAY[m] || m}</div>
      <div class="race-list">${races
        .slice()
        .sort((a, b) => getDay(a.fields['Date']) - getDay(b.fields['Date']))
        .map(r => renderCard(r)).join('')}</div>
    </div>`;
}
```

**New function: `togglePast(btn)`**
Toggles the `hidden` attribute on the adjacent `.past-months` div and the `.open` class on the button.

```js
function togglePast(btn) {
  const section = btn.nextElementSibling;
  const expanded = btn.getAttribute('aria-expanded') === 'true';
  btn.setAttribute('aria-expanded', String(!expanded));
  section.hidden = expanded;
  btn.classList.toggle('open', !expanded);
}
```

**Modified: `render()`**
Split `sortedMonths` into `pastMonths` and `upcomingMonths`, render past months inside a collapsible section.

```js
const curMonthIdx = new Date().getMonth(); // 0-based
const pastMonths = sortedMonths.filter(m => monthIdx(m) < curMonthIdx);
const upcomingMonths = sortedMonths.filter(m => monthIdx(m) >= curMonthIdx);
const pastCount = pastMonths.reduce((sum, m) => sum + byMonth[m].length, 0);

let html = '';

if (pastMonths.length > 0) {
  html += `
    <div class="past-section">
      <button class="past-toggle" onclick="togglePast(this)" aria-expanded="false">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
        Прошедшие старты · ${pastCount}
      </button>
      <div class="past-months" hidden>
        ${pastMonths.map(m => renderMonthGroup(m, byMonth[m])).join('')}
      </div>
    </div>`;
}

html += upcomingMonths.map(m => renderMonthGroup(m, byMonth[m])).join('');
content.innerHTML = html;
```

### `styles.css`

Add after `.month-group` styles:

```css
.past-section {
  margin-bottom: 24px;
}

.past-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 14px;
  cursor: pointer;
  color: var(--text-3);
  font-size: 0.8125rem;
  font-weight: 500;
  width: 100%;
  text-align: left;
  transition: color 0.15s, border-color 0.15s;
}

.past-toggle:hover {
  color: var(--text-1);
  border-color: var(--text-3);
}

.past-toggle svg {
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.past-toggle.open svg {
  transform: rotate(180deg);
}

.past-months {
  margin-top: 16px;
}
```

## Edge Cases

| Scenario | Behaviour |
|---|---|
| All races are in past months | Toggle shown, upcoming section empty (no empty state — the races exist, just collapsed) |
| All races are upcoming | No toggle rendered |
| Filter applied with only past results | Toggle shown, user must click to see results |
| January (no past months) | No toggle rendered |
| "Без даты" races | Treated as upcoming (`monthIdx` returns 999) |

## Files to Modify

- `index.html` — `render()` function (~line 373), add `renderMonthGroup()` and `togglePast()` before it
- `styles.css` — add after `.month-group` block (~line 252)

## Verification

1. Open site in current month — calendar shows toggle button above upcoming months, past months not visible
2. Click toggle — past months expand; chevron rotates
3. Click again — past months collapse
4. Apply a discipline filter — past months remain collapsed
5. Open site in January — no toggle button rendered
6. Check a race with no date — appears in upcoming section, not past
