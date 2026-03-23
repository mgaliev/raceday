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
        with self.assertRaises(SystemExit) as cm:
            load_config('/nonexistent/secrets.local')
        self.assertEqual(cm.exception.code, 1)

    def test_value_with_equals_sign(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.local', delete=False) as f:
            f.write("TOKEN=abc=def==\n")
            path = f.name
        try:
            cfg = load_config(path)
            self.assertEqual(cfg['TOKEN'], 'abc=def==')
        finally:
            os.unlink(path)

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

from race import fuzzy_match

class TestFuzzyMatch(unittest.TestCase):
    def setUp(self):
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

    def test_multiple_substring_matches_returns_list(self):
        result = fuzzy_match('MTB', self.records, 'Discipline Name')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

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

        with patch('builtins.print'):
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

        with patch('builtins.print'):
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

        with patch('builtins.input', return_value='u'), patch('builtins.print'):
            cmd_add(args, client, cache)

        client.patch.assert_called_once()
        self.assertEqual(client.patch.call_args[0][1], 'recEXIST')
        fields = client.patch.call_args[0][2]
        self.assertEqual(fields['Race Name'], 'Existing Race')
        self.assertEqual(fields['Date'], '1 августа')
        self.assertNotIn('Discipline', fields)
        self.assertNotIn('Location', fields)

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
        with patch('builtins.print'):
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
        self.assertIn('2', summary)
        os.unlink(path)

    def test_created_new_counter(self):
        csv_content = "name,date,discipline,location,link\nNew Race,,Гревел,НовыйГород,\n"
        path = self._write_csv(csv_content)

        client = MagicMock()
        client.post.return_value = {'id': 'recX', 'fields': {}}
        cache = MagicMock()
        cache.find_race_by_name.return_value = None
        cache.resolve_discipline.return_value = ('recD1', False)
        cache.resolve_location.return_value = ('recL1', True)  # location was created

        args = MagicMock()
        args.file = path
        printed = []
        with patch('builtins.print', side_effect=lambda *a: printed.append(' '.join(str(x) for x in a))):
            cmd_import(args, client, cache)

        summary = ' '.join(printed)
        self.assertIn('создано новых справочников 1', summary)
        os.unlink(path)


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

        with patch('builtins.print'):
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

        with patch('builtins.print'):
            cmd_update(args, client)

        fields = client.patch.call_args[0][2]
        self.assertNotIn('Race Name', fields)
        self.assertNotIn('Date', fields)
        self.assertIn('Registration Link', fields)

    def test_no_fields_exits(self):
        client = MagicMock()
        args = MagicMock()
        args.record_id = 'recABC'
        args.name = None
        args.date = None
        args.link = None

        with self.assertRaises(SystemExit):
            cmd_update(args, client)


if __name__ == '__main__':
    unittest.main()
