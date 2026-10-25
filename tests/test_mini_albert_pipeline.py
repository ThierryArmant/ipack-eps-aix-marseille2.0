import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from exact_source_answer import exact_answer
from generation_runtime import load_runtime


class MixedPipelineTests(unittest.TestCase):
    def run_case(self, choice):
        dr=load_runtime().documentary_review
        mini=SimpleNamespace(model='gpt-4o-mini',temperature=0,complete=Mock(
            return_value=SimpleNamespace(text=json.dumps(choice))))
        albert=SimpleNamespace(model='gpt-oss-120b',temperature=0,complete=Mock(
            return_value=SimpleNamespace(text=json.dumps({'phrases':[
                {'texte':'Ouvrez le menu [Dossier].','passages':['D1P1']}]}))))
        docs=dr.mark_excerpt('Ouvrez le menu [Dossier].',path='data/exemple.txt',title='Action')
        audit={}
        answer=exact_answer(albert,selector_llm=mini,synthesis=True,reviewer=dr,tracer=dr.TracedLLM,
            documents=docs,question='Où ouvrir le dossier ?',public='p',mode='ipack',
            academy='Non précisée',audit=audit)
        return mini,albert,audit,answer

    def test_one_mini_selection_then_one_albert_synthesis(self):
        mini,albert,a,out=self.run_case({'principal':'D1','complements':[],'passages':['D1P1']})
        mini.complete.assert_called_once();albert.complete.assert_called_once()
        self.assertEqual([(c['stage'],c['model']) for c in a['calls']],
            [('selection','gpt-4o-mini'),('short_answer','gpt-oss-120b')])
        self.assertIn('Ouvrez le menu [Dossier].',out)
        prompt=albert.complete.call_args.args[0]
        self.assertNotIn('Choisis les sources nécessaires',prompt)
        self.assertEqual(a['exact_extracts']['selected_ids'],['D1'])

    def test_invalid_selection_does_not_call_albert(self):
        mini,albert,a,_=self.run_case({'principal':'D99','complements':[],'passages':['D99P1']})
        mini.complete.assert_called_once();albert.complete.assert_not_called()
        self.assertEqual(a['exact_extracts']['status'],'invalid_selection_no_retry')

    def test_no_source_does_not_call_albert(self):
        mini,albert,a,_=self.run_case({'principal':None,'complements':[],'passages':[]})
        mini.complete.assert_called_once();albert.complete.assert_not_called()
        self.assertEqual(a['exact_extracts']['status'],'no_source_selected')


if __name__=='__main__':unittest.main()
