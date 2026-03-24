# Race Management CLI Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/race.py` — a zero-dependency Python CLI for adding, updating, and bulk-importing races into Airtable without touching Claude Code.

**Architecture:** Single file `scripts/race.py` with pure functions for validation/matching and an `AirtableClient` class for HTTP. Tests in `tests/test_race.py` using `unittest` + `unittest.mock`. Commands: `add`, `update`, `import`.

**Tech Stack:** Python 3 stdlib only — `urllib.request`, `urllib.parse`, `json`, `csv`, `argparse`, `unittest`, `unittest.mock`

---

## File Map

| File | Purpose |
|------|---------|
| `scripts/race.py` | Main CLI script — all logic |
| `tests/test_race.py` | Unit tests — pure functions + mocked Airtable calls |

---

### Task 1: Scaffold + config loading

**Files:**
- Create: `scripts/race.py`
- Create: `tests/test_race.py`

- [ ] **Step 1: Write failing test for `load_config`**

Create `tests/test_race.py`:

```python
import unittest
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from race import load_config

class TestLoadConfig(unittest.TestCase):
    def test_reads_key_value_pairs(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.local', delete=False) as f:
            f.write("AIRTABLE_TOKEN_WRITE=tok123\nAIRTABLE_BASE=appABC\n")
            path = f.name
        try:
            cfg = load_config(path)
            self.assertEqual(cfg['AIRTABLE_TOKEN_WRITE'], 'tok123')
            self.assertEqual(cfg['AIRTABLE_BASE'], 'appABC')
        finally:
            os.unlink(path)

    def test_missing_file_raises(self):
        with self.assertRaises(SystemExit):
            load_config('/nonexistent/secrets.local')

    def test_ignores_comments_and_blanks(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.local', delete=False) as f:
            f.write("# comment\n\nKEY=val\n")
            path = f.name
        try:
            cfg = load_config(path)
            self.assertEqual(cfg['KEY'], 'val')
            self.assertNotIn('# comment', cfg)
        finally:
            os.unlink(path)

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd /Users/maratgaliev/Projects/raceday
python3 -m pytest tests/test_race.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'race'`

- [ ] **Step 3: Create `scripts/race.py` with `load_config`**

```python
#!/usr/bin/env python3
"""RaceDay — CLI для управления гонками в Airtable."""

import argparse
import csv
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

MONTHS_GENITIVE = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря',
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(path=None):
    """Read KEY=VALUE pairs from secrets.local."""
    if path is None:
        path = os.path.join(BASE_DIR, 'secrets.local')
    if not os.path.exists(path):
        print(f"Ошибка: файл конфигурации не найден: {path}")
        print("Создайте secrets.local с AIRTABLE_TOKEN_WRITE и AIRTABLE_BASE")
        sys.exit(1)
    cfg = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                cfg[k.strip()] = v.strip()
    return cfg


if __name__ == '__main__':
    pass
```

- [ ] **Step 4: Run test — expect PASS**

```bash
python3 -m pytest tests/test_race.py::TestLoadConfig -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: scaffold race.py with load_config"
```

---

### Task 2: Date validation and conversion

**Files:**
- Modify: `scripts/race.py` — add `validate_date()`
- Modify: `tests/test_race.py` — add `TestValidateDate`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_race.py`:

```python
from race import validate_date

class TestValidateDate(unittest.TestCase):
    def test_valid_iso_converts_to_russian(self):
        self.assertEqual(validate_date('2026-06-15'), '15 июня')
        self.assertEqual(validate_date('2026-01-01'), '1 января')
        self.assertEqual(validate_date('2026-12-31'), '31 декабря')

    def test_empty_returns_none(self):
        self.assertIsNone(validate_date(''))
        self.assertIsNone(validate_date(None))

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            validate_date('15-06-2026')
        with self.assertRaises(ValueError):
            validate_date('2026/06/15')
        with self.assertRaises(ValueError):
            validate_date('not-a-date')

    def test_logically_invalid_date_raises(self):
        with self.assertRaises(ValueError):
            validate_date('2026-02-31')  # Feb 31 doesn't exist
        with self.assertRaises(ValueError):
            validate_date('2026-13-01')  # month 13
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_race.py::TestValidateDate -v
```

- [ ] **Step 3: Implement `validate_date` in `scripts/race.py`**

```python
def validate_date(iso_str):
    """Convert ISO date string '2026-06-15' to Russian genitive '15 июня'.
    Returns None for empty input. Raises ValueError for invalid format or impossible date.
    """
    if not iso_str:
        return None
    try:
        d = datetime.date.fromisoformat(iso_str)
    except ValueError:
        raise ValueError(
            f"Неверная дата: '{iso_str}'. Ожидается ГГГГ-ММ-ДД, например 2026-06-15"
        )
    return f"{d.day} {MONTHS_GENITIVE[d.month]}"
