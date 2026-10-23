import json
import unittest
from single_document_test import consume_short_prompt_test, short_prompt

class ShortPromptTests(unittest.TestCase):
    def test_one_use_admin_examens_requires_single_document(self):
        state = {'is_admin': True, 'single_document_pending': True, 'short_prompt_pending': True}
        self.assertFalse(consume_short_prompt_test(state, 'ipack'))
        self.assertTrue(consume_short_prompt_test(state, 'examens'))
        self.assertFalse(consume_short_prompt_test(state, 'examens'))
        for state in ({'short_prompt_pending': True}, {'is_admin': True, 'short_prompt_pending': True}):
            self.assertFalse(consume_short_prompt_test(state, 'examens'))

    def test_same_schema_and_data_no_subject_rule(self):
        schema = '{"claims":[]}'
        data = json.dumps({'question': 'test', 'documents': [{'id': 'D1', 'passages': [{'id': 'D1P1', 'text': 'preuve'}]}]})
        prompt = short_prompt(schema, data)
        self.assertEqual(prompt.split('DONNEES :\n', 1)[1], data)
        self.assertIn(schema, prompt)
        self.assertLess(len(prompt) - len(data), 1800)
        for word in ('AFL1', 'Santorin', 'cadenas', 'navigateur'):
            self.assertNotIn(word, prompt)
