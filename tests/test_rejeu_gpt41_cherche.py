import unittest
from pathlib import Path


class RejeuGpt41Cherche(unittest.TestCase):
    """Essai du 20/11/2026 : gpt-4.1 choisit les passages, Mini rédige, dans le rejeu administrateur seulement."""

    def test_moteur_propose_dans_le_rejeu(self):
        src = Path('admin_retest_113_live.py').read_text(encoding='utf-8')
        self.assertIn('"gpt41_cherche"', src)
        self.assertIn('engine == "gpt41_cherche" and not state.get("admin_faithful", True)', src)

    def test_branche_seulement_sur_le_lot_et_sans_pool(self):
        app = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('_gpt41_selection = bool(_faithful_trial and not _mixed_trial and not _albert_redige_trial', app)
        self.assertIn('and _lot_moteur in (None, "gpt41_cherche"))', app)
        self.assertIn("ModeleAvecSecours(", app)
        self.assertIn("OpenAI(model='gpt-4.1', temperature=0.0,", app)
        self.assertIn('common_pool=not (_albert_redige_trial or _gpt41_selection))', app)
        # Les collègues : gpt-4.1 cherche, Mini rédige, pas d'Albert.
        self.assertIn('_albert_redige_voulu = False', app)

    def test_secours_mini_si_gpt41_echoue(self):
        from albert_adapter import ModeleAvecSecours
        class Panne:
            model = 'gpt-4.1'
            def complete(self, prompt, **kw): raise TimeoutError('délai')
        class Mini:
            model = 'gpt-4o-mini'
            def complete(self, prompt, **kw): return 'ok'
        s = ModeleAvecSecours(Panne(), Mini())
        self.assertEqual(s.complete('x'), 'ok')
        self.assertEqual(s.fallback_reason, 'TimeoutError')
        self.assertEqual(s.resolved_model, 'gpt-4o-mini')

    def test_pas_de_secours_si_gpt41_repond(self):
        from albert_adapter import ModeleAvecSecours
        class G:
            model = 'gpt-4.1'
            def complete(self, prompt, **kw): return 'choix'
        class Mini:
            model = 'gpt-4o-mini'
            def complete(self, prompt, **kw): raise AssertionError('ne doit pas être appelé')
        s = ModeleAvecSecours(G(), Mini())
        self.assertEqual(s.complete('x'), 'choix')
        self.assertIsNone(s.fallback_reason)