```

- [ ] **Step 4: Run — expect PASS**

```bash
python3 -m pytest tests/test_race.py::TestValidateDate -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: add date validation ISO -> Russian genitive"
```

---

### Task 3: URL validation

**Files:**
- Modify: `scripts/race.py` — add `validate_url()`
- Modify: `tests/test_race.py` — add `TestValidateUrl`

- [ ] **Step 1: Write failing tests**

```python
from race import validate_url

class TestValidateUrl(unittest.TestCase):
    def test_valid_https(self):
        self.assertTrue(validate_url('https://example.ru'))
        self.assertTrue(validate_url('https://reg.place/events/race-2026'))

    def test_valid_http(self):
        self.assertTrue(validate_url('http://vk.com/race'))

    def test_empty_returns_none(self):
        self.assertIsNone(validate_url(''))
        self.assertIsNone(validate_url(None))

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            validate_url('not-a-url')
        with self.assertRaises(ValueError):
            validate_url('ftp://example.com')
        with self.assertRaises(ValueError):
            validate_url('example.com')
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_race.py::TestValidateUrl -v
```

- [ ] **Step 3: Implement `validate_url`**

```python
def validate_url(url_str):
    """Validate URL (http/https). Returns None for empty. Raises ValueError for invalid."""
    if not url_str:
        return None
    parsed = urllib.parse.urlparse(url_str)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValueError(
            f"Неверный URL: '{url_str}'. Ожидается https://... или http://..."
        )
    return url_str
```

- [ ] **Step 4: Run — expect PASS**

```bash
python3 -m pytest tests/test_race.py::TestValidateUrl -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: add URL validation"
```

---

### Task 4: Airtable HTTP client

**Files:**
- Modify: `scripts/race.py` — add `AirtableClient` class

No unit tests for the HTTP client itself (would require live API or complex mocking) — tested implicitly via command tests in later tasks.

- [ ] **Step 1: Add `AirtableClient` class to `scripts/race.py`**

```python
class AirtableClient:
    """Minimal Airtable REST client using urllib."""

    BASE_URL = 'https://api.airtable.com/v0'

    def __init__(self, token, base_id):
        self.token = token
        self.base_id = base_id
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def _request(self, method, path, data=None):
        url = f'{self.BASE_URL}/{self.base_id}/{urllib.parse.quote(path, safe="")}'
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"Airtable API ошибка {e.code}: {body}")
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"Сетевая ошибка: {e.reason}")
            sys.exit(1)

    def fetch_all(self, table):
        """Fetch all records from a table (handles pagination)."""
        records = []
        offset = None
        while True:
            params = {'pageSize': '100'}
            if offset:
                params['offset'] = offset
            url = (f'{self.BASE_URL}/{self.base_id}/{urllib.parse.quote(table, safe="")}'
                   f'?{urllib.parse.urlencode(params)}')
            req = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError as e:
                print(f"Airtable API ошибка {e.code}: {e.read().decode()}")
                sys.exit(1)
            records.extend(data.get('records', []))
            offset = data.get('offset')
            if not offset:
                break
        return records

    def post(self, table, fields):
        """Create a new record. Returns the created record."""
        return self._request('POST', table, {'fields': fields})

    def patch(self, table, record_id, fields):
        """Update fields of an existing record. Returns updated record."""
        url = f'{self.BASE_URL}/{self.base_id}/{urllib.parse.quote(table, safe="")}/{record_id}'
        data = json.dumps({'fields': fields}).encode()
        req = urllib.request.Request(url, data=data, headers=self.headers, method='PATCH')
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            print(f"Airtable API ошибка {e.code}: {e.read().decode()}")
            sys.exit(1)
