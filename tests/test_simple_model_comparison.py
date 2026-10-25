import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import time
import unittest

class ModelComparisonTests(unittest.TestCase):
    def setUp(self):
        source=(Path(__file__).resolve().parents[1]/'architecture_comparison.py').read_text()
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='run_model_comparison')
        self.exact=Mock(return_value='réponse')
        self.usage=Mock(return_value={'calls':2})
        env=dict(hashlib=hashlib,time=time,exact_answer=self.exact,usage_summary=self.usage,
                 TracedLLM=object(),_runtime=SimpleNamespace(documentary_review=object()),AlbertError=ValueError)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'function','exec'),env)
        self.run_compare=env['run_model_comparison']
        self.retrieve=Mock(return_value=('documents communs',[],[],''))
        self.mini=SimpleNamespace(model='gpt-4o-mini')
        self.albert=SimpleNamespace(model='gpt-oss-120b')
    def run_case(self):
        return self.run_compare(mini=self.mini,albert=self.albert,retrieve=self.retrieve,
            question='Question ?',public='Collège (DNB)',mode='ipack',academy='Aix-Marseille',version='test')
    def test_shared_retrieval_and_protocol(self):
        result=self.run_case()
        self.retrieve.assert_called_once()
        self.assertEqual(self.exact.call_count,2)
        for call in self.exact.call_args_list:
            self.assertEqual(call.kwargs['documents'],'documents communs')
            self.assertTrue(call.kwargs['synthesis'])
            self.assertNotIn('selector_llm',call.kwargs)
        self.assertIs(self.exact.call_args_list[0].args[0],self.mini)
        self.assertIs(self.exact.call_args_list[1].args[0],self.albert)
        self.assertEqual(result['branches']['Albert']['model'],'gpt-oss-120b')
    def test_no_generation_if_retrieval_failed(self):
        self.retrieve.return_value=('','','','incident')
        with self.assertRaises(ValueError):self.run_case()
        self.exact.assert_not_called()
    def test_albert_error_does_not_retry_or_replace_mini(self):
        self.exact.side_effect=['réponse mini',ValueError('quota')]
        result=self.run_case()
        self.assertEqual(self.exact.call_count,2)
        self.assertEqual(result['branches']['Mini']['answer'],'réponse mini')
        self.assertEqual(result['branches']['Albert']['error'],'quota')
    def test_ui_requires_submit_and_keeps_trials_separate(self):
        source=(Path(__file__).resolve().parents[1]/'architecture_comparison.py').read_text()
        tree=ast.parse(source)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='render_model_comparison')
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='run_model_comparison']
        self.assertEqual(len(calls),1)
        self.assertIn('if submitted:',ast.get_source_segment(source,fn))
        self.assertNotIn('admin_albert_only',ast.get_source_segment(source,fn))
