import json
import unittest
from documentary_review import _SCHEMA
from single_document_test import short_prompt

class ShortPromptSchemaTests(unittest.TestCase):
    def test_example_is_valid_and_choices_are_separate(self):
        data = '{"documents":[],"question":"test"}'
        prompt = short_prompt(_SCHEMA, data)
        example = prompt.split('SCHEMA :\n', 1)[1].split('\nDONNEES :\n', 1)[0]
        self.assertEqual(json.loads(example)['claims'][0]['section'], 'etape')
        self.assertNotIn('decision|condition|etape|limite', prompt)
        self.assertIn('section contient une seule valeur', prompt)
        for section in ('decision', 'condition', 'etape', 'limite'):
            self.assertIn('"' + section + '"', prompt)
        self.assertEqual(prompt.split('DONNEES :\n', 1)[1], data)
        self.assertIn('decision|condition|etape|limite', _SCHEMA)
