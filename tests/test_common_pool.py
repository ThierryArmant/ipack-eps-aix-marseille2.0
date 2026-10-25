import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from exact_source_answer import exact_answer, media_text
from generation_runtime import load_runtime

class CommonPoolTests(unittest.TestCase):
    def run_case(self, choice=None, phrase=None, extra='Exporter les notes.'):
        dr=load_runtime().documentary_review
        choice=choice or dict(principal='D1',complements=[],passages=['D1P1'])
        phrase=phrase or dict(texte=extra,passages=['D2P1'])
        mini=SimpleNamespace(model='mini',temperature=0,complete=Mock(return_value=SimpleNamespace(text=json.dumps(choice))))
        writer=SimpleNamespace(model='albert',temperature=0,complete=Mock(return_value=SimpleNamespace(text=json.dumps({'phrases':[phrase]}))))
        docs=dr.mark_excerpt('Consulter les notes.',path='data/one.txt',title='Notes')+'\n\n'+dr.mark_excerpt(extra,path='data/two.txt',title='Export')
        audit={}
        out=exact_answer(writer,selector_llm=mini,synthesis=True,reviewer=dr,tracer=dr.TracedLLM,documents=docs,question='Comment exporter ?',public='p',mode='examens',academy='Non précisée',audit=audit)
        return out,audit,mini,writer

    def test_recovery_same_pool_numbers_and_media(self):
        out,a,m,w=self.run_case()
        m.complete.assert_called_once();w.complete.assert_called_once()
        r=a['exact_extracts']
        self.assertEqual(r['recovered_from_pool'],['D2P1'])
        self.assertEqual(r['focused_passage_ids'],['D2P1'])
        self.assertIn('<strong>2.</strong>',out)
        self.assertEqual(media_text(a,''),'Exporter les notes.')
        self.assertEqual(r['mini_proposed_passage_ids'],['D1P1'])
        payload=json.loads(w.complete.call_args.args[0].split('DONNEES :\n')[1])
        self.assertIn('D1P1',str(payload));self.assertIn('D2P1',str(payload))

    def test_add_owner_without_retry_preserve_raw(self):
        out,a,m,w=self.run_case(dict(principal='D1',complements=[],passages=['D2P1']))
        self.assertEqual(a['exact_extracts']['raw_selection']['complements'],[])
        self.assertEqual(a['exact_extracts']['complement_ajoute_par_reference'][0]['document_id'],'D2')
        self.assertEqual(m.complete.call_count,1)

    def test_unknown_passage_rejected_before_writer(self):
        out,a,m,w=self.run_case(dict(principal='D1',complements=[],passages=['D9P1']))
        w.complete.assert_not_called()
        self.assertEqual(a['exact_extracts']['status'],'invalid_selection_no_retry')

    def test_writer_out_of_pool_is_not_used(self):
        out,a,m,w=self.run_case(phrase=dict(texte='Invention.',passages=['D99P1']))
        self.assertEqual(a['short_answer']['status'],'nothing_kept')
        self.assertNotIn('Invention.',out)
        self.assertEqual(w.complete.call_count,1)

    def test_budget_has_no_writer_call(self):
        with patch('short_answer.build_prompt',return_value='x'*40001):
            out,a,m,w=self.run_case()
        w.complete.assert_not_called()
        self.assertEqual(a['exact_extracts']['pool_status'],'budget_exceeded_no_writer_call')

    def test_numeric_pool_reference_rejected(self):
        out,a,m,w=self.run_case(phrase=dict(texte='Consulter les notes.',passages=[1]))
        self.assertEqual(a['short_answer']['status'],'nothing_kept')
