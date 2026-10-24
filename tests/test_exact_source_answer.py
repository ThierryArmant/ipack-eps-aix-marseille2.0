import html
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import architecture_comparison as ac
from exact_source_answer import exact_answer


class ExactSourceTests(unittest.TestCase):
    def run_extract(self, texts, choice):
        dr=ac._runtime.documentary_review
        docs='\n\n'.join(dr.mark_excerpt(text,path='data/test'+str(i)+'.txt',title='Source '+str(i))
                         for i,text in enumerate(texts))
        llm=SimpleNamespace(model='fake',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text=json.dumps(choice))))
        audit={}
        answer=exact_answer(llm,reviewer=dr,tracer=ac.TracedLLM,documents=docs,
            question='Comment effectuer cette opération ?',public='p',mode='ipack',academy='Aix-Marseille',audit=audit)
        return answer,audit,llm,docs

    def test_entire_source_conditions_negations_and_paths_are_copied_without_rewriting(self):
        texts=["Imprimer : si l’attestation est validée, [Dossier Natation] > [Imprimer].\nCette opération ne valide pas une nouvelle attestation.",
               'Valider une nouvelle attestation : autre opération.']
        answer,audit,llm,_=self.run_extract(texts,{'principal':'D1','complements':[]})
        self.assertIn(html.escape(texts[0].splitlines()[0]),answer)
        self.assertIn(html.escape(texts[0].splitlines()[1]),answer)
        self.assertNotIn(texts[1],answer)
        self.assertTrue(audit['exact_extracts']['no_business_rewriting'])
        self.assertEqual(ac.usage_summary(audit)['selection_calls'],1)
        self.assertEqual(ac.usage_summary(audit)['generation_calls'],0)
        llm.complete.assert_called_once()

    def test_main_and_other_tool_prerequisite_keep_exact_documents(self):
        answer,audit,_,_=self.run_extract(['Exporter les données.','Préalable : enregistrer dans un autre outil.'],
                                         {'principal':'D1','complements':['D2']})
        self.assertIn('Exporter les données.',answer)
        self.assertIn('Préalable : enregistrer dans un autre outil.',answer)
        self.assertEqual(audit['exact_extracts']['selected_ids'],['D1','D2'])

    def test_unknown_or_invented_answer_is_never_rendered(self):
        variants=[{'principal':'D99','complements':[]},
                  {'principal':None,'complements':['D1']},
                  {'principal':'D1','complements':[],'answer':'MENU_INVENTE'}]
        for choice in variants:
            with self.subTest(choice=choice):
                answer,audit,llm,_=self.run_extract(['Source vérifiable.'],choice)
                self.assertNotIn('MENU_INVENTE',answer)
                self.assertEqual(audit['exact_extracts']['status'],'invalid_selection_no_retry')
                llm.complete.assert_called_once()

    def test_source_html_is_escaped_and_not_executed(self):
        answer,_,_,_=self.run_extract(['<script>attaque()</script>\n[Menu] > [Action]'],
                                      {'principal':'D1','complements':[]})
        self.assertNotIn('<script>',answer)
        self.assertIn('&lt;script&gt;',answer)

    def test_empty_selection_does_not_claim_sources_do_not_exist(self):
        answer,audit,_,_=self.run_extract(['Source vérifiable.'],{'principal':None,'complements':[]})
        self.assertIn('ce choix reste à vérifier',answer)
        self.assertEqual(audit['exact_extracts']['status'],'no_source_selected')

    def test_g_reuses_a_search_and_never_calls_the_writer_or_albert(self):
        dr=ac._runtime.documentary_review
        docs=dr.mark_excerpt('Une action avec sa condition.',path='data/example.txt',title='Procédure')
        llm=SimpleNamespace(model='fake',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text='{"principal":"D1","complements":[]}')))
        retrieve=Mock(return_value=(docs,[],[],''))
        with patch('architecture_comparison.review_exam_answer',return_value='A') as review, \
             patch('architecture_comparison.AlbertLLM',side_effect=AssertionError('Albert interdit')):
            result=ac.run_comparison(llm=llm,retrieve=retrieve,question='Question',public='p',
                                    mode='examens',academy='Aix-Marseille',version='test',experimental='G')
        review.assert_called_once()
        retrieve.assert_called_once()
        self.assertEqual(result['branches']['G']['retrieved_documents'],docs)
        self.assertEqual(result['branches']['G']['usage']['calls'],1)
        self.assertEqual(result['branches']['G']['usage']['generation_calls'],0)

    def test_g_alone_has_one_selection_and_no_baseline_writer(self):
        dr=ac._runtime.documentary_review
        docs=dr.mark_excerpt('Action avec condition.',path='data/example.txt',title='Procédure')
        llm=SimpleNamespace(model='fake',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text='{"principal":"D1","complements":[]}')))
        retrieve=Mock(return_value=(docs,[],[],''))
        with patch('architecture_comparison.review_exam_answer') as review:
            result=ac.run_comparison(llm=llm,retrieve=retrieve,question='Question',public='p',
                mode='examens',academy='Aix-Marseille',version='test',experimental='G',compute_baseline=False)
        review.assert_not_called()
        retrieve.assert_called_once()
        llm.complete.assert_called_once()
        self.assertEqual(result['branches']['A']['usage']['calls'],0)
        self.assertEqual(result['branches']['A']['state'],'baseline_not_generated')

