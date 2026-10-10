import unittest
from response_controls import complete_gt_shn_conditions

CTX = '### Bac général et technologique : SHN et sportifs non listés MENE2531948N'

class ResponseControlsTests(unittest.TestCase):
    def test_omitted_conditions_are_completed(self):
        answer = complete_gt_shn_conditions('Bac GT EPS SHN', 'L’élève peut bénéficier d’un aménagement.', CTX)
        for word in ('justifié', 'comité de pilotage', 'validation par le recteur'):
            self.assertIn(word, answer)

    def test_complete_answer_is_not_duplicated(self):
        answer = 'Statut justifié, proposition du comité de pilotage et validation par le recteur.'
        self.assertEqual(complete_gt_shn_conditions('Bac GT SHN', answer, CTX), answer)

    def test_other_diplomas_options_errors_and_missing_source_are_preserved(self):
        answer = 'Une seule activité au CAP.'
        self.assertEqual(complete_gt_shn_conditions('CAP SHN', answer, '[PORTEE: cap]'), answer)
        self.assertEqual(complete_gt_shn_conditions('Option EPS SHN', answer, CTX), answer)
        self.assertEqual(complete_gt_shn_conditions('EPPCS SHN', answer, CTX), answer)
        self.assertEqual(complete_gt_shn_conditions('Bac GT', answer, ''), answer)
        self.assertEqual(complete_gt_shn_conditions('Bac GT', 'Erreur de traitement IA : timeout', CTX), 'Erreur de traitement IA : timeout')
