import tempfile
from pathlib import Path
import unittest
from admin_comparison_loader import load_comparison


class AdminLoaderTests(unittest.TestCase):
    def make(self, root, value):
        (root / 'albert_adapter.py').write_text('PLACEHOLDER = True')
        (root / 'confirmed_scope.py').write_text('VALUE = ' + repr(value))
        (root / 'clarification_pilot.py').write_text('from .confirmed_scope import VALUE')
        (root / 'architecture_comparison.py').write_text('from .clarification_pilot import VALUE')

    def test_changed_dependency_is_loaded_without_mutating_previous_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make(root, 'old')
            before = load_comparison(root)
            self.assertIs(before, load_comparison(root))
            self.make(root, 'new')  # même taille, modification immédiate : pas de cache mtime.
            after = load_comparison(root)
            self.assertEqual(before.VALUE, 'old')
            self.assertEqual(after.VALUE, 'new')
            self.assertIsNot(before, after)

    def test_broken_bundle_never_replaces_working_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make(root, 'good')
            before = load_comparison(root)
            (root / 'clarification_pilot.py').write_text('raise RuntimeError("invalid")')
            with self.assertRaises(RuntimeError):
                load_comparison(root)
            self.make(root, 'good')
            self.assertIs(before, load_comparison(root))
