"""Contrat transversal : exemples fictifs, hors banque privée du hub."""
import copy
import unittest
from pathlib import Path
from answer_grounding import grounding_errors
from documentary_review import mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

QUESTION = 'Je veux exporter le fichier, mais le bouton est grisé.'
SOURCE = 'Si le dossier est validé, le responsable peut exporter le fichier.'


def claim():
    return {'section': 'etape',
            'text': 'Si le dossier est validé, le responsable peut exporter le fichier.',
            'evidence': [{'document_id': 'D1', 'quote': SOURCE}],
            'application': {'role': 'necessary_step', 'question_quote': 'exporter le fichier',
                            'source_quote': SOURCE,
                            'conditions': [{'source_quote': 'Si le dossier est validé',
                                            'state': 'unknown', 'question_quote': ''}]}}


class GroundingTests(unittest.TestCase):
    def test_unknown_condition_must_remain_in_each_step(self):
        c = claim()
        self.assertFalse(grounding_errors([c], QUESTION))
        c['text'] = 'Le responsable peut exporter le fichier.'
        self.assertIn('condition inconnue supprimée', str(grounding_errors([c], QUESTION)))

    def test_condition_cannot_be_declared_established_without_actual_fact(self):
        c = claim()
        c['application']['conditions'][0].update(state='established', question_quote='Le dossier est validé')
        self.assertTrue(grounding_errors([c], QUESTION))
        self.assertFalse(grounding_errors([c], QUESTION + ' Le dossier est validé.'))

    def test_empty_conditions_cannot_hide_explicit_antecedent(self):
        c = claim()
        c['application']['conditions'] = []
        self.assertIn('antécédent explicite', str(grounding_errors([c], QUESTION)))

    def test_neighbouring_topic_is_not_an_answer_role(self):
        c = claim()
        c['application']['role'] = 'background'
        self.assertTrue(grounding_errors([c], QUESTION))
        c['application']['role'] = 'necessary_step'
        c['application']['question_quote'] = 'Comment modifier le statut ?'
        self.assertTrue(grounding_errors([c], QUESTION))

    def test_targeted_quote_must_be_in_selected_evidence_not_any_document(self):
        c = claim()
        c['application']['source_quote'] = 'Le responsable peut supprimer le dossier en attente.'
        self.assertTrue(grounding_errors([c], QUESTION))

    def test_repair_records_real_failure_and_preserves_condition(self):
        good = claim()
        bad = copy.deepcopy(good)
        bad['text'] = 'Le responsable peut exporter le fichier.'
        llm = FakeLLM([{'claims': [bad]}, {'claims': [good]}])
        audit = {}
        text = review_exam_answer(llm, question=QUESTION, public='GT',
                                  documents=mark_excerpt(SOURCE), audit=audit,
                                  require_grounding=True)
        self.assertIn('Si le dossier est validé', text)
        self.assertEqual(len(llm.prompts), 2)
        self.assertTrue(audit['initial_rejections'])
        self.assertFalse(audit['final_rejections'])
        self.assertTrue(audit['grounding_contract'])

    def test_valid_answer_keeps_single_call_and_targeted_evidence(self):
        c = claim()
        extra = SOURCE + ' Le responsable archive les dossiers supprimés.'
        c['evidence'][0]['quote'] = extra
        llm = FakeLLM([{'claims': [c]}])
        audit = {}
        review_exam_answer(llm, question=QUESTION, public='GT', documents=mark_excerpt(extra),
                           audit=audit, require_grounding=True)
        self.assertEqual(len(llm.prompts), 1)
        self.assertEqual(audit['accepted_claims'][0]['evidence'][0]['quote'], SOURCE)

    def test_production_uses_contract_and_does_not_replace_verified_prose(self):
        code = Path('app.py').read_text()
        self.assertIn('require_grounding=True', code)
        self.assertNotIn('verdict_champs', code)
        self.assertNotIn('zone de précision ci-dessous', code)


if __name__ == '__main__':
    unittest.main()
