import json
from types import SimpleNamespace
from unittest.mock import Mock,patch
import unittest
from architecture_comparison import run_comparison, render
from documentary_review import TracedLLM
from albert_adapter import AlbertError

class Model:
    temperature=0.0
    def __init__(self,name):self.model=name;self.prompts=[]
    def complete(self,prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(text='réponse',raw={'usage':{'prompt_tokens':5,'completion_tokens':2}})

class AlbertComparisonTests(unittest.TestCase):
    def test_same_retrieval_and_writing_input_with_independent_usage(self):
        first,second=Model('current'),Model('albert-model')
        retrieve=Mock(return_value=('same sources',[],{},''))
        def review(llm,*,question,documents,audit,**kwargs):
            return TracedLLM(llm,audit).complete(question+'\n'+documents).text
        with patch('architecture_comparison.review_exam_answer',side_effect=review):
            result=run_comparison(llm=first,comparison_llm=second,retrieve=retrieve,question='Une demande explicite.',public='Lycée Général & Techno',mode='ipack',academy='Grenoble',version='v',experimental='D')
        self.assertEqual(result['academy'],'Grenoble')
        self.assertEqual(retrieve.call_count,1)
        self.assertEqual(first.prompts,second.prompts)
        self.assertEqual(result['branches']['A']['usage']['calls'],1)
        self.assertEqual(result['branches']['D']['usage']['calls'],1)
        self.assertEqual(result['branches']['D']['model'],'albert-model')
        self.assertNotIn('interpretation',result['branches']['D'])
        self.assertNotIn('uncertainty',result['branches']['D'])

    def test_missing_model_or_temperature_mismatch_fails_before_paid_call(self):
        first=Model('current');second=Model('albert');second.temperature=1
        retrieve=Mock()
        for candidate in (None,second):
            with self.assertRaises(ValueError):
                run_comparison(llm=first,comparison_llm=candidate,retrieve=retrieve,question='q',public='p',mode='ipack',academy='a',version='v',experimental='D')
        retrieve.assert_not_called();self.assertEqual(first.prompts,[])

    def test_albert_error_keeps_A_without_silent_fallback(self):
        first,second=Model('current'),Model('albert')
        def review(llm,**kwargs):
            if llm is second:raise AlbertError('Quota Albert atteint ; réessayez plus tard.')
            return 'réponse A'
        with patch('architecture_comparison.review_exam_answer',side_effect=review):
            result=run_comparison(llm=first,comparison_llm=second,retrieve=Mock(return_value=('docs',[],{},'')),question='Une demande explicite.',public='Lycée Général & Techno',mode='ipack',academy='Aix-Marseille',version='v',experimental='D')
        self.assertEqual(result['branches']['A']['answer'],'réponse A')
        self.assertIn('Quota',result['branches']['D']['error'])
        self.assertNotIn('answer',result['branches']['D'])

    def test_guided_request_uses_neither_model(self):
        first,second=Model('current'),Model('albert')
        retrieve=Mock()
        result=run_comparison(llm=first,comparison_llm=second,retrieve=retrieve,question='aide moi je suis perdu',public='Collège (DNB)',mode='ipack',academy='Aix-Marseille',version='v',experimental='D')
        self.assertFalse(result['comparison_executed']);retrieve.assert_not_called()
        self.assertEqual(first.prompts+second.prompts,[])

    def test_opening_admin_panel_with_key_never_calls_provider(self):
        class Surface:
            def file_uploader(self, *args, **kwargs): return None
            session_state={'is_admin':True}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def expander(self,*args,**kwargs):return self
            form=expander
            def caption(self,*args,**kwargs):pass
            info=caption;warning=caption
            def button(self,*args,**kwargs):return False
            form_submit_button=button
            def selectbox(self,label,values):return values[0]
            def text_input(self,*args,**kwargs):return ''
            text_area=text_input
        with patch('architecture_comparison.available_models') as discover:
            render(Surface(),llm=Model('current'),retrieve=None,version='v',model='current',albert_api_key='private-placeholder')
        discover.assert_not_called()
        self.assertNotIn('private-placeholder',json.dumps(Surface.session_state))
