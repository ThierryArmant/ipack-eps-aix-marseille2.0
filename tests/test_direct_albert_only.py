"""Exécute les vrais blocs de routage de l'application, sans Streamlit ni réseau."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


TREE=ast.parse(Path('app.py').read_text())


def assigns(node,name):
    return isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)


def execute(node,env):
    exec(compile(ast.Module(body=[node],type_ignores=[]),'app.py','exec'),env)


class DirectAlbertOnlyTests(unittest.TestCase):
    def route(self,state,mode):
        constructor=Mock(return_value='albert-direct')
        env=dict(st=SimpleNamespace(session_state=state,secrets={'ALBERT_API_KEY':'placeholder','ALBERT_MODEL':'gpt-oss-120b'}),
                 mode=mode,_test_model='gpt-4.1',_test_gpt41=True,_single_document_test=True,
                 _short_prompt_test=True,_generation_llm='ordinary-writer',
                 _generation_runtime=SimpleNamespace(albert_adapter=SimpleNamespace(AlbertLLM=constructor)))
        assignment=next(n for n in ast.walk(TREE) if assigns(n,'_albert_only_trial'))
        execute(assignment,env)
        branches=[n for n in ast.walk(TREE) if isinstance(n,ast.If) and isinstance(n.test,ast.Name)
                  and n.test.id=='_albert_only_trial']
        for branch in branches:
            if any(assigns(n,'_test_model') or assigns(n,'_generation_llm') for n in branch.body):
                execute(branch,env)
        env['_orientation_active']=True
        orientation=next(n for n in branches if any(assigns(a,'_orientation_active') for a in n.body))
        execute(orientation,env)
        return env,constructor

    def test_admin_trial_overrides_pending_mini_tests_and_disables_orientation(self):
        env,constructor=self.route({'is_admin':True,'admin_albert_only':True},'examens')
        self.assertEqual(env['_generation_llm'],'albert-direct')
        self.assertIsNone(env['_test_model'])
        self.assertFalse(env['_test_gpt41'])
        self.assertFalse(env['_single_document_test'])
        self.assertFalse(env['_orientation_active'])
        constructor.assert_called_once_with('placeholder','gpt-oss-120b',temperature=0.0,allow_paused_test=True)

    def test_switch_off_or_non_admin_preserves_ordinary_routing(self):
        for state,mode in [({'is_admin':False},'examens'),
                           ({'is_admin':True,'admin_albert_only':False},'examens'),
                           ({'is_admin':True,'admin_albert_only':True},'pedagogie')]:
            with self.subTest(state=state,mode=mode):
                env,constructor=self.route(state,mode)
                self.assertEqual(env['_generation_llm'],'ordinary-writer')
                constructor.assert_not_called()

    def test_trial_has_no_paid_repair_and_other_mode_retains_its_policy(self):
        review=next(n for n in ast.walk(TREE) if isinstance(n,ast.Call)
                    and isinstance(n.func,ast.Name) and n.func.id=='review_exam_answer')
        repair=next(k.value for k in review.keywords if k.arg=='repair_enabled')
        expr=compile(ast.Expression(body=repair),'app.py','eval')
        self.assertFalse(eval(expr,{'_test_model':None,'_albert_only_trial':True}))
        self.assertTrue(eval(expr,{'_test_model':None,'_albert_only_trial':False}))
