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


if __name__ == '__main__':
    pass
