import tempfile
from pathlib import Path
import unittest
from generation_runtime import load_runtime

class RuntimeTests(unittest.TestCase):
    def test_new_sources_do_not_mutate_runtime_in_another_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'albert_adapter.py').write_text('generation_llm = "provider"')
            p=root/'documentary_review.py'
            p.write_text('TracedLLM="old"; usage_summary=None; review_exam_answer=None')
            before=load_runtime(root)
            self.assertIs(before,load_runtime(root))
            p.write_text('TracedLLM="new"; usage_summary=None; review_exam_answer=None')
            after=load_runtime(root)
            self.assertEqual(before.TracedLLM,'old');self.assertEqual(after.TracedLLM,'new')
    def test_runtime_routes_and_records_both_attempts(self):
        runtime=load_runtime();adapter=runtime.albert_adapter
        from test_albert_fallback import Fake
        a=Fake('albert',[adapter.AlbertServiceError('safe','http_503')]);g=Fake('openai',['ok'])
        outer={};inner={}
        llm=runtime.TracedLLM(runtime.TracedLLM(adapter.AlbertWithFallback(a,g),outer,capture_text=False),inner)
        self.assertEqual(llm.complete('proof').text,'ok')
        self.assertEqual(runtime.usage_summary(inner)['calls'],2)
        self.assertTrue(runtime.usage_summary(outer)['fallback_used'])
