import unittest
from types import SimpleNamespace
from albert_adapter import AlbertWithFallback, AlbertError, AlbertServiceError, generation_llm
from documentary_review import TracedLLM, usage_summary

class Fake:
    def __init__(self, provider, results):
        self.provider=provider; self.model='gpt-oss-120b' if provider=='albert' else 'gpt-4o-mini'
        self.temperature=0.0; self.resolved_model=None; self.results=list(results); self.prompts=[]
    def complete(self,prompt,**kwargs):
        self.prompts.append(prompt); r=self.results.pop(0)
        if isinstance(r,Exception):raise r
        return SimpleNamespace(text=r,raw={'usage':{'prompt_tokens':8,'completion_tokens':2,'total_tokens':10}})

class FallbackTests(unittest.TestCase):
    def test_primary_success_never_calls_gpt(self):
        a=Fake('albert',['ok']);g=Fake('openai',[]);audit={}
        self.assertEqual(TracedLLM(AlbertWithFallback(a,g),audit).complete('proof').text,'ok')
        self.assertEqual(g.prompts,[]);self.assertEqual(usage_summary(audit)['calls'],1)
        self.assertFalse(usage_summary(audit)['fallback_used'])
    def test_outage_replays_same_prompt_once_and_counts_both_attempts(self):
        for code in ('http_429','http_503','connection_unavailable','http_401'):
            with self.subTest(code=code):
                a=Fake('albert',[AlbertServiceError('safe',code)]);g=Fake('openai',['ok']);outer={};inner={}
                llm=TracedLLM(TracedLLM(AlbertWithFallback(a,g),outer,capture_text=False),inner)
                self.assertEqual(llm.complete('same proof').text,'ok')
                self.assertEqual(a.prompts,g.prompts)
                for audit in (outer,inner):
                    u=usage_summary(audit);self.assertEqual(u['calls'],2);self.assertEqual(u['failed_calls'],1)
                    self.assertTrue(u['fallback_used']);self.assertFalse(u['complete'])
                    self.assertEqual(u['total_tokens'],10)
                self.assertEqual(inner['calls'][0]['error_code'],code)
                self.assertNotIn('prompt',outer['calls'][0])
                self.assertEqual(inner['calls'][1]['model'],'gpt-4o-mini')
    def test_repair_stays_on_gpt_after_outage(self):
        a=Fake('albert',[AlbertServiceError('safe','http_503')]);g=Fake('openai',['draft','repair']);audit={}
        llm=TracedLLM(AlbertWithFallback(a,g),audit)
        llm.complete('draft');llm.complete('repair')
        self.assertEqual(a.prompts,['draft']);self.assertEqual(g.prompts,['draft','repair'])
        self.assertEqual(usage_summary(audit)['calls'],3)
    def test_documentary_content_never_triggers_provider_fallback(self):
        for value in ('{"claims":[]}','not json','incorrect claim'):
            a=Fake('albert',[value]);g=Fake('openai',[])
            self.assertEqual(AlbertWithFallback(a,g).complete('proof').text,value)
            self.assertEqual(g.prompts,[])
    def test_truncation_and_programming_error_do_not_trigger_fallback(self):
        for error in (AlbertError('truncated'),ValueError('invalid')):
            a=Fake('albert',[error]);g=Fake('openai',[])
            with self.assertRaises(type(error)):AlbertWithFallback(a,g).complete('proof')
            self.assertEqual(g.prompts,[])
    def test_second_provider_failure_stops_without_loop(self):
        a=Fake('albert',[AlbertServiceError('safe','http_503')]);g=Fake('openai',[RuntimeError('unavailable')]);audit={}
        with self.assertRaises(RuntimeError):TracedLLM(AlbertWithFallback(a,g),audit).complete('proof')
        self.assertEqual(usage_summary(audit)['calls'],2)
    def test_configuration_keeps_embeddings_and_comparator_independent(self):
        g=Fake('openai',[])
        self.assertIs(generation_llm(openai_llm=g,api_key=None),g)
        self.assertIs(generation_llm(openai_llm=g,api_key='placeholder',provider='openai'),g)
        one=generation_llm(openai_llm=g,api_key='placeholder');two=generation_llm(openai_llm=g,api_key='placeholder')
        self.assertIsNot(one,two);self.assertEqual(one.primary.timeout,45)
        self.assertEqual(one.primary.model,'gpt-oss-120b')
