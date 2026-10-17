import unittest
from academie import academy_context, AIX
from documentary_review import render_claims, review_exam_answer, mark_excerpt
from test_documentary_review import FakeLLM


class AcademyContextTests(unittest.TestCase):
    def test_declared_academy_overrides_menu_without_using_examples(self):
        cases = [('Je suis à Lyon : comment valider mon dossier ?', 'Lyon'),
                 ("J’enseigne dans l’académie de Creteil, mais le guide est celui d’Aix-Marseille", 'Créteil'),
                 ('Nous sommes à Nice.', 'Nice'),
                 ('Mon académie est Nancy-Metz.', 'Nancy-Metz'),
                 ('Académie de Lyon : validation des protocoles ?', 'Lyon')]
        for q, expected in cases:
            with self.subTest(q=q):
                effective, notice = academy_context(q, AIX)
                self.assertEqual(effective, expected)
                self.assertIn(expected, notice)
        for q in ('Le guide de Lyon est-il applicable ?', 'Comparer Lyon et Nice',
                  'Je ne suis pas à Lyon', 'Je suis à Lyon et nous sommes à Nice'):
            self.assertEqual(academy_context(q, AIX), (AIX, ''))
        self.assertEqual(academy_context('Je suis à Lyon', 'Lyon'), ('Lyon', ''))

    def test_scope_is_written_in_sentence_for_all_or_some_local_evidence(self):
        marked = {'document_id': 'D1', 'scope': {'academy': AIX, 'not_confirmed_for': 'Lyon'}}
        national = {'document_id': 'D1', 'scope': {'level': 'reglementaire'}}
        packets = [{'id': 'D1', 'title': 'Guide', 'display_level': 'academique'}]
        for evidence, expected_prefix in (([marked], True), ([marked, national], False), ([national], False)):
            result = render_claims([{'section': 'decision', 'text': 'Le chef valide le dossier.', 'evidence': evidence}], packets)
            self.assertNotIn('<p>À Aix-Marseille,', result)
            self.assertEqual('ne sont pas confirmées pour Lyon' in result, marked in evidence)
            self.assertIn('Le chef valide le dossier.', result)

    def test_ordinary_group_note_cannot_use_single_medical_note_evidence(self):
        docs = mark_excerpt('La note unique peut être conservée après inaptitude.', title='Note unique')
        docs += '\n' + mark_excerpt('Chaque candidat reçoit une note individuelle pour le groupe.', title='Notation de groupe')
        wrong = {'section': 'decision', 'text': 'La même note peut être conservée pour le groupe.',
                 'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}
        good = {'section': 'decision', 'text': 'Chaque candidat reçoit une note individuelle pour le groupe.',
                'evidence': [{'document_id': 'D2', 'passage_ids': ['D2P1']}]}
        llm, audit = FakeLLM([{'claims': [wrong]}, {'claims': [good]}]), {}
        result = review_exam_answer(llm, question='Peut-on mettre la même note à tout le groupe ?',
                                   public='GT', documents=docs, audit=audit)
        self.assertNotIn('peut être conservée', result)
        self.assertIn('note individuelle', result)
        self.assertTrue(audit['initial_rejections'])

    def test_group_rule_not_rejected_for_ne_dispense_pas(self):
        doc = mark_excerpt('Une partie commune au groupe ne dispense pas de donner une note à chacun.', title='Notation collective')
        claim = {'section': 'decision', 'text': 'Une partie commune au groupe ne dispense pas de donner une note à chacun.',
                 'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}
        result = review_exam_answer(FakeLLM([{'claims': [claim]}]), question='Même note pour tout le groupe ?', public='GT', documents=doc)
        self.assertIn('note à chacun', result)
