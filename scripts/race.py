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


def cmd_add(args, client, cache):
    """Handle 'add' subcommand."""
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
            # Only name/date/link updated on duplicate — discipline/location via Airtable UI
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


def cmd_update(args, client):
    """Handle 'update' subcommand. Supports --name, --date, --link only."""
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
                    result = client.patch('Races', existing['id'], fields)
                    # Update cached record so subsequent duplicate checks see latest state
                    existing['fields'].update(fields)
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


class AirtableClient:
    BASE_URL = 'https://api.airtable.com/v0'

    def __init__(self, token, base_id):
        self.token = token
        self.base_id = base_id
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def _do_request(self, req):
        """Execute a prepared Request, handle errors."""
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"Airtable API ошибка {e.code}: {error_body}")
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
            data = self._do_request(req)
            records.extend(data.get('records', []))
            offset = data.get('offset')
            if not offset:
                break
        return records

    def post(self, table, fields):
        """Create a new record."""
        url = f'{self.BASE_URL}/{self.base_id}/{urllib.parse.quote(table, safe="")}'
        body = json.dumps({'fields': fields}).encode()
        req = urllib.request.Request(url, data=body, headers=self.headers, method='POST')
        return self._do_request(req)

    def patch(self, table, record_id, fields):
        """Update fields of an existing record."""
        url = f'{self.BASE_URL}/{self.base_id}/{urllib.parse.quote(table, safe="")}/{record_id}'
        body = json.dumps({'fields': fields}).encode()
        req = urllib.request.Request(url, data=body, headers=self.headers, method='PATCH')
        return self._do_request(req)


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
