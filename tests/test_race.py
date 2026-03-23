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

if __name__ == '__main__':
    unittest.main()
