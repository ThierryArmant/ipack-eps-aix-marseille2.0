import unittest
from documentary_review import lycee_dnb_mismatch
from admin_comparison_loader import load_comparison

class ScopeBoundaryTests(unittest.TestCase):
    def test_college_submission_cannot_explain_lycee_certification(self):
        packet={'origin':'document','title':'[SITUATION: COLLÈGE — ENVOYER LE DOSSIER EPS POUR VALIDATION]',
                'text':'Le dossier EPS peut être soumis ; état en attente de validation.'}
        self.assertTrue(lycee_dnb_mismatch('Soumettre notre protocole certificatif', 'Lycée Général & Techno',packet))
        self.assertFalse(lycee_dnb_mismatch('Soumettre notre dossier EPS','Collège (DNB)',packet))
        self.assertFalse(lycee_dnb_mismatch('Comparer collège et lycée','Lycée Général & Techno',packet))
        packet['title']='Soumettre le Dossier Certificatif de lycée'
        self.assertFalse(lycee_dnb_mismatch('Soumettre notre protocole certificatif','Lycée Général & Techno',packet))
    def test_live_bundle_exposes_public_factory_and_preserves_private_comparator(self):
        bundle=load_comparison()
        self.assertTrue(callable(bundle.generation_llm))
        self.assertTrue(callable(bundle.run_comparison))
        self.assertTrue(bundle.AlbertLLM.__module__.startswith('_eps_admin_comparison_'))
