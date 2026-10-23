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

    def test_writer_and_selector_share_explicit_model_without_provider_wrapper(self):
        tree = ast.parse(Path('app.py').read_text())
        blocks = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                  and isinstance(n.test, ast.Name) and n.test.id == '_test_gpt41']
        self.assertEqual(len(blocks), 1)
        calls = [n for n in ast.walk(blocks[0]) if isinstance(n, ast.Call)]
        self.assertEqual(calls[0].func.id, 'test_clients')
        self.assertEqual(calls[0].args[0].id, '_test_model')
        self.assertIn('_test_selector if _test_gpt41 else OpenAI', Path('app.py').read_text())

    def test_selected_model_and_counter(self):
        from one_question_model_test import consume_model_test
        state = {'is_admin': True, 'gpt41_once_pending': 1, 'openai_test_model':'gpt-5.4'}
        self.assertEqual(consume_model_test(state),'gpt-5.4')
        self.assertIsNone(consume_model_test(state))
        self.assertIsNone(consume_model_test({'is_admin':True,'gpt41_once_pending':10,'openai_test_model':'unknown'}))
