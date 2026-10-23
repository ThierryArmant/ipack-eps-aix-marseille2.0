import unittest
from unittest.mock import patch
from albert_adapter import ALBERT_PAUSED, AlbertLLM, AlbertServiceError, available_models, generation_llm

class AlbertPausedTests(unittest.TestCase):
    def test_no_network_for_discovery_or_generation(self):
        self.assertTrue(ALBERT_PAUSED)
        with patch('albert_adapter.build_opener') as network:
            for operation in (lambda: available_models('placeholder'), lambda: AlbertLLM('placeholder', 'gpt-oss-120b').complete('question')):
                with self.assertRaises(AlbertServiceError) as caught:
                    operation()
                self.assertEqual(caught.exception.code, 'temporarily_disabled')
            network.assert_not_called()

    def test_configured_albert_returns_gpt_directly(self):
        gpt = object()
        self.assertIs(generation_llm(openai_llm=gpt, api_key='placeholder', provider='albert'), gpt)
