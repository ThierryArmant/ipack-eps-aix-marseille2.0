import ast
import unittest
from pathlib import Path
from knowledge_catalog import clarification


class NotesEntryClarificationTests(unittest.TestCase):
    def test_missing_software_is_asked_before_mixing_procedures(self):
        for question in ['Impossible de saisir les notes de ma classe.',
                         'Je ne peux pas enregistrer mes notes.',
                         'Les cases pour les notes sont grisées.']:
            with self.subTest(question=question):
                answer = clarification(question, 'Lycée Général & Techno', mode='ipack')
                self.assertIn('Dans quel logiciel', answer)
                self.assertIn('Santorin', answer)
                self.assertIn('Pronote', answer)
                self.assertIn('iPackEPS', answer)
                self.assertNotIn('AFLP', answer)

    def test_identified_software_or_exam_operation_is_not_asked_again(self):
        for question in ['Impossible de saisir les notes dans Santorin.',
                         'Je ne peux pas enregistrer mes notes dans Pronote.',
                         'Les cases AFLP sont grisées dans mon lot.',
                         'Je ne peux pas saisir mes notes dans iPackEPS.']:
            self.assertNotIn('Dans quel logiciel', clarification(question, 'Lycée Général & Techno', mode='ipack'))

    def test_other_modes_and_navigation_keep_their_existing_route(self):
        for mode in ['examens', 'textes']:
            self.assertNotIn('Dans quel logiciel', clarification('Impossible de saisir mes notes.', 'Lycée Général & Techno', mode=mode))
        self.assertNotIn('Dans quel logiciel', clarification('Où saisir les notes ?', 'Lycée Général & Techno', mode='ipack'))

    def test_app_supplies_mode_to_documentary_clarification(self):
        tree = ast.parse(Path('app.py').read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'clarification']
        self.assertTrue(calls)
        self.assertTrue(all(any(k.arg == 'mode' for k in call.keywords) for call in calls))
