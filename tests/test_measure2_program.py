import unittest
import knowledge_catalog as kc
from documentary_review import coherence_errors, mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

GT = 'Lycée Général & Techno'
PRO = 'Lycée Pro / CAP'


class Measure2ProgramTests(unittest.TestCase):
    def test_sport_facility_never_returns_software_access(self):
        for q in ('CAP : notre installation est inutilisable, comment organiser le CCF ?',
                  'Les travaux bloquent cette installation : quelles possibilités pour le CAP ?',
                  'iPackEPS : notre installation sportive est fermée, que déclarer ?'):
            for mode in ('examens', 'ipack'):
                answer, source = kc.documented_response(q, PRO, mode)
                self.assertNotEqual(source.get('title'), 'Accès iPackEPS et portail ESTEREL', q)
        answer, source = kc.documented_response('Comment installer iPackEPS sur mon ordinateur ?', GT, 'ipack')
        self.assertEqual(source['title'], 'Accès iPackEPS et portail ESTEREL')

    def test_certificate_period_already_given_is_not_requested_again(self):
        for q in ('Un certificat médical couvre la date de son CCF. Quelle démarche effectuer ?',
                  'CAP : certificat médical valable le jour du CCF, comment traiter son absence ?'):
            self.assertEqual(kc.clarification(q, PRO if 'CAP' in q else GT), '')
        self.assertTrue(kc.clarification('Élève dispensé : je mets DI ?', GT))
        self.assertIn('diplôme', kc.clarification('Certificat médical couvrant le CCF : je saisis quoi ?', PRO))

    def test_explicit_contradiction_rejected_but_conditional_branches_preserved(self):
        self.assertTrue(coherence_errors([{'section': 'decision', 'text': 'Non, il peut obtenir le 20/20.'}], 'A-t-il droit au 20/20 ?'))
        self.assertTrue(coherence_errors([
            {'section': 'decision', 'text': 'Il peut obtenir le 20/20.'},
            {'section': 'condition', 'text': 'Il ne peut pas obtenir le 20/20.'}], 'Statut sportif ?'))
        self.assertFalse(coherence_errors([
            {'section': 'decision', 'text': 'Il peut obtenir le 20/20 si les conditions sont réunies.'},
            {'section': 'condition', 'text': 'Il ne peut pas obtenir le 20/20 si le statut requis manque.'}], 'Statut sportif ?'))
        self.assertFalse(coherence_errors([{'section': 'decision', 'text': 'Non, il peut obtenir le 20/20 sous réserve du statut requis.'}], 'Est-ce automatique ?'))

    def test_inconsistent_proposal_is_repaired_before_display(self):
        doc = mark_excerpt('Le candidat peut obtenir le 20/20 sous réserve de justifier le statut requis.', title='Statut sportif')
        bad = {'section': 'decision', 'text': 'Non, le candidat peut obtenir le 20/20.',
               'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}
        good = {**bad, 'text': 'Le candidat peut obtenir le 20/20 sous réserve de justifier le statut requis.'}
        llm, audit = FakeLLM([{'claims': [bad]}, {'claims': [good]}]), {}
        result = review_exam_answer(llm, question='Le candidat a-t-il droit au 20/20 ?', public=GT, documents=doc, audit=audit)
        self.assertNotIn('Non,', result)
        self.assertTrue(audit['initial_rejections'])
        self.assertEqual(len(llm.prompts), 2)
