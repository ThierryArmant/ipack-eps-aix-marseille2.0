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
