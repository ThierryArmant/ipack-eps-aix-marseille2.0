import unittest
from types import SimpleNamespace as N
from openai_test_adapter import test_clients, TestCallLimitError
from documentary_review import TracedLLM, usage_summary


class AdapterTests(unittest.TestCase):
    def factory(self, **kwargs):
        self.options.append(kwargs)
        owner=self
        class Client:
            chat=N(completions=N(create=lambda **p: owner.request(p)))
            def __enter__(self): return self
            def __exit__(self,*args): return False
        return Client()

    def request(self, params):
        self.requests.append(params)
        return N(model=params['model'],choices=[N(message=N(content='{"claims":[]}'))],
                 usage=N(prompt_tokens=12,completion_tokens=6,total_tokens=18))

    def setUp(self): self.requests=[];self.options=[]

    def test_two_real_calls_max_and_no_retry_or_fallback(self):
        selector,writer=test_clients('gpt-5.4','fake-key',self.factory)
        audit={}
        TracedLLM(selector,audit,stage='selection').complete('Selection prompt')
        traced=TracedLLM(writer,audit)
        traced.complete('Writing prompt')
        with self.assertRaises(TestCallLimitError):traced.complete('Repair prompt')
        self.assertEqual(len(self.requests),2)
        self.assertEqual([p['max_completion_tokens'] for p in self.requests],[600,1600])
        self.assertTrue(all(p['model']=='gpt-5.4' and p['reasoning_effort']=='none' for p in self.requests))
        self.assertTrue(all(p['store'] is False for p in self.requests))
        self.assertTrue(all(o['max_retries']==0 for o in self.options))
        self.assertEqual(usage_summary(audit)['input_tokens'],24)
        self.assertFalse(usage_summary(audit)['fallback_used'])

    def test_limits_prevent_network_and_gpt4_uses_legacy_parameter(self):
        selector,writer=test_clients('gpt-4.1','fake-key',self.factory)
        with self.assertRaises(ValueError):selector.complete('x'*14001)
        with self.assertRaises(ValueError):writer.complete('x'*50001)
        self.assertEqual(self.requests,[])
        writer.complete('Prompt')
        self.assertEqual(self.requests[0]['max_tokens'],1600)
        self.assertNotIn('reasoning_effort',self.requests[0])

    def test_documentary_validation_does_not_retry_in_test_mode(self):
        from documentary_review import review_exam_answer, mark_excerpt
        from test_documentary_review import FakeLLM
        llm=FakeLLM([{'claims':[{'section':'decision','text':'Action non justifiée.',
            'evidence':[{'document_id':'D999','passage_ids':['D999P1']}]}]}])
        audit={}
        with self.assertRaises(ValueError):
            review_exam_answer(llm,question='Ouvrir le dossier',public='Lycée Général & Techno',
                documents=mark_excerpt('Procédure : ouvrir le dossier.',title='Dossier'),
                repair_enabled=False,audit=audit)
        self.assertEqual(len(llm.prompts),1)
        self.assertTrue(audit['repair_disabled_for_test'])
        self.assertFalse(audit['repair_performed'])
        self.assertTrue(audit['final_rejections'])
