import unittest
from unittest.mock import patch
from types import SimpleNamespace
from architecture_comparison import run_comparison, interpret, render


class FakeLLM:
    model = 'fake'
    temperature = 0
    def __init__(self, output):
        self.output = output
        self.prompts = []
    def complete(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(text=self.output)


class ArchitectureComparisonTests(unittest.TestCase):
    def test_branches_keep_original_question_and_context(self):
        llm = FakeLLM('{"action":"chercher","objet":"accès","incertitudes":"","recherche":"accès second établissement"}')
        queries = []
        def retrieve(*args):
            queries.append(args)
            return 'preuves', [], [], ''
        with patch('architecture_comparison.review_exam_answer', return_value='réponse') as review:
            result = run_comparison(llm=llm, retrieve=retrieve, question='question originale',
                                    public='Collège (DNB)', mode='ipack', academy='Grenoble', version='test')
        self.assertEqual(queries[0], ('question originale', 'Collège (DNB)', 'ipack', None))
        self.assertEqual(queries[1], ('question originale', 'Collège (DNB)', 'ipack', 'accès second établissement'))
        for call in review.call_args_list:
            self.assertEqual(call.kwargs['question'], 'question originale')
            self.assertEqual(call.kwargs['academy'], 'Grenoble')
            self.assertNotIn('selection_policy', call.kwargs)
        self.assertEqual(result['branches']['B']['usage']['calls'], 1)
        self.assertFalse(result['branches']['B']['usage']['complete'])

    def test_invalid_interpretation_does_not_silently_fallback(self):
        queries = []
        with patch('architecture_comparison.review_exam_answer', return_value='ok'):
            result = run_comparison(llm=FakeLLM('{"recherche":"inventée"}'),
                                    retrieve=lambda *args: (queries.append(args) or ('docs', [], [], '')),
                                    question='question', public='public', mode='ipack', academy='académie', version='test')
        self.assertEqual(len(queries), 1)
        self.assertIn('error', result['branches']['B'])
        self.assertNotIn('answer', result['branches']['B'])
        self.assertEqual(result['branches']['A']['answer'], 'ok')

    def test_non_admin_cannot_render_or_call(self):
        st = SimpleNamespace(session_state={})
        render(st, llm=None, retrieve=None, version='test', model='fake')

    def test_interpreter_rejects_model_context_override(self):
        with self.assertRaises(ValueError):
            interpret(FakeLLM('{"action":"a","objet":"o","incertitudes":"","recherche":"q","mode":"textes"}'),
                      'q', 'p', 'ipack', 'a')

    def test_opening_panel_with_existing_result_does_not_generate(self):
        class Surface:
            session_state = {'is_admin': True}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def expander(self, *args, **kwargs): return self
            def form(self, *args, **kwargs): return self
            def caption(self, *args, **kwargs): pass
            info = caption
            warning = caption
            def text_area(self, *args, **kwargs): return 'question'
            def text_input(self, *args, **kwargs): return 'académie'
            def selectbox(self, label, values): return values[0]
            def form_submit_button(self, *args, **kwargs): return False
        llm = FakeLLM('ne doit pas être appelé')
        render(Surface(), llm=llm, retrieve=None, version='test', model='fake')
        self.assertEqual(llm.prompts, [])

    def test_generation_is_counted_once_even_when_reviewer_traces(self):
        from documentary_review import TracedLLM
        llm = FakeLLM('{"action":"chercher","objet":"accès","incertitudes":[],"recherche":"accès"}')
        def reviewed(model, *, audit, **kwargs):
            TracedLLM(model, audit).complete('rédaction')
            return 'réponse'
        with patch('architecture_comparison.review_exam_answer', side_effect=reviewed):
            result = run_comparison(llm=llm, retrieve=lambda *args: ('preuves', [], [], ''),
                                    question='q', public='p', mode='ipack', academy='a', version='test')
        self.assertEqual(len(llm.prompts), 3)
        self.assertEqual(result['branches']['A']['usage']['calls'], 1)
        self.assertEqual(result['branches']['B']['usage']['calls'], 2)
        self.assertEqual(result['branches']['B']['interpretation']['incertitudes'], '')

    def test_invalid_uncertainty_list_is_rejected(self):
        with self.assertRaises(ValueError):
            interpret(FakeLLM('{"action":"a","objet":"o","incertitudes":[{"fait":"inventé"}],"recherche":"q"}'),
                      'q', 'p', 'ipack', 'a')
