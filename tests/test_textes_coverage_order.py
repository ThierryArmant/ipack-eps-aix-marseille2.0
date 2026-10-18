import json
from pathlib import Path
import unittest
import knowledge_catalog as kc
from hub_session import public_label
from text_inventory import domain_for

class CoverageOrderTests(unittest.TestCase):
    def test_real_public_label_is_same_search_scope(self):
        for public in ['Collège','Collège (DNB)']:
            self.assertEqual(kc.effective_context('Combien d’adultes pour une sortie ?',public,'textes')[0],'Collège (DNB)')
            self.assertTrue(kc.has_text_reference('Combien d’adultes pour une sortie ?',public))
        self.assertEqual(public_label('Collège (DNB)'),'Collège')
    def test_every_text_has_one_domain_and_registry_entry(self):
        d=json.loads(Path('config/classement_textes.json').read_text())
        files={str(p) for p in Path('data/textes').rglob('*.txt')}
        self.assertEqual(files,{r['path'] for r in d['fiches']})
        for path in files:self.assertIn(domain_for(Path(path)),d['domaines'])
    def test_common_wording_reaches_documented_subject(self):
        cases=[('Puis-je demander une marque de chaussures à mes élèves ?','Collège','neutralité'),
               ('Puis-je exclure un élève de mon cours pour oubli de tenue ?','Collège','punitions'),
               ('Je veux changer d’académie : comment faire ?','Collège','mutation'),
               ('Comment se répartissent les 108 heures ?','1er degré','108'),
               ('Quel programme EPS en CP cette année ?','1er degré','Cycle 2'),
               ('Qui autorise un voyage scolaire avec une nuitée ?','1er degré','autorisation'),
               ('Le directeur peut-il me donner des consignes ?','1er degré','autorité fonctionnelle')]
        for q,p,expected in cases:
            with self.subTest(q=q):
                self.assertTrue(kc.has_text_reference(q,p))
                self.assertIn(expected,' '.join(kc.priority_titles(q,p,'textes')))
    def test_primary_route_does_not_apply_to_secondary(self):
        q='Qui autorise un voyage scolaire avec une nuitée ?'
        self.assertNotIn('École : autorisation', ' '.join(kc.priority_titles(q,'Collège','textes')))
        self.assertNotIn('36 heures',kc.priority_context('Comment se répartissent les 108 heures ?','Collège','textes'))
    def test_disabled_duplicate_not_indexed(self):
        records=list(kc.document_records('data/textes'))
        self.assertFalse(any('_060_' in md['path'] for _,md in records))
        self.assertTrue(any('_023_' in md['path'] for _,md in records))
    def test_legacy_programs_no_longer_injects_legal_doctrine(self):
        body=Path('data/programmes_officiels_eps.txt').read_text()
        self.assertNotIn('DIRECTIVE RAG',body)
        self.assertNotIn('CONTACTS PHYSIQUES',body)
        self.assertNotIn('sécurité absolue',body)
        self.assertIn('AFLP',body)
