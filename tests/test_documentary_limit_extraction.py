"""Limite documentaire littérale : économiser une réparation, jamais sa preuve."""
import unittest
from documentary_review import mark_excerpt, review_exam_answer, source_limits_for_rejections, source_packets
from test_documentary_review import FakeLLM

PROOF = "Aucun texte de la base n'interdit ni n'organise la publication du résultat provisoire. Faire confirmer la consigne par le service compétent."
QUESTION = 'La publication du résultat provisoire est-elle interdite ?'
FALSE = "Il n'existe pas de règle écrite interdisant la publication du résultat provisoire."


def proposal(text=FALSE, document='D1'):
    return {'claims': [{'section': 'decision', 'text': text,
                        'evidence': [{'document_id': document, 'quote': PROOF}]}]}


class DocumentaryLimitExtractionTests(unittest.TestCase):
    def test_false_certainty_replaced_only_by_literal_source_without_second_call(self):
        llm, audit = FakeLLM([proposal()]), {}
        answer = review_exam_answer(llm, question=QUESTION, public='GT',
            documents=mark_excerpt(PROOF, title='Publication du résultat provisoire'), audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertTrue(audit['documentary_limit_extraction'])
        self.assertFalse(audit['repair_performed'])
        self.assertEqual(len(audit['initial_rejections']), 1)
        self.assertEqual(audit['final_rejections'], [])
        self.assertEqual(audit['accepted_claims'][0]['text'], PROOF)
        self.assertNotIn(FALSE, answer)
        self.assertIn('Références', answer)

    def test_correct_literal_limit_is_accepted_on_first_pass(self):
        llm, audit = FakeLLM([proposal(PROOF)]), {}
        review_exam_answer(llm, question=QUESTION, public='GT',
            documents=mark_excerpt(PROOF, title='Publication du résultat provisoire'), audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertFalse(audit['documentary_limit_extraction'])
        self.assertEqual(audit['initial_rejections'], [])

    def test_unknown_source_keeps_normal_repair(self):
        llm, audit = FakeLLM([proposal(document='D99'), {'claims': []}]), {}
        review_exam_answer(llm, question=QUESTION, public='GT',
            documents=mark_excerpt(PROOF, title='Publication du résultat provisoire'), audit=audit)
        self.assertEqual(len(llm.prompts), 2)
        self.assertFalse(audit['documentary_limit_extraction'])

    def test_other_error_never_uses_shortcut(self):
        rejection = {'claim': proposal()['claims'][0],
                     'errors': ['absence de consigne transformée en règle certaine', 'document inconnu']}
        self.assertEqual(source_limits_for_rejections([rejection], source_packets(mark_excerpt(PROOF)), QUESTION), [])

    def test_unrelated_question_never_receives_neighbour_excerpt(self):
        rejection = {'claim': proposal()['claims'][0],
                     'errors': ['absence de consigne transformée en règle certaine']}
        self.assertEqual(source_limits_for_rejections([rejection], source_packets(mark_excerpt(PROOF)),
                          'Comment supprimer un créneau ?'), [])

    def test_editorial_instruction_is_not_a_reader_response(self):
        proof = 'Réponse directe : pour la publication du résultat provisoire, aucune consigne écrite retrouvée ; ne pas répondre oui ni non.'
        claim = proposal()['claims'][0]
        claim['evidence'][0]['quote'] = proof
        rejection = {'claim': claim, 'errors': ['absence de consigne transformée en règle certaine']}
        self.assertEqual(source_limits_for_rejections([rejection], source_packets(mark_excerpt(proof)), QUESTION), [])

    def test_annotated_document_keeps_its_scope_and_full_reserve(self):
        from pathlib import Path
        path = 'data/examens/audit_lot4_2026_10_13/points_sans_consigne_aix.txt'
        docs = mark_excerpt(Path(path).read_text(), path=path,
                            title='Questions sans consigne écrite trouvée pour Aix-Marseille', priority=300)
        packet = source_packets(docs)[0]
        span = next(s for s in packet['passages'] if 'Communiquer aux élèves leurs notes' in s['text'])
        output = {'claims': [{'section': 'decision',
                    'text': "Il n'existe pas de règle écrite interdisant de communiquer les notes aux élèves.",
                    'evidence': [{'document_id': packet['id'], 'passage_ids': [span['id']]}]}]}
        llm, audit = FakeLLM([output]), {}
        answer = review_exam_answer(llm, question='Peut-on communiquer les notes de CCF aux élèves ?',
                                   public='Lycée Général & Techno', documents=docs, audit=audit)
        self.assertEqual(len(llm.prompts), 0)
        self.assertTrue(audit['explicit_source_limit'])
        self.assertIn('provisoires', answer)
        self.assertIn('Faire confirmer', answer)
        self.assertTrue(audit['accepted_claims'][0]['evidence'][0]['scope'])

    def test_explicit_topic_and_limit_need_no_model_call(self):
        doc = mark_excerpt('Publication du résultat provisoire : ' + PROOF,
                           title='Limite documentaire', priority=300)
        llm, audit = FakeLLM([]), {}
        answer = review_exam_answer(llm, question=QUESTION, public='GT', documents=doc, audit=audit)
        self.assertEqual(len(llm.prompts), 0)
        self.assertTrue(audit['explicit_source_limit'])
        self.assertIn('Faire confirmer', answer)

    def test_compound_question_keeps_normal_model_path(self):
        doc = mark_excerpt('Publication du résultat provisoire : ' + PROOF,
                           title='Limite documentaire', priority=300)
        llm, audit = FakeLLM([{'claims': []}]), {}
        review_exam_answer(llm, question=QUESTION + ' Et comment supprimer un créneau ?',
                           public='GT', documents=doc, audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertFalse(audit['explicit_source_limit'])

    def test_competing_priority_document_keeps_normal_model_path(self):
        doc = mark_excerpt('Publication du résultat provisoire : ' + PROOF,
                           title='Limite documentaire', priority=300)
        doc += '\n\n' + mark_excerpt('Une autre règle concerne la publication du résultat provisoire.',
                            title='Autre cadre applicable', priority=300)
        llm, audit = FakeLLM([{'claims': []}]), {}
        review_exam_answer(llm, question=QUESTION, public='GT', documents=doc, audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertFalse(audit['explicit_source_limit'])

    def test_neighbouring_topic_keeps_normal_model_path(self):
        doc = mark_excerpt('Publication du résultat provisoire : ' + PROOF,
                           title='Limite documentaire', priority=300)
        llm, audit = FakeLLM([{'claims': []}]), {}
        review_exam_answer(llm, question='Comment supprimer un créneau de mon planning ?',
                           public='GT', documents=doc, audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertFalse(audit['explicit_source_limit'])

    def test_low_priority_document_cannot_bypass_model(self):
        doc = mark_excerpt('Publication du résultat provisoire : ' + PROOF,
                           title='Limite documentaire', priority=20)
        llm, audit = FakeLLM([{'claims': []}]), {}
        review_exam_answer(llm, question=QUESTION, public='GT', documents=doc, audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertFalse(audit['explicit_source_limit'])
