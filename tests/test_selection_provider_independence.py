"""La sélection documentaire doit rester indépendante du fournisseur de rédaction."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

class SelectionProviderIndependence(unittest.TestCase):
    def evaluate(self, mode, provider, secrets):
        tree = ast.parse(Path('app.py').read_text())
        assignments = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == '_orientation_active' for t in n.targets)]
        expr = next(n.value for n in assignments if isinstance(n.value, ast.BoolOp))
        return eval(compile(ast.Expression(expr), 'app.py', 'eval'),
                    {'mode': mode, '_provider_reponse': provider,
                     'st': SimpleNamespace(secrets=secrets)})

    def test_same_selection_for_both_writers_with_or_without_albert_key(self):
        for mode in ('examens', 'ipack'):
            for provider in ('openai', 'albert'):
                for key in ('', 'placeholder'):
                    with self.subTest(mode=mode, provider=provider, key=bool(key)):
                        self.assertTrue(self.evaluate(mode, provider, {'ALBERT_API_KEY': key}))

    def test_explicit_legacy_and_textes_keep_their_behavior(self):
        for provider in ('openai', 'albert'):
            self.assertFalse(self.evaluate('textes', provider, {}))
            self.assertFalse(self.evaluate('examens', provider, {'ORIENTATION_FICHES': 'legacy'}))
