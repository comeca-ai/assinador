import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('backup', Path(__file__).resolve().parents[1] / 'scripts/backup.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Backup(unittest.TestCase):
    def test_recover_document_and_preserve_previous_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.sqlite3'
            target = Path(folder) / 'backup.sqlite3'
            with sqlite3.connect(source) as c:
                c.execute('CREATE TABLE documents(id TEXT, pdf BLOB)')
                c.execute('INSERT INTO documents VALUES(?,?)', ('document', b'%PDF-example'))
            module.backup(source, target)
            with sqlite3.connect(target) as c:
                self.assertEqual(c.execute('SELECT * FROM documents').fetchone(), ('document', b'%PDF-example'))
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            original = target.read_bytes()
            with self.assertRaises(FileExistsError): module.backup(source, target)
            self.assertEqual(target.read_bytes(), original)
            with self.assertRaises(ValueError): module.backup(source, source)