```

- [ ] **Step 2: Run existing tests — expect still PASS**

```bash
python3 -m pytest tests/test_race.py -v
```

- [ ] **Step 3: Commit**

```bash
git add scripts/race.py
git commit -m "feat: add AirtableClient with fetch_all/post/patch"
```

---

### Task 5: Discipline/Location cache and fuzzy match

**Files:**
- Modify: `scripts/race.py` — add `Cache` class + `fuzzy_match()`
- Modify: `tests/test_race.py` — add `TestFuzzyMatch`

- [ ] **Step 1: Write failing tests**

```python
from race import fuzzy_match

class TestFuzzyMatch(unittest.TestCase):
    def setUp(self):
        # Simulates the cache structure: {name_lower: record_id}
        self.records = [
            {'id': 'rec1', 'fields': {'Discipline Name': 'Гревел'}},
            {'id': 'rec2', 'fields': {'Discipline Name': 'MTB XCM'}},
            {'id': 'rec3', 'fields': {'Discipline Name': 'MTB XCO'}},
            {'id': 'rec4', 'fields': {'Discipline Name': 'Шоссе'}},
        ]

    def test_exact_match(self):
        result = fuzzy_match('Гревел', self.records, 'Discipline Name')
        self.assertEqual(result, 'rec1')

    def test_exact_match_case_insensitive(self):
        result = fuzzy_match('гревел', self.records, 'Discipline Name')
        self.assertEqual(result, 'rec1')

    def test_single_substring_match_auto_select(self):
        result = fuzzy_match('Шоссе', self.records, 'Discipline Name')
        self.assertEqual(result, 'rec4')

    def test_no_match_returns_none(self):
        result = fuzzy_match('Триатлон', self.records, 'Discipline Name')
        self.assertIsNone(result)

    def test_multiple_substring_matches_returns_sentinel(self):
        # When multiple matches, fuzzy_match returns a special value
        # indicating the caller should prompt the user
        result = fuzzy_match('MTB', self.records, 'Discipline Name')
        # Returns list of matching records for caller to present
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_race.py::TestFuzzyMatch -v
```

- [ ] **Step 3: Implement `fuzzy_match` and `Cache` in `scripts/race.py`**

```python
def fuzzy_match(name, records, name_field):
    """Match name against records. Returns:
    - record_id (str) for exact or single substring match
    - list of matching records when multiple substring matches
    - None when no match
    """
    needle = name.strip().lower()
    # Exact match first
    for r in records:
        if r['fields'].get(name_field, '').strip().lower() == needle:
            return r['id']
    # Substring match
    matches = [r for r in records if needle in r['fields'].get(name_field, '').lower()]
    if len(matches) == 1:
        return matches[0]['id']
    if len(matches) > 1:
        return matches  # caller handles multi-match prompt
    return None


class Cache:
    """Holds discipline and location records fetched at startup."""

    def __init__(self, client):
        print("Загружаю справочники...", end=' ', flush=True)
        self.disciplines = client.fetch_all('Disciplines')
        self.locations = client.fetch_all('Locations')
        self.races = client.fetch_all('Races')
        # Normalize: some locations use City, others use Location Name — unify into Location Name
        for r in self.locations:
            if not r['fields'].get('Location Name') and r['fields'].get('City'):
                r['fields']['Location Name'] = r['fields']['City']
        print("готово.")

    def resolve_discipline(self, name, client):
        """Resolve discipline name to record ID. Returns (id, was_created)."""
        return _resolve_linked(name, self.disciplines, 'Discipline Name',
                               'Дисциплина', 'Disciplines', client, self.disciplines)

    def resolve_location(self, name, client):
        """Resolve location name to record ID. Returns (id, was_created)."""
        return _resolve_linked(name, self.locations, 'Location Name',
                               'Локация', 'Locations', client, self.locations)

    def find_race_by_name(self, name):
        """Find existing race by case-insensitive exact name match."""
        needle = name.strip().lower()
        for r in self.races:
            if r['fields'].get('Race Name', '').strip().lower() == needle:
                return r
        return None


