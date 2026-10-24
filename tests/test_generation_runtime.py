import tempfile
from pathlib import Path
import unittest
from generation_runtime import load_runtime

class RuntimeTests(unittest.TestCase):
    def test_new_sources_do_not_mutate_runtime_in_another_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'exact_source_answer.py').write_text('# fixture')
            (root/'short_answer.py').write_text('# fixture')
            (root/'question_normalization.py').write_text('# fixture')
            (root/'source_scope.py').write_text('# fixture')
            (root/'evidence_logic.py').write_text('# fixture')
            (root/'navigation_restore.py').write_text('# fixture')
            (root/'single_document_test.py').write_text('# fixture')
            (root/'document_selector.py').write_text('# fixture')
            (root/'claim_guards.py').write_text('# fixture')
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

    def test_guard_change_selects_new_runtime_without_mutating_old(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'exact_source_answer.py').write_text('# fixture')
            (root/'short_answer.py').write_text('# fixture')
            (root/'question_normalization.py').write_text('# fixture')
            (root/'source_scope.py').write_text('# fixture')
            (root/'evidence_logic.py').write_text('# fixture')
            (root/'navigation_restore.py').write_text('# fixture')
            (root/'single_document_test.py').write_text('# fixture')
            (root/'document_selector.py').write_text('# fixture')
            (root/'albert_adapter.py').write_text('generation_llm=None')
            guard=root/'claim_guards.py'
            guard.write_text('marker="old"')
            (root/'documentary_review.py').write_text('from .claim_guards import marker\nTracedLLM=marker;usage_summary=None;review_exam_answer=None')
            before=load_runtime(root)
            guard.write_text('marker="new"')
            after=load_runtime(root)
            self.assertEqual(before.TracedLLM,'old')
            self.assertEqual(after.TracedLLM,'new')
            self.assertIsNot(before,after)

    def test_stale_global_test_module_does_not_break_new_runtime(self):
        import sys
        import types
        from unittest.mock import patch
        stale = types.ModuleType('single_document_test')
        with patch.dict(sys.modules, {'single_document_test': stale}):
            runtime = load_runtime()
            self.assertTrue(callable(runtime.single_document_test.consume_short_prompt_test))
            self.assertIn('SCHEMA', runtime.single_document_test.short_prompt('{}', '{}'))
            self.assertIs(sys.modules['single_document_test'], stale)

    def test_test_helper_change_selects_new_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'exact_source_answer.py').write_text('# fixture')
            (root/'short_answer.py').write_text('# fixture')
            (root/'question_normalization.py').write_text('# fixture')
            (root/'source_scope.py').write_text('# fixture')
            (root/'evidence_logic.py').write_text('# fixture')
            (root/'navigation_restore.py').write_text('# fixture')
            for name in ('document_selector', 'claim_guards'):
                (root / (name + '.py')).write_text('# fixture')
            (root/'albert_adapter.py').write_text('generation_llm=None')
            (root/'documentary_review.py').write_text('TracedLLM=None;usage_summary=None;review_exam_answer=None')
            helper = root/'single_document_test.py'
            helper.write_text('marker="before"')
            before = load_runtime(root)
            helper.write_text('marker="after"')
            after = load_runtime(root)
            self.assertIsNot(before, after)
            self.assertEqual(before.single_document_test.marker, 'before')
            self.assertEqual(after.single_document_test.marker, 'after')

    def test_scope_dependency_change_creates_new_runtime_without_mutating_previous(self):
        import shutil
        from generation_runtime import _FILES
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in _FILES:shutil.copyfile(Path(name+'.py'),root/(name+'.py'))
            before=load_runtime(root)
            source=root/'source_scope.py'
            source.write_text(source.read_text()+'\nREVISION_SCOPE_TEST = True\n')
            after=load_runtime(root)
            self.assertIsNot(before,after)
            self.assertFalse(hasattr(before.source_scope,'REVISION_SCOPE_TEST'))
            self.assertTrue(after.source_scope.REVISION_SCOPE_TEST)
            self.assertIs(after.documentary_review.scoped_segments,after.source_scope.scoped_segments)
            self.assertIs(after.documentary_review.evidence_logic,after.evidence_logic)
            self.assertIs(after.claim_guards.normalized,after.evidence_logic.normalized)
