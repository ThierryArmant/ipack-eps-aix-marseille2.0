import unittest
from pathlib import Path
import knowledge_catalog as kc
from documentary_review import mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

GT = 'Lycée Général & Techno'

class IndependentQuestionsTests(unittest.TestCase):
    def test_grade_counts_already_described_do_not_trigger_generic_clarification(self):
        for q in (
            'Un élève présentant 2 inaptitudes totales et une note doit-il être noté en BGT ?',
            'Deux inaptitudes et une note : doit-on noter ce candidat ?',
            "Comment noter un élève qui n'est noté que sur une épreuve et dispensé sur les 2 autres en BGT ?",
        ):
            self.assertEqual(kc.clarification(q, GT), '', q)
        self.assertTrue(kc.clarification('Élève dispensé : je mets DI ?', GT))

    def test_shn_grading_uses_exam_controls_but_software_operation_stays_technical(self):
        q = "Comment noter un élève SHN qui n'a participé qu'à un seul cycle en raison de son statut ?"
        self.assertEqual(kc.effective_context(q, GT, 'ipack'), (GT, 'examens'))
        self.assertIn("ne peut être l'unique note", kc.priority_context(q, GT, 'examens'))
        self.assertEqual(kc.effective_context('Comment saisir la note SHN dans iPackEPS ?', GT, 'ipack'), (GT, 'ipack'))

    def test_same_model_two_requests_receive_only_their_current_documents(self):
        llm = FakeLLM([{'claims': []}, {'claims': []}])
        review_exam_answer(llm, question='QUESTION_PRECEDENTE_ABC', public=GT,
                           documents=mark_excerpt('DOCUMENT_PRECEDENT_ABC'))
        review_exam_answer(llm, question='QUESTION_ACTUELLE_XYZ', public=GT,
                           documents=mark_excerpt('DOCUMENT_ACTUEL_XYZ'))
        self.assertIn('QUESTION_ACTUELLE_XYZ', llm.prompts[-1])
        self.assertIn('DOCUMENT_ACTUEL_XYZ', llm.prompts[-1])
        self.assertNotIn('QUESTION_PRECEDENTE_ABC', llm.prompts[-1])
        self.assertNotIn('DOCUMENT_PRECEDENT_ABC', llm.prompts[-1])

    def test_app_never_replays_answer_cache_and_clears_display_history(self):
        source = Path('app.py').read_text()
        self.assertNotIn('ANSWER_CACHE.get', source)
        self.assertNotIn('ANSWER_CACHE.put', source)
        self.assertIn('st.session_state.messages_hub = []\n    question_affichee = prompt', source)

if __name__ == '__main__':
    unittest.main()
