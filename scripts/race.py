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


if __name__ == '__main__':
    pass
