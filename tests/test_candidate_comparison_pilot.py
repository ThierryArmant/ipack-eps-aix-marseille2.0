"""Le pilote compare les candidats déjà retrouvés, sans neutraliser les gardes."""
import unittest
from documentary_review import review_exam_answer, mark_excerpt
from test_documentary_review import FakeLLM

class CandidateComparisonPilot(unittest.TestCase):
    def run_policy(self,policy=None,documents=None,question='Comment obtenir un accès au dossier partagé ?'):
        documents=documents or (mark_excerpt('Le dossier de gestion est alimenté par les services.',path='gestion.txt',title='Gestion des dossiers',priority=300,selection='catalogue')+'\n'+mark_excerpt('Pour obtenir un accès au dossier partagé, contacter son gestionnaire.',path='acces.txt',title='Comptes et habilitations'))
        llm=FakeLLM([{'claims':[]}]);audit={};args={} if policy is None else {'selection_policy':policy}
        review_exam_answer(llm,question=question,public='Lycée Général & Techno',mode='ipack',documents=documents,audit=audit,**args)
        return audit,llm
    def test_default_preserves_legacy_and_pilot_retains_alternative(self):
        default,_=self.run_policy();explicit,_=self.run_policy('legacy')
        self.assertEqual(default['model_document_ids'],explicit['model_document_ids'])
        self.assertNotIn('D2',default['model_document_ids'])
        pilot,llm=self.run_policy('compare_candidates')
        self.assertIn('D2',pilot['model_document_ids'])
        self.assertEqual(len(llm.prompts),1)
        self.assertIn('retrieval_profile',str(llm.prompts))
        self.assertIn('ne prouvent ni l’applicabilité',str(llm.prompts))
    def test_domain_exclusion_still_applies_before_comparison(self):
        docs=mark_excerpt('Le maximum de service dépend du corps.',path='data/textes/complement_obligations_service_eps.txt',title='Obligations de service',priority=320,selection='catalogue')+'\n'+mark_excerpt('Revenir au choix des établissements pour vérifier les accès.',path='acces.txt',title='Accès')
        audit,_=self.run_policy('compare_candidates',docs,'Mon accès au second lycée est bloqué.')
        self.assertIn('D1',audit['excluded_situation_documents'])
        self.assertNotIn('D1',audit['model_document_ids'])
    def test_oversize_falls_back_without_partial_source_truncation(self):
        docs=mark_excerpt('Gestion documentaire. '*1000,path='long.txt',title='Gestion',priority=300,selection='catalogue')
        audit,_=self.run_policy('compare_candidates',docs)
        self.assertTrue(audit['candidate_comparison_fallback'])
        self.assertEqual(audit['effective_selection_policy'],'legacy')
    def test_unknown_policy_is_not_silently_activated(self):
        with self.assertRaises(ValueError):self.run_policy('unknown')
