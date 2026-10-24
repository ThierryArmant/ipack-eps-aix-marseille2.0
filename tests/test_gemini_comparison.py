import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from architecture_comparison import run_comparison, GEMINI_SCOPE_INSTRUCTIONS, GEMINI_SCOPE_VERSION


class GeminiComparisonTests(unittest.TestCase):
    def run_variant(self, retrieve, review):
        model = SimpleNamespace(model='gpt-4o-mini', temperature=0)
        result = run_comparison(llm=model, retrieve=retrieve,
            question='Comment réaffecterun lotà un autre examinateur ?',
            public='Lycée Général & Techno', mode='examens', academy='Aix-Marseille',
            version='test', experimental='E')
        return model, result

    def test_same_documents_model_context_and_controls_only_added_instructions(self):
        retrieve = Mock(return_value=('preuves identiques', ['source'], ['diagnostic'], ''))
        with patch('architecture_comparison.review_exam_answer', return_value='réponse') as review, \
             patch('architecture_comparison.AlbertLLM', side_effect=AssertionError('Albert interdit')), \
             patch('architecture_comparison.interpret', side_effect=AssertionError('appel supplémentaire')):
            model, result = self.run_variant(retrieve, review)
        self.assertEqual(retrieve.call_count, 1)
        self.assertEqual(review.call_count, 2)
        a, e = review.call_args_list
        self.assertIs(a.args[0], model)
        self.assertIs(e.args[0], model)
        for key in ['question', 'public', 'documents', 'academy', 'mode']:
            self.assertEqual(a.kwargs[key], e.kwargs[key])
        self.assertEqual(e.kwargs['instructions'], a.kwargs['instructions'] + '\n\n' + GEMINI_SCOPE_INSTRUCTIONS)
        self.assertNotIn('instruction_variant', result['branches']['A'])
        self.assertEqual(result['branches']['E']['instruction_variant']['id'], GEMINI_SCOPE_VERSION)
        self.assertTrue(result['branches']['E']['initial_retrieval_reused_from_A'])

    def test_failed_retrieval_does_not_start_a_different_search_for_e(self):
        retrieve = Mock(side_effect=RuntimeError('recherche indisponible'))
        with patch('architecture_comparison.review_exam_answer') as review:
            _, result = self.run_variant(retrieve, review)
        retrieve.assert_called_once()
        review.assert_not_called()
        self.assertIn('error', result['branches']['E'])

    def test_common_direct_answer_does_not_generate_either_column(self):
        retrieve = Mock(side_effect=AssertionError('aucune recherche attendue'))
        with patch('architecture_comparison.prepare_question', return_value={'kind':'documentee'}), \
             patch('architecture_comparison.review_exam_answer') as review:
            _, result = self.run_variant(retrieve, review)
        self.assertFalse(result['comparison_executed'])
        self.assertEqual(result['branches'], {})
        retrieve.assert_not_called()
        review.assert_not_called()

    def test_actual_calls_counted_separately_without_analysis_call(self):
        from architecture_comparison import TracedLLM
        model = SimpleNamespace(model='gpt-4o-mini', temperature=0,
                                complete=Mock(return_value=SimpleNamespace(text='réponse')))
        def reviewed(llm, *, audit, **kwargs):
            TracedLLM(llm, audit).complete('rédaction')
            return 'réponse'
        with patch('architecture_comparison.review_exam_answer', side_effect=reviewed):
            result = run_comparison(llm=model, retrieve=lambda *args: ('preuves', [], [], ''),
                question='question', public='p', mode='examens', academy='Aix-Marseille',
                version='test', experimental='E')
        self.assertEqual(model.complete.call_count, 2)
        self.assertEqual(result['branches']['A']['usage']['calls'], 1)
        self.assertEqual(result['branches']['E']['usage']['calls'], 1)
