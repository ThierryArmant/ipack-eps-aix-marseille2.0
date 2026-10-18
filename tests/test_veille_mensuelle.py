import tempfile
import unittest
from pathlib import Path

import veille_mensuelle as v


class VeilleMensuelleTests(unittest.TestCase):
    def test_sans_rapport(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(v.dernier_rapport(d))
        titre, phrase = v.texte_bandeau(None)
        self.assertIn('1er novembre', phrase)

    def test_dernier_rapport_et_bandeau(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, '2026-11.md').write_text('# Veille mensuelle 2026-11\nPassage : 01/11/2026 · Textes nouveaux : 0 (état de référence)\n', encoding='utf-8')
            Path(d, '2026-12.md').write_text('# Veille mensuelle 2026-12\nPassage : 01/12/2026 · Textes nouveaux : 2\n## Textes nouveaux\n- [Note de service EPS](https://www.education.gouv.fr/bo/x) — 20/11/2026\n- [Ressource Éduscol](https://eduscol.education.fr/y) — 25/11/2026\n', encoding='utf-8')
            Path(d, 'README.md').write_text('x', encoding='utf-8')
            r = v.dernier_rapport(d)
        self.assertEqual(r['mois'], '2026-12'); self.assertEqual(r['nouveaux'], 2); self.assertEqual(len(r['titres']), 2)
        self.assertTrue(r['url'].endswith('docs/veille/2026-12.md'))
        titre, phrase = v.texte_bandeau(r)
        self.assertIn('01/12/2026', titre); self.assertIn('2 textes nouveaux', phrase)

    def test_reference_et_aucun(self):
        ref = {'passage': '01/11/2026', 'reference': True, 'nouveaux': 0}
        self.assertIn('référence', v.texte_bandeau(ref)[1])
        zero = {'passage': '01/12/2026', 'reference': False, 'nouveaux': 0}
        self.assertIn('Aucun texte nouveau', v.texte_bandeau(zero)[1])

    def test_app_ne_lance_plus_la_recherche_tavily(self):
        src = Path('app.py').read_text(encoding='utf-8')
        self.assertNotIn('verifier_veille_dec(tavily_client)', src)
        self.assertIn('from veille_mensuelle import dernier_rapport, texte_bandeau', src)


if __name__ == '__main__':
    unittest.main()
