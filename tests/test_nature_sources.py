import json
import unittest
from pathlib import Path


class NatureSourcesTests(unittest.TestCase):
    """Étiquettes de nature de source fournies au programme (l'IA ne les choisit pas)."""

    def setUp(self):
        self.d = json.loads(Path('config/nature_sources.json').read_text(encoding='utf-8'))['fichiers']

    def test_valeurs_autorisees_et_fichiers_existants(self):
        for f, v in self.d.items():
            self.assertTrue(Path(f).is_file(), f)
            self.assertTrue(set(v['nature']) <= {'texte_national', 'consigne_academique', 'logiciel', 'a_verifier'}, f)

    def test_exemples(self):
        self.assertIn('logiciel', self.d['data/examens/audit_faq_2026_10_12/j2_procedure_verifiee.txt']['nature'])
        self.assertNotIn('texte_national', self.d['data/examens/audit_faq_2026_10_12/j2_procedure_verifiee.txt']['nature'])
        self.assertIn('texte_national', self.d['data/examens/audit_faq_2026_10_12/d3_procedure_verifiee.txt']['nature'])
        self.assertEqual(self.d['data/commun/audit60/aix_protocoles_2026.txt']['academie'], 'aix-marseille')


if __name__ == '__main__':
    unittest.main()
