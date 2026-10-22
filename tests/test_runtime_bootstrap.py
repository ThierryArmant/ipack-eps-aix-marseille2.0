import tempfile
import unittest
from pathlib import Path
from runtime_bootstrap import load_runtime

class BootstrapTests(unittest.TestCase):
    def test_loader_changes_do_not_use_cached_previous_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'generation_runtime.py'
            p.write_text('def load_runtime(root): return "old"')
            self.assertEqual(load_runtime(root),'old')
            p.write_text('def load_runtime(root): return "new"')
            self.assertEqual(load_runtime(root),'new')

    def test_default_runtime_contains_selector(self):
        self.assertTrue(callable(load_runtime().document_selector.select_documents))
