import unittest
import knowledge_catalog as kc
from documentary_review import situation_mismatch
from source_scope import select_academy


class SssCampaignIntentTests(unittest.TestCase):
    def test_ambiguous_wishes_ask_for_request_type(self):
        result = kc.clarification('Dans iPackEPS, comment préparer les vœux pour une section sportive scolaire ?', 'Collège (DNB)')
        for word in ('ouverture', 'reconduction', 'fermeture', 'académie'):
            self.assertIn(word, result)

    def test_explicit_renewal_gets_evolution_document(self):
        q = 'Dans iPackEPS, préparer les vœux de reconduction de ma section sportive'
        self.assertEqual(kc.clarification(q, 'Collège (DNB)'), '')
        context = kc.priority_context(q, 'Collège (DNB)', 'ipack')
        self.assertIn('[Évolution]', context)
        self.assertIn('pièces complémentaires', context)

    def test_campaign_does_not_assume_group_setup(self):
        q = 'Comment préparer les vœux SSS ?'
        text = 'Créez les groupes SSS et placez les élèves dans les groupes.'
        self.assertTrue(situation_mismatch(q, text))
        self.assertFalse(situation_mismatch('Comment créer les groupes SSS et placer les élèves ?', text))

    def test_local_calendar_scope_is_preserved(self):
        p = {'id':'D1', 'passages':[{'id':'P1', 'text':'Date de campagne', 'scope':{'nature':['consigne_academique'], 'academy':'Aix-Marseille'}}]}
        selected, marked = select_academy([p], 'Versailles')
        self.assertTrue(marked)
        self.assertEqual(selected[0]['passages'][0]['scope']['not_confirmed_for'], 'Versailles')
