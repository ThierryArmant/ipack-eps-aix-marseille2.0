import unittest
from unittest.mock import patch
from albert_adapter import ALBERT_PAUSED, AlbertLLM, AlbertServiceError, available_models, generation_llm

class AlbertPausedTests(unittest.TestCase):
    def test_authorized_admin_instance_reaches_http_without_unpausing_public(self):
        import json
        payload={'choices':[{'message':{'content':'réponse'},'finish_reason':'stop'}],
                 'model':'gpt-oss-120b','usage':{'prompt_tokens':3,'completion_tokens':2,'total_tokens':5}}
        with patch('albert_adapter.ALBERT_PAUSED',True), patch('albert_adapter.build_opener') as network:
            response=network.return_value.open.return_value.__enter__.return_value
            response.status=200
            response.read.return_value=json.dumps(payload).encode()
            direct=AlbertLLM('placeholder','gpt-oss-120b',allow_paused_test=True)
            self.assertEqual(direct.complete('question').text,'réponse')
            network.return_value.open.assert_called_once()
            with self.assertRaises(AlbertServiceError):
                AlbertLLM('placeholder','gpt-oss-120b').complete('question')
            with self.assertRaises(AlbertServiceError):
                available_models('placeholder')
            network.return_value.open.assert_called_once()
            gpt=object()
            self.assertIs(generation_llm(openai_llm=gpt,api_key='placeholder',provider='albert'),gpt)

    def test_authorized_admin_service_failure_retried_once_only(self):
        from urllib.error import URLError
        with patch('albert_adapter.ALBERT_PAUSED',True), patch('albert_adapter.build_opener') as network, \
                patch('albert_adapter._sleep', lambda seconds: None):
            network.return_value.open.side_effect=URLError('unavailable')
            with self.assertRaises(AlbertServiceError):
                AlbertLLM('placeholder','gpt-oss-120b',allow_paused_test=True).complete('question')
            self.assertEqual(network.return_value.open.call_count, 2)

    def test_no_network_for_discovery_or_generation(self):
        self.assertTrue(ALBERT_PAUSED)
        with patch('albert_adapter.ALBERT_PAUSED', True), patch('albert_adapter.build_opener') as network:
            for operation in (lambda: available_models('placeholder'), lambda: AlbertLLM('placeholder', 'gpt-oss-120b').complete('question')):
                with self.assertRaises(AlbertServiceError) as caught:
                    operation()
                self.assertEqual(caught.exception.code, 'temporarily_disabled')
            network.assert_not_called()

    def test_configured_albert_is_active_without_construction_network(self):
        from types import SimpleNamespace
        from albert_adapter import AlbertWithFallback
        gpt = SimpleNamespace(temperature=0.0)
        with patch('albert_adapter.ALBERT_PAUSED', False), patch('albert_adapter.build_opener') as network:
            writer = generation_llm(openai_llm=gpt, api_key='placeholder', provider='albert')
            self.assertIsInstance(writer, AlbertWithFallback)
            self.assertIs(generation_llm(openai_llm=gpt, api_key=None, provider='albert'), gpt)
            self.assertIs(generation_llm(openai_llm=gpt, api_key='placeholder', provider='openai'), gpt)
            network.assert_not_called()

    def test_pause_returns_gpt_even_with_albert_key(self):
        gpt = object()
        with patch('albert_adapter.build_opener') as network:
            self.assertIs(generation_llm(openai_llm=gpt, api_key='placeholder', provider='albert'),gpt)
            network.assert_not_called()
