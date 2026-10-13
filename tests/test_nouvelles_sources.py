import unittest
from pathlib import Path
from source_scope import scoped_segments, select_academy, evidence_label

class NouvellesSourcesTests(unittest.TestCase):
    def test_assistance_cannot_be_promoted_to_national_rule(self):
        p='data/ipack/courriels_aix_2026_10_13/classe_apprentis_absente.txt'
        spans=scoped_segments(p,Path(p).read_text())
        self.assertTrue(spans)
        self.assertTrue(all(s['scope']['level']=='assistance' for s in spans))
        label=evidence_label({'scope':spans[0]['scope']},{'title':'Import'},{'assistance':'Retour d’assistance'})
        self.assertIn('Retour d’assistance',label)
        self.assertIn('8 et 9 octobre',label)

    def test_regional_source_applies_to_both_academies_only(self):
        p='data/examens/apprentissage_paca_2026_10_13/cfa_porteur_ufa.txt'
        spans=scoped_segments(p,Path(p).read_text())
        for i, span in enumerate(spans): span['id']=f'D1P{i+1}'
        for academy in ('Aix-Marseille','Nice'):
            _,marked=select_academy([{'id':'D1','passages':spans}],academy)
            self.assertFalse(marked)
        chosen,marked=select_academy([{'id':'D1','passages':spans}],'Lyon')
        self.assertTrue(marked)
        self.assertEqual(chosen[0]['passages'][0]['scope']['not_confirmed_for'],'Lyon')

    def test_unresolved_ticket_remains_explicit(self):
        text=Path('data/ipack/courriels_aix_2026_10_13/centres_etrangers_blocage_non_resolu.txt').read_text()
        self.assertIn('erreur persiste',text)
        self.assertIn('résolution du ticket n’est pas fournie',text)
        self.assertNotIn('@',text)

if __name__=='__main__': unittest.main()
