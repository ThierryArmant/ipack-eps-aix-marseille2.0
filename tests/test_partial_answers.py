import unittest
from documentary_review import review_exam_answer, mark_excerpt, NO_APPLICABLE_GUIDANCE, render_exam_fallback
from response_controls import suggested_tab
from test_documentary_review import FakeLLM


class PartialAnswersTests(unittest.TestCase):
    def test_documented_condition_without_decision_uses_one_call(self):
        doc = mark_excerpt('La note est individuelle pour chaque candidat.', title='Note collective en acrosport')
        llm = FakeLLM([{'claims': [{'section': 'condition', 'text': 'La note est individuelle pour chaque candidat.',
                                 'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}]}])
        result = review_exam_answer(llm, question='Note collective en acrosport ?', public='GT', documents=doc)
        self.assertIn('Conditions', result)
        for heading in ('Décision', 'Démarches', 'Limites et précisions'):
            self.assertNotIn(heading, result)
        self.assertEqual(len(llm.prompts), 1)

    def test_empty_answer_does_not_trigger_repair(self):
        llm = FakeLLM([{'claims': []}])
        audit = {}
        result = review_exam_answer(llm, question='Émargement obligatoire ?', public='GT',
                                   documents=mark_excerpt('Le dossier conserve les notes.'), audit=audit)
        self.assertIn(NO_APPLICABLE_GUIDANCE, result)
        self.assertEqual(audit['accepted_claims'], [])
        self.assertEqual(len(llm.prompts), 1)

    def test_collective_grading_excludes_medical_fiche_and_claim(self):
        docs = mark_excerpt('La note est individuelle.', title='Note collective', priority=300)
        docs += '\n' + mark_excerpt('Une seule note après inaptitude totale annuelle.', title='Inaptitude totale annuelle', priority=300)
        good = {'section': 'decision', 'text': 'La note est individuelle.',
                'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}
        wrong = {'section': 'condition', 'text': 'La note est individuelle sauf dispense pour inaptitude.',
                 'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}
        llm, audit = FakeLLM([{'claims': [good, wrong]}, {'claims': [good]}]), {}
        result = review_exam_answer(llm, question='Note collective en acrosport ?', public='GT', documents=docs, audit=audit)
        self.assertEqual(audit['model_document_ids'], ['D1'])
        self.assertNotIn('dispense', result)
        self.assertTrue(audit['initial_rejections'])

    def test_absence_fallback_does_not_publish_annual_inaptitude(self):
        doc = mark_excerpt('Absent CCF : inaptitude totale annuelle.', title='Inaptitude totale annuelle', priority=300)
        result = render_exam_fallback({}, question='Élève absent au CCF, comment noter ?', documents=doc)
        self.assertIn(NO_APPLICABLE_GUIDANCE, result)
        self.assertNotIn('<blockquote>', result)

    def test_tab_notice_for_bee_without_confusing_cyclades_export(self):
        self.assertEqual(suggested_tab('Synchronisation BEE : élèves importés mais pas les groupes EPS', 'examens'),
                         'Assistance Technique iPackEPS')
        self.assertEqual(suggested_tab('iPackEPS : exporter les groupes vers Cyclades', 'examens'), '')
        self.assertEqual(suggested_tab('Synchronisation BEE des groupes', 'ipack'), '')
