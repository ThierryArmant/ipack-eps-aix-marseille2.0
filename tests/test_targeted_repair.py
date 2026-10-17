"""La réparation repart de la documentation sans recopier le brouillon rejeté."""
import unittest
import ast
from pathlib import Path
from documentary_review import mark_excerpt, review_exam_answer, source_packets, compact_model_packet
from test_documentary_review import FakeLLM


class TargetedRepairTests(unittest.TestCase):
    def test_streamlit_entrypoint_does_not_manually_reload_shared_modules(self):
        tree = ast.parse(Path('app.py').read_text())
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                             and isinstance(n.func.value, ast.Name)
                             and n.func.value.id == 'importlib' and n.func.attr == 'reload'
                             for n in ast.walk(tree)))

    def test_repair_keeps_current_rules_without_reinjecting_bad_draft(self):
        text = 'Le responsable vérifie le dispositif avant de valider le dossier.'
        bad = {'claims': [{'section': 'decision', 'text': 'BROUILLON_FAUX_SANS_PREUVE',
                          'evidence': [{'document_id': 'D999', 'passage_ids': ['D999P1']}]}]}
        good = {'claims': [{'section': 'decision', 'text': text,
                           'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}]}
        llm = FakeLLM([bad, good])
        result = review_exam_answer(llm, question='Qui valide le dossier ?', public='Collège',
                                   documents=mark_excerpt(text), instructions='CONSIGNE_ACTUELLE')
        self.assertEqual(len(llm.prompts), 2)
        self.assertNotIn('BROUILLON_FAUX_SANS_PREUVE', llm.prompts[-1])
        self.assertIn(text, llm.prompts[-1])
        self.assertIn('CONSIGNE_ACTUELLE', llm.prompts[-1])
        self.assertIn('responsable', result)

    def test_repair_identifies_failed_passage_selection_without_copying_draft(self):
        import json
        docs = mark_excerpt('Le dispositif demeure exceptionnel.\n\n'
                            'Le responsable valide le dispositif après vérification des pièces.')
        bad = {'claims': [{'section': 'decision', 'text': 'BROUILLON_SANS_JUSTIFICATION',
                           'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}]}
        good = {'claims': [{'section': 'condition',
                            'text': 'Le responsable valide le dispositif après vérification des pièces.',
                            'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P2']}]}]}
        llm = FakeLLM([bad, good])
        review_exam_answer(llm, question='Comment valider le dispositif ?', public='Collège',
                           documents=docs, mode='textes')
        feedback = json.loads(llm.prompts[1].split('ERREURS MECANIQUES :\n')[1])
        self.assertEqual(feedback[0]['rejected_evidence'],
                         [{'document_id': 'D1', 'passage_ids': ['D1P1']}])
        self.assertEqual(feedback[0]['section'], 'decision')
        self.assertNotIn('BROUILLON_SANS_JUSTIFICATION', llm.prompts[1])
        self.assertEqual(len(llm.prompts), 2)

    def test_logical_rejection_keeps_its_passage_after_an_earlier_lexical_rejection(self):
        import json
        docs = mark_excerpt('Le dispositif demeure exceptionnel.\n\n'
                            'Le responsable valide le dispositif après vérification des pièces.\n\n'
                            'Le texte prévoit un contrôle annuel. Le référentiel est ancien ; '
                            'les justificatifs actuels doivent être confirmés.')
        bad = {'claims': [
            {'section': 'decision', 'text': 'BROUILLON_SANS_JUSTIFICATION',
             'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]},
            {'section': 'condition', 'text': 'Vous devez effectuer un contrôle annuel.',
             'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P3']}]}]}
        good = {'claims': [{'section': 'condition',
                           'text': 'Selon le texte ancien, un contrôle annuel est prévu ; les justificatifs actuels sont à confirmer.',
                           'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P3']}]}]}
        llm, audit = FakeLLM([bad, good]), {}
        review_exam_answer(llm, question='Quels contrôles du dispositif ?', public='Collège',
                           documents=docs, mode='textes', audit=audit)
        feedback = json.loads(llm.prompts[1].split('ERREURS MECANIQUES :\n')[1])
        self.assertEqual(feedback[1]['rejected_evidence'],
                         [{'document_id': 'D1', 'passage_ids': ['D1P3']}])
        self.assertEqual(audit['repair_feedback'], feedback)
        self.assertNotIn('BROUILLON_SANS_JUSTIFICATION', llm.prompts[1])

    def test_lexical_rejection_does_not_hide_source_independent_wording_error(self):
        import json
        docs = mark_excerpt('Le responsable vérifie les pièces du dossier avant validation.')
        bad = {'claims': [{'section': 'decision',
                           'text': 'Vous pouvez utiliser le dispositif sous certaines conditions.',
                           'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}]}
        good = {'claims': [{'section': 'condition',
                            'text': 'Le responsable vérifie les pièces du dossier avant validation.',
                            'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}]}
        llm, audit = FakeLLM([bad, good]), {}
        review_exam_answer(llm, question='Comment valider le dossier ?', public='Collège',
                           documents=docs, mode='textes', audit=audit)
        feedback = audit['repair_feedback'][0]
        self.assertEqual(len(feedback['errors']), 2)
        self.assertIn('passage cité sans rapport', feedback['errors'][0])
        self.assertIn('conditions non précisées', feedback['errors'][1])
        self.assertNotIn(bad['claims'][0]['text'], llm.prompts[1])
        self.assertEqual(len(llm.prompts), 2)

    def test_compact_payload_preserves_exact_text_ids_and_legal_scope(self):
        packet = source_packets(mark_excerpt('Une consigne locale précise les étapes.'))[0]
        span = packet['passages'][0]
        span['scope'] = {'level': 'academique', 'nature': ['consigne_academique'],
                         'academy': 'Aix-Marseille', 'not_confirmed_for': 'Lyon',
                         'sessions': ['2026'], 'status': 'metadata_fiche', 'file_academy': None}
        compact = compact_model_packet(packet)
        selected = compact['passages'][0]
        self.assertEqual(selected['id'], span['id'])
        self.assertIn(span['text'], selected['text'])
        self.assertIn('non confirmée pour Lyon', selected['text'])
        self.assertEqual(selected['scope']['sessions'], ['2026'])
        self.assertEqual(selected['scope']['nature'], ['consigne_academique'])
        self.assertNotIn('start', selected)
        self.assertNotIn('status', selected['scope'])
        self.assertIn('start', span)
