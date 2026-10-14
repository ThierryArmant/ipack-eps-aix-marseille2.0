import unittest
from pathlib import Path
import knowledge_catalog as kc
from documentary_review import mark_excerpt, source_packets
from source_scope import select_academy

FICHE='data/ipack/courriels_aix_2026_10_14/courses_deux_fca_pdf_menu_individuel.txt'
GT='Lycée Général & Techno'

class FcaPdfTests(unittest.TestCase):
    def test_dual_question_gets_both_rules_in_both_tabs(self):
        q="Deux FCA de courses, 3 x 500 m et 3 x 1 min 30, pour des groupes différents : même PDF et deux épreuves pour le même élève ?"
        for mode in ('ipack','examens'):
            context=kc.priority_context(q,GT,mode)
            self.assertIn('réunir les deux FCA dans un même document PDF',context)
            self.assertIn('Deux épreuves du même champ ne peuvent donc pas compter',context)
            self.assertNotIn('Aix-Marseille : certificats EPS',context)

    def test_ca5_is_not_given_ca1_deposit_procedure(self):
        context=kc.priority_context('Regrouper deux FCA de course en durée et demi-fond dans un PDF ?',GT,'examens')
        self.assertNotIn('Deux FCA de demi-fond dans un PDF',context)

    def test_local_deposit_and_national_rule_have_separate_scope(self):
        doc=mark_excerpt(Path(FICHE).read_text(),path=FICHE,priority=300)
        packets=source_packets(doc)
        selected,marked=select_academy(packets,'Lyon')
        passages=[s for p in selected for s in p['passages']]
        local=next(s for s in passages if s['text'].startswith('Dans le cas décrit'))
        national=next(s for s in passages if s['text'].startswith('Au bac général'))
        self.assertEqual(local['scope']['not_confirmed_for'],'Lyon')
        self.assertNotIn('not_confirmed_for',national['scope'])

if __name__=='__main__': unittest.main()
