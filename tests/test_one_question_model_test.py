import ast
from pathlib import Path
import unittest
from one_question_model_test import consume_gpt41_test


class OneQuestionModelTests(unittest.TestCase):
    def test_admin_only_and_consumed_once(self):
        state = {'is_admin': True, 'gpt41_once_pending': True}
        self.assertTrue(consume_gpt41_test(state))
        self.assertFalse(consume_gpt41_test(state))
        self.assertFalse(consume_gpt41_test({'gpt41_once_pending': True}))

    def test_ten_manual_questions_then_normal(self):
        state = {'is_admin': True, 'gpt41_once_pending': 10}
        for remaining in range(10, 0, -1):
            self.assertEqual(state['gpt41_once_pending'], remaining)
            self.assertTrue(consume_gpt41_test(state))
        self.assertFalse(consume_gpt41_test(state))
        self.assertNotIn('gpt41_once_pending', state)
        self.assertFalse(consume_gpt41_test({'is_admin': True, 'gpt41_once_pending': 11}))

    def test_writer_override_has_no_provider_wrapper(self):
        tree = ast.parse(Path('app.py').read_text())
        blocks = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                  and isinstance(n.test, ast.Name) and n.test.id == '_test_gpt41']
        self.assertEqual(len(blocks), 1)
        assignment = blocks[0].body[0]
        self.assertEqual(assignment.targets[0].id, '_generation_llm')
        self.assertEqual(assignment.value.func.id, 'OpenAI')
        self.assertEqual(next(k.value.value for k in assignment.value.keywords if k.arg == 'model'), 'gpt-4.1')
        selectors = [n for n in ast.walk(tree) if isinstance(n, ast.IfExp)
                     and isinstance(n.test, ast.Name) and n.test.id == '_test_gpt41']
        self.assertTrue(any(isinstance(n.body, ast.Constant) and n.body.value == 'gpt-4.1' for n in selectors))
