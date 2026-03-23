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

if __name__ == '__main__':
    unittest.main()
