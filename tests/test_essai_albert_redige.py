import inspect
import unittest
from pathlib import Path
import exact_source_answer as esa


class EssaiAlbertRedige(unittest.TestCase):
    def test_exact_answer_accepte_un_selecteur_sans_pool(self):
        self.assertIn('common_pool', inspect.signature(esa.exact_answer).parameters)
        self.assertIn('if selector_llm is not None and common_pool:', Path('exact_source_answer.py').read_text(encoding='utf-8'))

    def test_case_admin_decochee_par_defaut_et_branchee(self):
        # Depuis le 20/11/2026 : Mini seul pour les collègues ; l'admin voit la même chose par défaut.
        app = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('value=False,\n                    key="admin_albert_redige"', app)
        self.assertIn('common_pool=not _albert_redige_trial', app)
        self.assertIn("'albert_redige_trial': _albert_redige_trial", app)

    def test_collegues_mode_documente_mini_seul_albert_en_essai(self):
        app = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('and (not _is_admin or st.session_state.get("admin_faithful", True)))', app)
        self.assertIn('_mixed_trial = (_is_admin and', app)
        # Collègues : Mini rédige (20/11/2026) ; Albert reste disponible pour l'essai admin et le rejeu.
        self.assertIn('_albert_redige_voulu = False', app)
        self.assertNotIn('_albert_redige_voulu = True', app)
        self.assertIn('AlbertWithFallback(_albert_redacteur, Settings.llm)', app)
