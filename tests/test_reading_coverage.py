"""La grille relie les demandes aux réponses et conserve les preuves retenues.

Cela vérifie la structure, pas l'exhaustivité sémantique de la lecture du modèle.
"""
import unittest
from documentary_review import coverage_errors, mark_excerpt, source_packets, review_exam_answer
from test_documentary_review import FakeLLM


class ReadingCoverageTests(unittest.TestCase):
    def setUp(self):
        self.documents = mark_excerpt(
            'Le responsable autorise l’opération après vérification du dispositif.\n\n'
            'Le contrôle est conservé dans le registre.')
        self.packets = source_packets(self.documents)
        self.data = {'coverage': [{
            'request': 'Qui autorise et quelle trace conserver ?', 'status': 'answered',
            'claim_indices': [0, 1],
            'required_passages': [{'document_id': 'D1', 'passage_ids': ['D1P1', 'D1P2']}]}],
            'claims': [
                {'section': 'decision', 'text': 'Le responsable autorise après vérification du dispositif.',
                 'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]},
                {'section': 'etape', 'text': 'Conserver le contrôle dans le registre.',
                 'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P2']}]}]}

    def test_complementary_proofs_are_preserved_without_second_call(self):
        audit = {}; llm = FakeLLM([self.data])
        result = review_exam_answer(llm, question='Qui autorise et quelle trace conserver ?',
                                   public='Collège', documents=self.documents, mode='textes',
                                   require_coverage=True, audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertIn('registre', result)
        self.assertEqual(audit['coverage'], self.data['coverage'])

    def test_selected_condition_cannot_disappear_from_response_proofs(self):
        self.data['claims'][1]['evidence'][0]['passage_ids'] = ['D1P1']
        errors = coverage_errors(self.data, self.packets)
        self.assertIn('condition lue puis perdue', str(errors))

    def test_indices_are_checked_against_original_claims(self):
        self.data['coverage'][0]['claim_indices'] = [2]
        self.assertTrue(coverage_errors(self.data, self.packets))
        self.data['coverage'][0]['claim_indices'] = [True]
        self.assertTrue(coverage_errors(self.data, self.packets))

    def test_missing_documentation_is_explicit_not_a_supported_decision(self):
        self.data['coverage'][0].update(status='not_documented', required_passages=[])
        self.assertIn('limite', str(coverage_errors(self.data, self.packets)))
        self.data['claims'][0]['section'] = 'limite'
        self.assertFalse(coverage_errors(self.data, self.packets))

    def test_unknown_passage_or_unmapped_claim_is_rejected(self):
        self.data['coverage'][0]['required_passages'][0]['passage_ids'] = ['D1P999']
        self.assertIn('inconnu', str(coverage_errors(self.data, self.packets)))
        self.data['coverage'][0]['required_passages'][0]['passage_ids'] = ['D1P1']
        self.data['coverage'][0]['claim_indices'] = [0]
        self.assertIn('sans lien', str(coverage_errors(self.data, self.packets)))

    def test_empty_response_retains_safe_fallback(self):
        self.assertFalse(coverage_errors({'claims': []}, self.packets))

    def test_invalid_grid_gets_one_repair_and_is_never_displayed(self):
        llm = FakeLLM([{'claims': self.data['claims']}, self.data])
        result = review_exam_answer(llm, question='Qui autorise et quelle trace conserver ?',
                                   public='Collège', documents=self.documents,
                                   require_coverage=True)
        self.assertEqual(len(llm.prompts), 2)
        self.assertIn('Réécris les affirmations rejetées', llm.prompts[-1])
        self.assertIn('registre', result)


if __name__ == '__main__':
    unittest.main()
