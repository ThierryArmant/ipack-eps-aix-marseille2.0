import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import io
from urllib.error import HTTPError, URLError
from albert_adapter import AlbertLLM, AlbertError, available_models, BASE_URL
from documentary_review import TracedLLM, usage_summary

class AlbertAdapterTests(unittest.TestCase):
    def response(self, payload, status=200):
        result=io.BytesIO(json.dumps(payload).encode());result.status=status
        return result

    def test_discovery_excludes_typed_non_generation_models(self):
        payload={'data':[{'id':'writer','type':'text-generation'}, {'id':'embedding','type':'text-embeddings-inference'}, {'id':'writer','type':'text-generation'}]}
        with patch('albert_adapter.build_opener') as factory, patch.object(factory.return_value, 'open', return_value=self.response(payload)) as request:
            self.assertEqual(available_models('private-placeholder'),['writer'])
        self.assertEqual(request.call_args.args[0].full_url,BASE_URL+'/models')
        self.assertEqual(request.call_args.args[0].method,'GET')
        self.assertIsNone(factory.call_args.args[0].redirect_request(None,None,302,'',None,'https://other.example'))

    def test_generation_and_real_usage_without_secret_in_result(self):
        payload={'choices':[{'message':{'content':'{"claims":[]}'},'finish_reason':'stop'}],
                 'usage':{'prompt_tokens':10,'completion_tokens':4,'total_tokens':14},'model':'resolved-writer'}
        audit={}
        with patch('albert_adapter.build_opener') as factory, patch.object(factory.return_value, 'open', return_value=self.response(payload)) as request:
            llm=AlbertLLM('private-placeholder','writer')
            answer=TracedLLM(llm,audit).complete('question et preuves')
        self.assertEqual(answer.text,'{"claims":[]}')
        self.assertEqual(usage_summary(audit)['total_tokens'],14)
        self.assertNotIn('private-placeholder',json.dumps(audit))
        self.assertEqual(llm.resolved_model,'resolved-writer')
        sent=json.loads(request.call_args.args[0].data)
        self.assertEqual(sent['messages'],[{'role':'user','content':'question et preuves'}])
        self.assertNotIn('private-placeholder',json.dumps(sent))
        self.assertIsNone(factory.call_args.args[0].redirect_request(None,None,302,'',None,'https://other.example'))

    def test_errors_never_echo_response_body_or_secret(self):
        for status in (401,403,429,500,302):
            with self.subTest(status=status),patch('albert_adapter.build_opener') as factory, patch.object(factory.return_value, 'open', return_value=self.response({'error':'private-placeholder'},status)) as request:
                with self.assertRaises(AlbertError) as exc:available_models('private-placeholder')
                self.assertNotIn('private-placeholder',str(exc.exception))
                self.assertEqual(request.call_count,1)

    def test_transport_error_has_no_retry_or_secret(self):
        with patch('albert_adapter.build_opener') as factory, patch.object(factory.return_value,'open',side_effect=URLError('private-placeholder')) as request:
            with self.assertRaises(AlbertError) as exc:available_models('private-placeholder')
        self.assertNotIn('private-placeholder',str(exc.exception))
        self.assertEqual(request.call_count,1)

    def test_truncated_response_is_not_accepted(self):
        payload={'choices':[{'message':{'content':'partial'},'finish_reason':'length'}]}
        with patch('albert_adapter.build_opener') as factory, patch.object(factory.return_value, 'open', return_value=self.response(payload)):
            with self.assertRaises(AlbertError):AlbertLLM('private-placeholder','writer').complete('q')

    def test_missing_usage_is_not_estimated(self):
        payload={'choices':[{'message':{'content':'text'},'finish_reason':'stop'}]}
        audit={}
        with patch('albert_adapter.build_opener') as factory, patch.object(factory.return_value, 'open', return_value=self.response(payload)):
            TracedLLM(AlbertLLM('private-placeholder','writer'),audit).complete('q')
        self.assertFalse(usage_summary(audit)['complete'])

    def test_invalid_model_or_key_does_not_send_request(self):
        with patch('albert_adapter.build_opener') as request:
            with self.assertRaises(AlbertError):AlbertLLM('private-placeholder','model\nother')
            with self.assertRaises(AlbertError):available_models('')
        request.assert_not_called()
