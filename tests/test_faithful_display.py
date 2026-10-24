import html
import ast
from pathlib import Path
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from exact_source_answer import render_exact_sources
from generation_runtime import load_runtime


class FaithfulDisplayTests(unittest.TestCase):
    def test_metadata_prefix_never_hides_following_business_lines(self):
        reviewer=SimpleNamespace(_LEVELS={},evidence_label=lambda *args:'Source')
        body='[DOCUMENT: exemple]\nSi le lot est noté, ne pas le supprimer.'
        packet=dict(id='D1',title='Source',passages=[dict(id='D1P1',text=body,scope={})])
        report={};out=render_exact_sources([packet],reviewer,report)
        self.assertIn(html.escape(body),out)
        self.assertEqual(report['hidden_non_business_passages'],[])

    def test_actual_app_branch_returns_exact_text_and_records_one_selection(self):
        runtime=load_runtime();dr=runtime.documentary_review
        tree=ast.parse(Path('app.py').read_text())
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If)
            and isinstance(n.test,ast.Name) and n.test.id=='_faithful_trial'
            and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute)
                    and c.func.attr=='exact_answer' for c in ast.walk(n)))
        llm=SimpleNamespace(model='fake',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text='{"principal":"D1","complements":[]}')))
        docs=dr.mark_excerpt('Si la condition manque, ne pas valider.',path='data/example.txt',title='Procédure')
        env=dict(_faithful_trial=True,_mixed_trial=False,_generation_runtime=runtime,_generation_llm=llm,
                 TracedLLM=dr.TracedLLM,prompt='Question',niveau_actuel_form='p',
                 contexte_complet_ia=docs,diagnostic_ia={},academie_reponse='Aix-Marseille',
                 mode='examens',usage_ia={})
        exec(compile(ast.Module(body=[branch],type_ignores=[]),'app.py','exec'),env)
        self.assertIn('Si la condition manque, ne pas valider.',env['reponse_ia'])
        self.assertEqual(env['_doc_utilises'],{'D1'})
        self.assertEqual(dr.usage_summary(env['usage_ia'])['calls'],1)
        self.assertEqual(dr.usage_summary(env['usage_ia'])['selection_calls'],1)
        self.assertEqual(dr.usage_summary(env['usage_ia'])['generation_calls'],0)
        llm.complete.assert_called_once()

    def test_titles_not_duplicated_references_grouped_and_conditions_untouched(self):
        dr=load_runtime().documentary_review
        text='[SITUATION: Procédure]\nSi la validation manque, ne pas importer.\n[Menu] > [Importer] après validation.'
        p=dr.source_packets(dr.mark_excerpt(text,path='data/test.txt',title='[SITUATION: Procédure]'))
        report={};out=render_exact_sources(p,dr,report)
        self.assertEqual(out.count('<h3>'),1)
        self.assertEqual(out.count('<details>'),1)
        self.assertIn('Si la validation manque, ne pas importer.',html.unescape(out))
        self.assertIn('[Menu] > [Importer] après validation.',html.unescape(out))
        hidden={r['id'] for r in report['hidden_non_business_passages']}
        for span in p[0]['passages']:
            if span['id'] not in hidden:
                self.assertIn(html.escape(span['text']),out)

    def test_different_scopes_stay_attached_and_are_not_merged(self):
        reviewer=SimpleNamespace(_LEVELS={}, evidence_label=lambda evidence,packet,labels:evidence['scope']['label'])
        p=[dict(id='D1',title='Procédure',passages=[
            dict(id='D1P1',text='Condition nationale.',scope={'label':'National'}),
            dict(id='D1P2',text='Circuit local à confirmer ailleurs.',scope={'label':'Académique'}),
            dict(id='D1P3',text='Autre condition nationale.',scope={'label':'National'})])]
        out=render_exact_sources(p,reviewer,{})
        self.assertEqual(out.count('National'),1)
        self.assertEqual(out.count('Académique'),1)
        self.assertIn('[1.1]',out)
        self.assertIn('[1.2]',out)

    def test_runtime_contains_exact_helper_and_has_no_writer_call(self):
        dr=load_runtime().documentary_review
        runtime=load_runtime()
        llm=SimpleNamespace(model='fake',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text='{"principal":"D1","complements":[]}')))
        docs=dr.mark_excerpt('Agir seulement après validation.',path='data/example.txt',title='Procédure')
        audit={}
        out=runtime.exact_source_answer.exact_answer(llm,reviewer=dr,tracer=dr.TracedLLM,
            documents=docs,question='Question',public='p',mode='ipack',academy='Aix-Marseille',audit=audit)
        self.assertIn('Agir seulement après validation.',out)
        llm.complete.assert_called_once()
        self.assertEqual(dr.usage_summary(audit)['generation_calls'],0)
        self.assertEqual(dr.usage_summary(audit)['selection_calls'],1)
        self.assertEqual(audit['rendered_answer'],out)
