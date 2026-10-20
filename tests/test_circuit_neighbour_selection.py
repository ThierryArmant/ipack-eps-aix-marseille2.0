"""Confusions de démarches : filtrage avant génération et voisins préservés."""
import unittest
from documentary_review import circuit_document_mismatch, mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

class CircuitNeighbourSelection(unittest.TestCase):
    def test_ponctuel_keeps_own_procedure_and_comparisons(self):
        source = 'Créer une mission Notation EPS CCF puis distribuer les lots dans Santorin.'
        self.assertTrue(circuit_document_mismatch('Où consulter ma convocation au ponctuel ?', source))
        self.assertFalse(circuit_document_mismatch('Comment ouvrir ma mission CCF ?', source))
        self.assertFalse(circuit_document_mismatch('CCF et ponctuel : quelles missions ?', source))
        self.assertFalse(circuit_document_mismatch('Ma convocation au ponctuel ?', 'Consulter sa convocation au ponctuel dans son espace personnel.'))

    def test_consulting_is_not_creating_ccf_missions(self):
        source = 'Créer les missions dans Imag’in et transmettre les droits à Santorin.'
        self.assertTrue(circuit_document_mismatch('Comment télécharger mon ordre de mission ?', source))
        self.assertFalse(circuit_document_mismatch('Comment créer les missions pour Santorin ?', source))
        self.assertFalse(circuit_document_mismatch('Comment éditer la convocation CCF pour Santorin ?', source))
        self.assertFalse(circuit_document_mismatch('Comment télécharger mon ordre de mission ?', 'Télécharger le document dans son espace personnel.'))

    def test_bulletin_is_not_coefficient_neutralisation(self):
        source = 'Inaptitude annuelle : le coefficient EPS est neutralisé au baccalauréat.'
        self.assertTrue(circuit_document_mismatch('Mention inapte au bulletin trimestriel : que renseigner ?', source))
        self.assertFalse(circuit_document_mismatch('Inaptitude au bac : quel coefficient ?', source))
        self.assertFalse(circuit_document_mismatch('Bulletin trimestriel et CCF : quelle différence ?', source))
        self.assertFalse(circuit_document_mismatch('Mention inapte au bulletin trimestriel ?', 'Le bulletin trimestriel et la note de certification sont distincts.'))

    def test_full_text_excluded_before_generation_even_with_generic_title(self):
        wrong = mark_excerpt('Créer les missions dans Imag’in et transmettre les droits à Santorin.', path='wrong.txt', title='Accès Imag’in')
        right = mark_excerpt('Consulter sa convocation au ponctuel dans son espace personnel.', path='right.txt', title='Convocation ponctuelle')
        llm = FakeLLM([{'claims': []}]); audit = {}
        review_exam_answer(llm, question='Comment télécharger mon ordre de mission au ponctuel ?', public='Lycée Général & Techno', mode='examens', documents=wrong+'\n'+right, audit=audit)
        self.assertIn('D1', audit['excluded_situation_documents'])
        self.assertNotIn('D2', audit['excluded_situation_documents'])
        self.assertTrue(llm.prompts)
        self.assertNotIn('Créer les missions', str(llm.prompts))
        self.assertIn('espace personnel', str(llm.prompts))
