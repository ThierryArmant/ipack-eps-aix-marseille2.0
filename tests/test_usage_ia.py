import unittest
from types import SimpleNamespace

from documentary_review import TracedLLM, response_token_usage, usage_summary


class UsageTests(unittest.TestCase):
    def test_provider_usage_and_llamaindex_fallback(self):
        for raw in ({'usage': {'prompt_tokens': 120, 'completion_tokens': 30, 'total_tokens': 150}},
                    SimpleNamespace(usage=SimpleNamespace(prompt_tokens=120, completion_tokens=30, total_tokens=150))):
            result = SimpleNamespace(raw=raw, additional_kwargs={})
            self.assertEqual(response_token_usage(result), {'input_tokens':120, 'output_tokens':30, 'total_tokens':150})
        result = SimpleNamespace(raw={'usage': {'prompt_tokens': None}},
                                 additional_kwargs={'prompt_tokens':120, 'completion_tokens':30})
        self.assertEqual(response_token_usage(result)['input_tokens'], 120)

    def test_nested_review_counts_each_call_once_in_response_summary(self):
        class Provider:
            def complete(self, prompt):
                return SimpleNamespace(text='ok', raw=None, additional_kwargs={'prompt_tokens':10, 'completion_tokens':5})
        response_audit, review_audit = {}, {}
        outer = TracedLLM(Provider(), response_audit, capture_text=False)
        inner = TracedLLM(outer, review_audit)
        for _ in range(3):  # extraction, vérification, réparation
            inner.complete('private prompt')
        usage = usage_summary(response_audit)
        self.assertEqual((usage['calls'], usage['input_tokens'], usage['output_tokens']), (3,30,15))
        self.assertTrue(usage['complete'])
        self.assertNotIn('private prompt', str(response_audit))

    def test_missing_usage_and_failures_are_not_reported_as_measured_zero(self):
        class Provider:
            def complete(self, prompt):
                if prompt == 'fail':
                    raise RuntimeError('provider failed')
                return SimpleNamespace(text='ok')
        audit = {}
        traced = TracedLLM(Provider(), audit)
        traced.complete('unknown')
        with self.assertRaises(RuntimeError):
            traced.complete('fail')
        usage = usage_summary(audit)
        self.assertEqual((usage['calls'], usage['failed_calls'], usage['calls_with_usage']), (2,1,0))
        self.assertFalse(usage['complete'])
        self.assertTrue(usage_summary({})['complete'])


if __name__ == '__main__':
    unittest.main()
