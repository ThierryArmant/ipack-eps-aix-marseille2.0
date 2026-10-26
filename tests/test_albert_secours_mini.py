import unittest
from types import SimpleNamespace
from unittest import mock

import albert_adapter


class SecoursMiniTest(unittest.TestCase):
    def test_quota_albert_mini_redige(self):
        albert = mock.Mock(model='gpt-oss-120b', temperature=0, resolved_model=None)
        albert.complete.side_effect = albert_adapter.AlbertServiceError('Quota', 'http_429')
        mini = mock.Mock(model='gpt-4o-mini', temperature=0)
        mini.complete.return_value = SimpleNamespace(text='{"phrases": []}')
        llm = albert_adapter.AlbertWithFallback(albert, mini)
        self.assertEqual(llm.complete('prompt').text, '{"phrases": []}')
        self.assertEqual(llm.fallback_reason, 'http_429')
        self.assertEqual(llm.resolved_model, 'gpt-4o-mini')

    def test_albert_disponible_pas_de_mini(self):
        albert = mock.Mock(model='gpt-oss-120b', temperature=0, resolved_model='gpt-oss-120b')
        albert.complete.return_value = SimpleNamespace(text='ok')
        mini = mock.Mock(model='gpt-4o-mini', temperature=0)
        llm = albert_adapter.AlbertWithFallback(albert, mini)
        self.assertEqual(llm.complete('prompt').text, 'ok')
        mini.complete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
