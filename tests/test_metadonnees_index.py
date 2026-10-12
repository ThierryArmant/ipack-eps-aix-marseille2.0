"""Les métadonnées visibles par l'index restent courtes (sinon l'index plante au démarrage :
« Metadata length … is longer than chunk size », incident du 12 octobre 2026)."""
import re
import unittest
from pathlib import Path

import knowledge_catalog as kc

CLES_VISIBLES = ('title', 'source', 'path', 'statut')


class MetadonneesIndexTests(unittest.TestCase):
    def test_app_masque_les_cles_du_catalogue_pour_l_index(self):
        src = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('excluded_embed_metadata_keys=cles_masquees', src)
        self.assertIn('excluded_llm_metadata_keys=cles_masquees', src)
        m = re.search(r"cles_masquees = \[k for k in md_morceau if k not in \(([^)]*)\)\]", src)
        self.assertIsNotNone(m)
        self.assertEqual(set(re.findall(r"'(\w+)'", m.group(1))), set(CLES_VISIBLES))

    def test_metadonnees_visibles_courtes_pour_chaque_document(self):
        for dossier in ('data/examens', 'data/ipack', 'data/textes'):
            for _, md in kc.document_records(dossier):
                visible = '\n'.join(f'{k}: {md[k]}' for k in CLES_VISIBLES if k in md)
                with self.subTest(path=md.get('path')):
                    # 1024 jetons de découpage : rester très en dessous (environ 3 caractères par jeton au pire)
                    self.assertLess(len(visible), 600)


if __name__ == '__main__':
    unittest.main()