def _resolve_linked(name, records, name_field, label, table, client, cache_list):
    """Resolve a name to an Airtable record ID with interactive prompts.
    Returns (record_id, was_created) tuple.
    """
    result = fuzzy_match(name, records, name_field)
    if isinstance(result, str):
        return result, False  # single match, not created
    if isinstance(result, list):
        # Multiple matches — prompt user to choose
        print(f"\nНайдено несколько совпадений для '{name}':")
        for i, r in enumerate(result, 1):
            print(f"  {i}. {r['fields'].get(name_field, r['id'])}")
        print("  0. Создать новую запись")
        while True:
            choice = input("Выберите номер: ").strip()
            if choice == '0':
                break
            if choice.isdigit() and 1 <= int(choice) <= len(result):
                return result[int(choice) - 1]['id'], False
            print("Неверный ввод, попробуйте снова.")
        # Fall through to create new
    # No match — ask to create
    answer = input(f"{label} '{name}' не найдена. Создать? [y/n]: ").strip().lower()
    if answer != 'y':
        return None, False
    created = client.post(table, {name_field: name})
    new_record = {'id': created['id'], 'fields': {name_field: name}}
    cache_list.append(new_record)
    print(f"Создана {label.lower()}: '{name}' ({created['id']})")
    return created['id'], True
```

- [ ] **Step 4: Run — expect PASS**

```bash
python3 -m pytest tests/test_race.py::TestFuzzyMatch -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: add fuzzy_match and Cache for discipline/location resolution"
```

---

### Task 6: `add` command

**Files:**
- Modify: `scripts/race.py` — add `cmd_add()`
- Modify: `tests/test_race.py` — add `TestCmdAdd`

- [ ] **Step 1: Write failing tests**

```python
from unittest.mock import MagicMock, patch
from race import cmd_add

class TestCmdAdd(unittest.TestCase):
    def _make_cache(self, existing_race=None):
        cache = MagicMock()
        cache.find_race_by_name.return_value = existing_race
        cache.resolve_discipline.return_value = ('recDISC1', False)
        cache.resolve_location.return_value = ('recLOC1', False)
        return cache

    def test_creates_new_race(self):
        client = MagicMock()
        client.post.return_value = {'id': 'recNEW1', 'fields': {'Race Name': 'Test Race'}}
        cache = self._make_cache(existing_race=None)

        args = MagicMock()
        args.name = 'Test Race'
        args.date = '2026-06-15'
        args.discipline = 'Гревел'
        args.location = 'Москва'
        args.link = 'https://example.ru'

        with patch('builtins.print') as mock_print:
            cmd_add(args, client, cache)

        client.post.assert_called_once()
        call_fields = client.post.call_args[0][1]
        self.assertEqual(call_fields['Race Name'], 'Test Race')
        self.assertEqual(call_fields['Date'], '15 июня')
        self.assertEqual(call_fields['Registration Link'], 'https://example.ru')
        self.assertEqual(call_fields['Discipline'], ['recDISC1'])
        self.assertEqual(call_fields['Location'], ['recLOC1'])

    def test_tbd_date_not_sent(self):
        client = MagicMock()
        client.post.return_value = {'id': 'recNEW2', 'fields': {}}
        cache = self._make_cache()

        args = MagicMock()
        args.name = 'TBD Race'
        args.date = None
        args.discipline = 'Гревел'
        args.location = 'Москва'
        args.link = None

        cmd_add(args, client, cache)

        fields = client.post.call_args[0][1]
        self.assertNotIn('Date', fields)
        self.assertNotIn('Registration Link', fields)

    def test_duplicate_skip(self):
        client = MagicMock()
        existing = {'id': 'recEXIST', 'fields': {'Race Name': 'Existing Race'}}
        cache = self._make_cache(existing_race=existing)

        args = MagicMock()
        args.name = 'Existing Race'
        args.date = None
        args.discipline = 'Гревел'
        args.location = 'Москва'
        args.link = None

        with patch('builtins.input', return_value='s'):
            cmd_add(args, client, cache)

        client.post.assert_not_called()
        client.patch.assert_not_called()

    def test_duplicate_update(self):
        client = MagicMock()
        client.patch.return_value = {'id': 'recEXIST', 'fields': {}}
        existing = {'id': 'recEXIST', 'fields': {'Race Name': 'Existing Race'}}
        cache = self._make_cache(existing_race=existing)

        args = MagicMock()
        args.name = 'Existing Race'
        args.date = '2026-08-01'
        args.discipline = 'Гревел'
        args.location = 'Москва'
        args.link = None

        with patch('builtins.input', return_value='u'):
            cmd_add(args, client, cache)

        client.patch.assert_called_once()
        self.assertEqual(client.patch.call_args[0][1], 'recEXIST')
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_race.py::TestCmdAdd -v
```

- [ ] **Step 3: Implement `cmd_add` in `scripts/race.py`**

```python
def cmd_add(args, client, cache):
    """Handle 'add' subcommand."""
    # Validate inputs
    try:
        date_str = validate_date(args.date)
        link_str = validate_url(getattr(args, 'link', None))
    except ValueError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    # Check for duplicate
    existing = cache.find_race_by_name(args.name)
    if existing:
        rec_id = existing['id']
        answer = input(f'"{args.name}" уже существует ({rec_id}). [u]pdate / [s]kip: ').strip().lower()
        if answer == 'u':
            fields = _build_fields(args.name, date_str, link_str, None, None)
            client.patch('Races', rec_id, fields)
            print(f'Обновлено: "{args.name}" ({rec_id})')
        else:
            print('Пропущено.')
        return

    # Resolve discipline and location
    disc_id, _ = cache.resolve_discipline(args.discipline, client)
    if disc_id is None:
        print('Пропущено (дисциплина не выбрана).')
        return
    loc_id, _ = cache.resolve_location(args.location, client)
    if loc_id is None:
        print('Пропущено (локация не выбрана).')
        return

    fields = _build_fields(args.name, date_str, link_str, disc_id, loc_id)
    result = client.post('Races', fields)
    print(f'Создано: "{args.name}" ({result["id"]})')
    cache.races.append(result)


