import copy
import hashlib
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
import architecture_comparison as ac


class AlbertSelectedGTests(unittest.TestCase):
    def saved(self):
        dr=ac._runtime.documentary_review
        original='\n\n'.join(dr.mark_excerpt(text,path='data/t'+str(i)+'.txt',title='Source '+str(i))
            for i,text in enumerate(['Source voisine.','Procédure principale avec sa condition.']))
        packets=dr.source_packets(original)
        return dict(experimental='G',question='Question',public='p',mode='ipack',academy='Aix-Marseille',
            model='gpt-4o-mini',temperature=0,version='ancienne',run_id='ancien',branches={'G':dict(
                model='gpt-4o-mini',temperature=0,elapsed_seconds=1,answer='Extraits',
                usage={'calls':1},retrieved_documents=original,audit={'exact_extracts':dict(
                    status='rendered_exact_sources',selected_ids=['D2'],selected_sources=[packets[1]],
                    context_sha256=hashlib.sha256(original.encode()).hexdigest())})})

    def test_reuses_only_selected_text_and_preserves_context_no_repair(self):
        saved=self.saved(); before=copy.deepcopy(saved)
        model=ac.AlbertLLM('placeholder','gpt-oss-120b',temperature=0)
        model.complete=Mock(return_value=SimpleNamespace(text='résultat'))
        def reviewed(llm,*,audit,**kwargs):
            ac.TracedLLM(llm,audit).complete('rédaction')
            return 'Réponse Albert'
        with patch('architecture_comparison.review_exam_answer',side_effect=reviewed) as review:
            result=ac.write_selected_g_with_albert(saved,model,version='nouvelle')
        kw=review.call_args.kwargs
        self.assertFalse(kw['repair_enabled'])
        self.assertNotIn('Source voisine.',kw['documents'])
        self.assertIn('Procédure principale avec sa condition.',kw['documents'])
        self.assertEqual(kw['question'],saved['question'])
        self.assertEqual(kw['academy'],saved['academy'])
        self.assertEqual(result['new_usage']['calls'],1)
        self.assertFalse(result['branches']['H']['mini_called'])
        self.assertEqual(result['baseline_branch'],'G')
        self.assertTrue(result['branches']['G']['historical_result'])
        self.assertEqual(saved,before)
        model.complete.assert_called_once()

    def test_tampered_selection_or_context_rejected_before_model_call(self):
        model=ac.AlbertLLM('placeholder','gpt-oss-120b');model.complete=Mock()
        for kind in ['text','context','ids']:
            saved=self.saved()
            if kind=='text':saved['branches']['G']['audit']['exact_extracts']['selected_sources'][0]['text']='Inventé'
            if kind=='context':saved['branches']['G']['retrieved_documents']+='Ajout'
            if kind=='ids':saved['branches']['G']['audit']['exact_extracts']['selected_ids']=['D99']
            with self.assertRaises(ValueError): ac.write_selected_g_with_albert(saved,model,version='v')
        model.complete.assert_not_called()

    def test_no_fallback_provider_is_accepted(self):
        with self.assertRaises(ValueError):
            ac.write_selected_g_with_albert(self.saved(),SimpleNamespace(model='gpt'),version='v')

    def test_service_failure_is_not_retried(self):
        model=ac.AlbertLLM('placeholder','gpt-oss-120b')
        model.complete=Mock(side_effect=ac.AlbertError('Service indisponible'))
        def reviewed(llm,*,audit,**kwargs):
            return ac.TracedLLM(llm,audit).complete('rédaction')
        with patch('architecture_comparison.review_exam_answer',side_effect=reviewed):
            result=ac.write_selected_g_with_albert(self.saved(),model,version='v')
        self.assertIn('error',result['branches']['H'])
        model.complete.assert_called_once()
