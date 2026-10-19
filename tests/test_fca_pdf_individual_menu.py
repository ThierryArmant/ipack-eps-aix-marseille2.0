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

    def test_natural_deposit_question_gets_distinctions_without_ca5_menu_invention(self):
        q = 'peut on deposer une activite course de durée et demi fond'
        for mode in ('ipack', 'examens'):
            self.assertEqual(kc.clarification(q, GT, mode=mode), '')
            context = kc.priority_context(q, GT, mode)
            self.assertIn('Le dépôt de deux FCA dans un document a déjà été pratiqué', context)
            self.assertIn("trois champs d'apprentissage différents", context)
            self.assertIn('développement des ressources', context)
            self.assertIn("pas sur une procédure de fusion d'une FCA du CA1 et d'une FCA du CA5", context)

    def test_local_deposit_and_national_rule_have_separate_scope(self):
        doc=mark_excerpt(Path(FICHE).read_text(),path=FICHE,priority=300)
        packets=source_packets(doc)
        selected,marked=select_academy(packets,'Lyon')
        passages=[s for p in selected for s in p['passages']]
        local=next(s for s in passages if s['text'].startswith('Dans le cas décrit'))
        national=next(s for s in passages if s['text'].startswith('Au bac général'))
        self.assertEqual(local['scope']['not_confirmed_for'],'Lyon')
        self.assertNotIn('not_confirmed_for',national['scope'])
        distinction=next(s for s in passages if s['text'].startswith('Distinction des activités'))
        confirmation=next(s for s in passages if s['text'].startswith('À Aix-Marseille, le retour du modérateur'))
        self.assertEqual(distinction['scope']['nature'], ['texte_national'])
        self.assertNotIn('not_confirmed_for', distinction['scope'])
        self.assertEqual(confirmation['scope']['not_confirmed_for'], 'Lyon')

if __name__=='__main__': unittest.main()