def _build_fields(name, date_str, link_str, disc_id, loc_id):
    """Build Airtable fields dict, omitting None/empty values."""
    fields = {'Race Name': name}
    if date_str:
        fields['Date'] = date_str
    if link_str:
        fields['Registration Link'] = link_str
    if disc_id:
        fields['Discipline'] = [disc_id]
    if loc_id:
        fields['Location'] = [loc_id]
    return fields
```

- [ ] **Step 4: Run — expect PASS**

```bash
python3 -m pytest tests/test_race.py::TestCmdAdd -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: implement cmd_add with duplicate detection"
```

---

### Task 7: `update` command

**Files:**
- Modify: `scripts/race.py` — add `cmd_update()`
- Modify: `tests/test_race.py` — add `TestCmdUpdate`

- [ ] **Step 1: Write failing tests**

```python
from race import cmd_update

class TestCmdUpdate(unittest.TestCase):
    def test_updates_allowed_fields(self):
        client = MagicMock()
        client.patch.return_value = {'id': 'recABC', 'fields': {}}

        args = MagicMock()
        args.record_id = 'recABC'
        args.name = 'New Name'
        args.date = '2026-09-01'
        args.link = 'https://new-link.ru'

        cmd_update(args, client)

        client.patch.assert_called_once()
        fields = client.patch.call_args[0][2]
        self.assertEqual(fields['Race Name'], 'New Name')
        self.assertEqual(fields['Date'], '1 сентября')
        self.assertEqual(fields['Registration Link'], 'https://new-link.ru')

    def test_only_provided_fields_sent(self):
        client = MagicMock()
        client.patch.return_value = {'id': 'recABC', 'fields': {}}

        args = MagicMock()
        args.record_id = 'recABC'
        args.name = None
        args.date = None
        args.link = 'https://link.ru'

        cmd_update(args, client)

        fields = client.patch.call_args[0][2]
        self.assertNotIn('Race Name', fields)
        self.assertNotIn('Date', fields)
        self.assertIn('Registration Link', fields)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_race.py::TestCmdUpdate -v
```

- [ ] **Step 3: Implement `cmd_update`**

```python
def cmd_update(args, client):
    """Handle 'update' subcommand."""
    fields = {}
    try:
        if getattr(args, 'name', None):
            fields['Race Name'] = args.name
        if getattr(args, 'date', None):
            fields['Date'] = validate_date(args.date)
        if getattr(args, 'link', None):
            validate_url(args.link)
            fields['Registration Link'] = args.link
    except ValueError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    if not fields:
        print("Нет полей для обновления. Укажите --name, --date или --link.")
        sys.exit(1)

    result = client.patch('Races', args.record_id, fields)
    print(f'Обновлено: ({result["id"]})')
```

- [ ] **Step 4: Run — expect PASS**

```bash
python3 -m pytest tests/test_race.py::TestCmdUpdate -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: implement cmd_update"
```

---

### Task 8: `import` command

**Files:**
- Modify: `scripts/race.py` — add `cmd_import()`
- Modify: `tests/test_race.py` — add `TestCmdImport`

- [ ] **Step 1: Write failing tests**

```python
from race import cmd_import
import tempfile

