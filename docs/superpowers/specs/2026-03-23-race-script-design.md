# Race Script Design

**Date:** 2026-03-23
**Project:** RaceDay — MVP Календарь велогонок
**File:** `scripts/race.py`

## Goal

CLI-скрипт для добавления и обновления гонок в Airtable без использования Claude Code (экономия токенов). Поддерживает одиночный ввод через аргументы и bulk-импорт из CSV.

## Architecture

Один файл `scripts/race.py`. Только stdlib Python (urllib, csv, json, argparse). Зависимости не нужны.

Читает токен и Base ID из `secrets.local` в корне проекта (формат `KEY=VALUE`).

При запуске фетчит все записи из таблиц `Disciplines` и `Locations` один раз — кэш используется для fuzzy-match и экономии API-запросов.

## Commands

```bash
# Добавить одну гонку
python3 scripts/race.py add --name "Gravel Race" --date 2026-06-15 --discipline "Гревел" --location "Москва" --link "https://example.ru"

# Добавить без даты и ссылки (TBD)
python3 scripts/race.py add --name "Осенний МТБ" --discipline "MTB" --location "Сочи"

# Обновить существующую запись
python3 scripts/race.py update recXXXXXXXXXXXXXX --link "https://reg.ru/..."

# Bulk-импорт из CSV
python3 scripts/race.py import data/races.csv
```

## Fields

| Поле | CLI-аргумент | Обязательное | Тип в Airtable |
|------|-------------|--------------|----------------|
| Race Name | `--name` | да | string |
| Date | `--date` | нет | string ("15 июня") |
| Discipline | `--discipline` | да | multipleRecordLinks |
| Location | `--location` | да | multipleRecordLinks |
| Registration Link | `--link` | нет | string (URL) |

## Validation

**Дата (`--date`):**
- Принимается в ISO-формате: `2026-06-15`
- Конвертируется в русский родительный падеж: `"15 июня"`
- Пустое значение допустимо → дата TBD (поле не заполняется в Airtable)
- Невалидный формат → ошибка с подсказкой: `Ожидается ГГГГ-ММ-ДД, например 2026-06-15`

**Ссылка (`--link`):**
- Проверяется через `urllib.parse.urlparse`: схема http/https, наличие netloc
- Пустое значение допустимо → поле не заполняется, на лендинге показывается "Скоро"
- Невалидный URL → ошибка с примером

## Discipline / Location Resolution

1. Fuzzy-match по имени (case-insensitive, strip):
   - Сначала точное совпадение (lowercase)
   - Затем substring-match
   - Если substring-match даёт **один результат** → выбирается автоматически без подтверждения
   - Если substring-match даёт **несколько результатов** → выводить нумерованный список для выбора:
     ```
     Найдено несколько совпадений для "MTB":
       1. MTB XCM
       2. MTB XCO
       3. MTB Гонка в гору
     Выберите номер (или 0 для создания нового):
     ```
2. Если совпадений нет → интерактивный вопрос:
   ```
   Дисциплина "Трэкинг" не найдена. Создать? [y/n]:
   ```
3. `y` → POST новой записи в соответствующую таблицу, получить record ID
4. `n` → текущая гонка пропускается (в bulk — продолжает со следующей)

## Duplicate Detection

**Для `add`:** перед созданием скрипт проверяет существующие записи на case-insensitive exact match по `Race Name`. При совпадении:
```
"Gravel Race Алтай" уже существует (recXXX). [u]pdate / [s]kip:
```
При `u` — PATCH существующей записи с переданными полями. При `s` — выход без изменений.

**Для bulk import:** аналогично, но продолжает обработку следующих строк после [s]kip.

**Алгоритм сравнения:** `name.strip().lower()` — точное совпадение после нормализации.

## Commands Detail

**`add`:** создаёт запись, после успеха выводит:
```
Создано: "Gravel Race Алтай" (recXXXXXXXXXXXXXX)
```
Этот record ID используется для последующего `update`.

**`update <record_id>`:** поддерживает изменение следующих полей: `--name`, `--date`, `--link`. Поля `--discipline` и `--location` командой `update` не поддерживаются (изменить через Airtable UI). Это явное ограничение, прописанное в `--help`.

Если record ID не известен — использовать `add` с тем же именем: скрипт найдёт дубликат и предложит обновить.

## Bulk Import (CSV)

Формат файла:
```csv
name,date,discipline,location,link
Gravel Race Алтай,2026-08-10,Гревел,Барнаул,https://example.ru
Осенний МТБ,,MTB,Сочи,
```

Поведение:
Файл читается через `csv.DictReader` (первая строка — заголовки; корректно обрабатывает запятые внутри кавычек: `"Марафон, Казань"`).

1. Читает построчно, валидирует каждую строку перед отправкой
2. Если гонка с таким `name` уже существует в Airtable → спрашивает:
   ```
   "Gravel Race Алтай" уже существует. [u]pdate / [s]kip:
   ```
3. При новых discipline/location — пауза с подтверждением (как для одиночного add)
4. Ошибки валидации в строке — выводит предупреждение, пропускает строку, продолжает

Итоговая сводка после импорта:
```
Импорт завершён: добавлено 12, обновлено 2, пропущено 1, создано новых локаций 1
```

## Error Handling

- `secrets.local` не найден → понятное сообщение с путём к файлу
- Airtable API вернул ошибку → вывод статуса и тела ответа
- Сетевая ошибка → вывод исключения

## Out of Scope

- Удаление записей (не нужно для MVP)
- Создание новых таблиц
- Работа с несколькими Base ID
- GUI / web-интерфейс
