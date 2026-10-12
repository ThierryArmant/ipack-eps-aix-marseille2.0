"""Régressions : blocage institutionnel distinct d'une inaptitude individuelle."""
import unittest
import knowledge_catalog as kc


class BlocagesCCFTests(unittest.TestCase):
    def test_gt_blockage_gets_reviewed_response_in_both_modes(self):
        for mode in ('examens', 'ipack'):
            answer, source = kc.documented_response('Lycée bloqué : peut-on rattraper le CCF1 en fin d’année ?', 'Lycée Général & Techno', mode)
            self.assertIn('chef d\'établissement reconnaît la force majeure', answer)
            self.assertIn('formation effective', answer)
            self.assertIn('MENE2531948N', answer)
            self.assertNotIn('MENE2505383C', answer)

    def test_pro_has_own_exceptional_conditions(self):
        answer, _ = kc.documented_response('Bac professionnel : blocage du lycée et CCF annulé', 'Lycée Pro / CAP', 'examens')
        self.assertIn('MENE2505383C', answer)
        self.assertIn('situation extrême', answer)
        self.assertNotIn('MENE2531948N', answer)

    def test_blockage_does_not_override_medical_or_software_questions(self):
        for question in ('Santorin : lot bloqué, déverrouillage des notes CCF ?', 'Élève inapte : rattrapage CCF', 'DNB collège fermé : moyenne EPS ?'):
            answer, source = kc.documented_response(question, 'Collège (DNB)', 'examens')
            self.assertNotIn('blocages_lycees', source.get('title', ''))
            self.assertFalse(answer.startswith('Un blocage du lycée'))

    def test_gt_response_does_not_import_pro_one_activity_exception(self):
        answer, _ = kc.documented_response('Blocus du lycée : une seule note EPS suffit au bac général ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('Aucun automatisme de note unique', answer)
        self.assertNotIn('situation extrême', answer)