class TestCmdImport(unittest.TestCase):
    def _write_csv(self, content):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return f.name

    def test_imports_new_races(self):
        csv_content = "name,date,discipline,location,link\nTest Race,2026-07-01,Гревел,Москва,https://example.ru\n"
        path = self._write_csv(csv_content)

        client = MagicMock()
        client.post.return_value = {'id': 'recNEW', 'fields': {'Race Name': 'Test Race'}}
        cache = MagicMock()
        cache.find_race_by_name.return_value = None
        cache.resolve_discipline.return_value = ('recD1', False)
        cache.resolve_location.return_value = ('recL1', False)

        args = MagicMock()
        args.file = path
        cmd_import(args, client, cache)

        client.post.assert_called_once()
        os.unlink(path)

    def test_skips_invalid_date(self):
        csv_content = "name,date,discipline,location,link\nBad Race,not-a-date,Гревел,Москва,\n"
        path = self._write_csv(csv_content)

        client = MagicMock()
        cache = MagicMock()
        cache.find_race_by_name.return_value = None

        args = MagicMock()
        args.file = path
        with patch('builtins.print'):
            cmd_import(args, client, cache)

        client.post.assert_not_called()
        os.unlink(path)

    def test_prints_summary(self):
        csv_content = "name,date,discipline,location,link\nRace A,,Гревел,Москва,\nRace B,,Гревел,Москва,\n"
        path = self._write_csv(csv_content)

        client = MagicMock()
        client.post.return_value = {'id': 'recX', 'fields': {}}
        cache = MagicMock()
        cache.find_race_by_name.return_value = None
        cache.resolve_discipline.return_value = ('recD1', False)
        cache.resolve_location.return_value = ('recL1', False)

        args = MagicMock()
        args.file = path
        printed = []
        with patch('builtins.print', side_effect=lambda *a: printed.append(' '.join(str(x) for x in a))):
            cmd_import(args, client, cache)

        summary = ' '.join(printed)
        self.assertIn('добавлено', summary)
        os.unlink(path)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_race.py::TestCmdImport -v
