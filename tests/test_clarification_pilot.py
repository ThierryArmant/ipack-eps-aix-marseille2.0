import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from documentary_review import mark_excerpt
from architecture_comparison import run_comparison
from clarification_pilot import assess_uncertainty, resume_clarification

DOC = mark_excerpt('L’écran Alpha concerne la consultation ; l’écran Bêta concerne la modification.',
                   path='guide_test.txt', title='Deux opérations distinctes')
ASK = dict(status='needs_clarification', reason='L’opération voulue n’est pas précisée.',
           question='Souhaitez-vous consulter ou modifier ?',
           options=[{'label':'Consulter une information', 'document_ids':['D1']},
                    {'label':'Modifier une information', 'document_ids':['D1']}])
CLEAR = dict(status='clear', reason='L’opération est précisée.', question='', options=[])
GAP = dict(status='source_gap', reason='Les extraits ne couvrent pas cette opération.', question='', options=[])

class FakeLLM:
    model = 'factice'
    temperature = 0
    def __init__(self, response):
        self.response = response
        self.prompts = []
    def complete(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(text=json.dumps(self.response, ensure_ascii=False))

class ClarificationPilotTests(unittest.TestCase):
    def start(self, status=ASK):
        llm = FakeLLM(status)
        retrieve = Mock(return_value=(DOC, [], [], ''))
        with patch('architecture_comparison.review_exam_answer', return_value='réponse A') as reviewed:
            result = run_comparison(llm=llm, retrieve=retrieve, question='Je souhaite accéder au dossier.',
                                    public='Lycée Général & Techno', mode='ipack', academy='Non précisée',
                                    version='test', experimental='C')
        return result, llm, retrieve, reviewed.call_count

    def test_uncertainty_suspends_C_before_any_answer(self):
        result, llm, retrieve, calls = self.start()
        self.assertEqual(calls, 1)  # A seulement ; C ne rédige pas une réponse supposée.
        self.assertEqual(result['branches']['C']['state'], 'waiting_for_user')
        self.assertNotIn('answer', result['branches']['C'])
        self.assertEqual(result['branches']['C']['usage']['calls'], 1)
        self.assertEqual(retrieve.call_count, 1)  # C examine les mêmes candidats que A.
        self.assertEqual(len(llm.prompts), 1)

    def test_clear_request_does_not_interrupt(self):
        result, llm, _, calls = self.start(CLEAR)
        self.assertEqual(calls, 2)
        self.assertEqual(result['branches']['C']['state'], 'completed')

    def test_source_gap_is_not_presented_as_user_ambiguity(self):
        result, _, _, calls = self.start(GAP)
        self.assertEqual(calls, 1)
        self.assertEqual(result['branches']['C']['state'], 'source_gap')
        self.assertNotIn('answer', result['branches']['C'])

    def test_fake_document_identifier_cannot_offer_a_choice(self):
        bad = copy.deepcopy(ASK)
        bad['options'][0]['document_ids'] = ['D999']
        result, _, _, calls = self.start(bad)
        self.assertEqual(calls, 1)
        self.assertEqual(result['branches']['C']['state'], 'error')
        self.assertNotIn('answer', result['branches']['C'])

    def test_confirmation_restarts_search_and_preserves_A_and_original(self):
        result, llm, _, _ = self.start()
        saved = copy.deepcopy(result)
        retrieve = Mock(return_value=(DOC, [], [], ''))
        with patch('clarification_pilot.review_exam_answer', return_value='réponse après précision') as reviewed:
            updated = resume_clarification(result, choice='Modifier une information', detail='Le dossier est déjà ouvert.',
                                           llm=llm, retrieve=retrieve, version='test')
        q = retrieve.call_args.args[0]
        self.assertTrue(q.startswith(result['question']))
        self.assertIn('Modifier une information', q)
        self.assertIn('Le dossier est déjà ouvert.', q)
        self.assertEqual(reviewed.call_args.kwargs['question'], q)
        self.assertEqual(updated['branches']['A'], saved['branches']['A'])
        self.assertEqual(updated['question'], saved['question'])
        self.assertEqual(result, saved)  # aucune mutation d’un résultat déjà téléchargé
        self.assertEqual(updated['branches']['C']['state'], 'completed')
        with self.assertRaises(ValueError):
            resume_clarification(updated, choice='Modifier une information', detail='', llm=llm, retrieve=retrieve, version='test')

    def test_forged_choice_cannot_restart(self):
        result, llm, _, _ = self.start()
        retrieve = Mock()
        with self.assertRaises(ValueError):
            resume_clarification(result, choice='Une affirmation cachée', detail='', llm=llm, retrieve=retrieve, version='test')
        retrieve.assert_not_called()

    def test_other_situation_requires_user_text(self):
        result, llm, _, _ = self.start()
        with self.assertRaises(ValueError):
            resume_clarification(result, choice='Autre situation', detail=' ', llm=llm, retrieve=None, version='test')

    def test_version_change_cannot_mix_measurements(self):
        result, llm, _, _ = self.start()
        with self.assertRaises(ValueError):
            resume_clarification(result, choice='Consulter une information', detail='', llm=llm, retrieve=None, version='nouvelle')

    def test_existing_common_clarification_can_resume_without_initial_model_call(self):
        llm = FakeLLM(CLEAR)
        result = run_comparison(llm=llm, retrieve=None, question='Inaptitude : dois-je attribuer zéro ou DI ?',
                                public='Lycée Général & Techno', mode='examens', academy='Aix-Marseille',
                                version='test', experimental='C')
        self.assertEqual(result['branches']['C']['state'], 'waiting_for_user')
        self.assertEqual(result['branches']['C']['usage']['calls'], 0)
        self.assertEqual(llm.prompts, [])

    def test_no_documents_does_not_spend_an_interpretation_call(self):
        llm = FakeLLM(ASK)
        result = assess_uncertainty(llm, question='q', public='p', mode='ipack', academy='a', documents='')
        self.assertEqual(result['status'], 'source_gap')
        self.assertEqual(llm.prompts, [])

    def test_duplicate_choices_are_rejected(self):
        bad = copy.deepcopy(ASK)
        bad['options'][1]['label'] = bad['options'][0]['label']
        with self.assertRaises(ValueError):
            assess_uncertainty(FakeLLM(bad), question='q', public='p', mode='ipack', academy='a', documents=DOC)

    def test_common_guide_remains_free_in_C(self):
        llm = FakeLLM(ASK)
        result = run_comparison(llm=llm, retrieve=None, question='aide moi je suis perdu',
                                public='Collège (DNB)', mode='ipack', academy='a', version='test', experimental='C')
        self.assertFalse(result['comparison_executed'])
        self.assertEqual(llm.prompts, [])

    def test_explicit_software_precision_recomputes_context_before_search(self):
        result, llm, _, _ = self.start()
        retrieve = Mock(return_value=(DOC, [], [], ''))
        with patch('clarification_pilot.review_exam_answer', return_value='réponse') as reviewed:
            updated = resume_clarification(result, choice='Modifier une information',
                                           detail='Dans Santorin, en bac professionnel.',
                                           llm=llm, retrieve=retrieve, version='test')
        self.assertEqual(retrieve.call_args.args[1:3], ('Lycée Pro / CAP', 'examens'))
        self.assertEqual(reviewed.call_args.kwargs['mode'], 'examens')
        self.assertEqual(updated['branches']['C']['resumed_context']['mode'], 'examens')
        self.assertEqual(updated['initial_context']['mode'], 'ipack')

    def test_explicit_rejected_software_is_not_used_for_routing_but_preserved_for_answer(self):
        result,llm,_,_=self.start()
        retrieve=Mock(return_value=(DOC,[],[],''))
        with patch('clarification_pilot.review_exam_answer',return_value='réponse') as reviewed:
            updated=resume_clarification(result,choice='Autre situation',
                                         detail="Ce n'est pas Santorin : je parle de Pronote.",
                                         llm=llm,retrieve=retrieve,version='test')
        self.assertNotIn('Santorin',retrieve.call_args.args[0])
        self.assertIn("Ce n'est pas Santorin",reviewed.call_args.kwargs['question'])
        self.assertEqual(reviewed.call_args.kwargs['mode'],'ipack')
        self.assertEqual(updated['branches']['C']['confirmed_retrieval']['plan']['scope']['rejected'],['santorin'])

    def test_free_text_alone_resumes_without_invented_choice(self):
        result, llm, _, _ = self.start()
        retrieve = Mock(return_value=(DOC, [], [], ''))
        with patch('clarification_pilot.review_exam_answer', return_value='réponse'):
            updated = resume_clarification(result, choice=None, detail='Je veux consulter le dossier déjà ouvert.',
                                           llm=llm, retrieve=retrieve, version='test')
        self.assertEqual(updated['branches']['A'], result['branches']['A'])
        self.assertIn('Je veux consulter le dossier déjà ouvert.', updated['branches']['C']['resumed_question'])
        self.assertNotIn('Modifier une information', updated['branches']['C']['resumed_question'])

    def test_empty_confirmation_does_not_call_search(self):
        result, llm, _, _ = self.start()
        retrieve = Mock()
        with self.assertRaises(ValueError):
            resume_clarification(result, choice=None, detail='', llm=llm, retrieve=retrieve, version='test')
        retrieve.assert_not_called()
