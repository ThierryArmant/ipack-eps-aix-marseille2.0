import unittest
from types import SimpleNamespace as N
from model_access_probe import probe_gpt54


class ProbeTests(unittest.TestCase):
    def factory(self, model='gpt-5.4-2026-03-05', error=None):
        owner=self
        class Client:
            def __init__(self, **kwargs):
                owner.init=kwargs
                self.chat=N(completions=N(create=self.create))
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def create(self, **kwargs):
                owner.payload=kwargs
                if error: raise error
                return N(model=model,choices=[N(message=N(content='OK'))],usage=N(prompt_tokens=8,completion_tokens=1))
        return Client

    def test_exact_model_no_fallback_and_bounded_call(self):
        r=probe_gpt54('fake-key',self.factory())
        self.assertTrue(r['ok'])
        self.assertEqual(self.payload['model'],'gpt-5.4')
        self.assertEqual(self.payload['max_completion_tokens'],32)
        self.assertEqual(self.payload['reasoning_effort'],'none')
        self.assertFalse(self.payload['store'])
        self.assertEqual(self.init['max_retries'],0)
        self.assertEqual(r['output_tokens'],1)

    def test_other_model_not_confirmed(self):
        self.assertFalse(probe_gpt54('fake-key',self.factory('gpt-4.1'))['ok'])

    def test_error_and_missing_key_do_not_leak(self):
        e=Exception('private fake-key')
        e.status_code=429;e.code='insufficient_quota'
        r=probe_gpt54('fake-key',self.factory(error=e))
        self.assertFalse(r['ok']);self.assertEqual(r['error_code'],'insufficient_quota')
        self.assertNotIn('fake-key',str(r))
        self.assertFalse(probe_gpt54(None)['ok'])