```

- [ ] **Step 3: Implement `cmd_import`**

```python
def cmd_import(args, client, cache):
    """Handle 'import' subcommand — bulk load races from CSV."""
    added = updated = skipped = created_new = 0

    with open(args.file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            name = row.get('name', '').strip()
            if not name:
                print(f"Строка {row_num}: пустое имя, пропуск.")
                skipped += 1
                continue

            # Validate date and link
            try:
                date_str = validate_date(row.get('date', '').strip() or None)
                link_str = validate_url(row.get('link', '').strip() or None)
            except ValueError as e:
                print(f"Строка {row_num} ({name}): {e} — пропуск.")
                skipped += 1
                continue

            # Check duplicate
            existing = cache.find_race_by_name(name)
            if existing:
                answer = input(f'"{name}" уже существует. [u]pdate / [s]kip: ').strip().lower()
                if answer == 'u':
                    fields = _build_fields(name, date_str, link_str, None, None)
                    client.patch('Races', existing['id'], fields)
                    updated += 1
                    print(f'  Обновлено: "{name}"')
                else:
                    skipped += 1
                    print(f'  Пропущено: "{name}"')
                continue

            # Resolve discipline and location
            disc_id, disc_new = cache.resolve_discipline(row.get('discipline', '').strip(), client)
            if disc_id is None:
                skipped += 1
                continue
            loc_id, loc_new = cache.resolve_location(row.get('location', '').strip(), client)
            if loc_id is None:
                skipped += 1
                continue

            created_new += int(disc_new) + int(loc_new)
            fields = _build_fields(name, date_str, link_str, disc_id, loc_id)
            result = client.post('Races', fields)
            cache.races.append(result)
            added += 1
            print(f'  Добавлено: "{name}" ({result["id"]})')

    print(f"\nИмпорт завершён: добавлено {added}, обновлено {updated}, "
          f"пропущено {skipped}, создано новых справочников {created_new}")
```

- [ ] **Step 4: Run — expect PASS**

```bash
python3 -m pytest tests/test_race.py::TestCmdImport -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: implement cmd_import with bulk CSV loading and summary"
```

---

### Task 9: Wire up argparse `main()`

**Files:**
- Modify: `scripts/race.py` — add `main()` with argparse and `if __name__ == '__main__'`

- [ ] **Step 1: Replace the bottom of `scripts/race.py`**

Replace the existing `if __name__ == '__main__': pass` with:

```python
def main():
    parser = argparse.ArgumentParser(
        prog='race.py',
        description='RaceDay — управление гонками в Airtable'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # add
    p_add = sub.add_parser('add', help='Добавить одну гонку')
    p_add.add_argument('--name', required=True, help='Название гонки')
    p_add.add_argument('--date', default=None, help='Дата в формате ГГГГ-ММ-ДД (необязательно)')
    p_add.add_argument('--discipline', required=True, help='Дисциплина (например: Гревел, MTB)')
    p_add.add_argument('--location', required=True, help='Город/место проведения')
    p_add.add_argument('--link', default=None, help='Ссылка на регистрацию (необязательно)')

    # update
    p_upd = sub.add_parser('update', help='Обновить существующую гонку по record ID')
    p_upd.add_argument('record_id', help='Airtable record ID (recXXXXXXXXXXXXXX)')
    p_upd.add_argument('--name', default=None)
    p_upd.add_argument('--date', default=None, help='Формат ГГГГ-ММ-ДД')
    p_upd.add_argument('--link', default=None)
    p_upd.epilog = 'Для изменения дисциплины/локации используйте Airtable UI.'

    # import
    p_imp = sub.add_parser('import', help='Bulk-импорт гонок из CSV')
    p_imp.add_argument('file', help='Путь к CSV файлу')

    args = parser.parse_args()
    cfg = load_config()
    client = AirtableClient(cfg['AIRTABLE_TOKEN_WRITE'], cfg['AIRTABLE_BASE'])

    if args.command == 'update':
        cmd_update(args, client)
    else:
        cache = Cache(client)
        if args.command == 'add':
            cmd_add(args, client, cache)
        elif args.command == 'import':
            cmd_import(args, client, cache)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run all tests — expect all PASS**

```bash
python3 -m pytest tests/test_race.py -v
```

Expected: all tests green.

- [ ] **Step 3: Smoke test — help output**

```bash
python3 scripts/race.py --help
python3 scripts/race.py add --help
python3 scripts/race.py update --help
python3 scripts/race.py import --help
```

Expected: clean help text, no errors.

- [ ] **Step 4: Commit**

```bash
git add scripts/race.py
git commit -m "feat: wire up argparse main() — script is now runnable"
```

---

### Task 10: Live smoke test + final polish

- [ ] **Step 1: Create a test CSV**

```bash
cat > /tmp/test_import.csv << 'EOF'
name,date,discipline,location,link
Тестовая гонка CLI,2026-11-01,Гревел,Москва,
EOF
```

- [ ] **Step 2: Run live add (creates real record in Airtable)**

```bash
python3 scripts/race.py add \
  --name "Тестовая гонка CLI" \
  --date 2026-11-01 \
  --discipline "Гревел" \
  --location "Москва"
```

Expected: `Создано: "Тестовая гонка CLI" (recXXXXXXXXXXXXXX)` — запишите record ID.

- [ ] **Step 3: Run update with the record ID from step 2**

```bash
python3 scripts/race.py update recXXXXXXXXXXXXXX --link "https://example.ru"
```

Expected: `Обновлено: (recXXXXXXXXXXXXXX)`

- [ ] **Step 4: Delete the test record via Airtable UI**

Открой Airtable → найди "Тестовая гонка CLI" → удали вручную.

- [ ] **Step 5: Run full test suite one last time**

```bash
python3 -m pytest tests/test_race.py -v
```

Expected: all PASSED.

- [ ] **Step 6: Final commit**

```bash
git add scripts/race.py tests/test_race.py
git commit -m "feat: complete race management CLI script"
```

---

## Quick Reference

```bash
# Одна гонка
python3 scripts/race.py add --name "..." --date 2026-06-15 --discipline "Гревел" --location "Москва" --link "https://..."

# Без даты и ссылки
python3 scripts/race.py add --name "..." --discipline "MTB" --location "Сочи"

# Обновить
python3 scripts/race.py update recXXXXXXXXXXXXXX --link "https://..."

# Bulk-импорт
python3 scripts/race.py import data/races.csv
```

CSV формат:
```
name,date,discipline,location,link
Название гонки,2026-08-10,Гревел,Барнаул,https://example.ru
Гонка без даты,,MTB,Сочи,
```
