"""Le corps reste lisible sans perdre les conditions ni les sources contrôlées."""
import unittest
from documentary_review import mark_excerpt, source_packets, render_claims, render_exam_fallback, review_exam_answer
from test_documentary_review import FakeLLM

class ConciseAnswerTests(unittest.TestCase):
    def test_shared_source_is_grouped_and_reservation_stays_visible(self):
        packets = source_packets(mark_excerpt('Le responsable valide après vérification.', title='Guide institutionnel', url='https://example.org/guide'))
        evidence = [{'document_id':'D1','quote':'Le responsable valide après vérification.','level':'documentaire'}]
        claims = [{'section':'condition','text':text,'evidence':evidence} for text in
                  ('Faire confirmer la procédure par le responsable avant toute utilisation.',
                   'Présenter les justificatifs pour la vérification.')]
        result = render_claims(claims, packets)
        visible, details = result.split('<details>', 1)
        self.assertIn('avant toute utilisation', visible)
        self.assertNotIn('Guide institutionnel', visible)
        self.assertEqual(details.count('Guide institutionnel'), 1)
        self.assertIn('https://example.org/guide', details)
        self.assertIn('[1]', visible)

    def test_unconfirmed_fallback_does_not_expand_internal_fiche(self):
        text = 'Le responsable valide le dispositif après vérification des pièces.'
        result = render_exam_fallback({}, question='Qui valide le dispositif ?', documents=mark_excerpt(text), mode='textes')
        visible, details = result.split('<details>', 1)
        self.assertIn('Réponse non confirmée', visible)
        self.assertNotIn(text, visible)
        self.assertIn(text, details)
        self.assertNotIn('<details open', result)

    def test_repair_can_start_with_confirmation_instead_of_vague_permission(self):
        proof = 'Le responsable doit confirmer les modalités avant utilisation.'
        bad = {'claims':[{'section':'decision','text':'Le dispositif est possible sous certaines conditions.',
                         'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}
        good = {'claims':[{'section':'etape','text':proof,
                          'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}
        llm = FakeLLM([bad,good])
        result = review_exam_answer(llm,question='Comment utiliser le dispositif ?',public='Collège',documents=mark_excerpt(proof),mode='textes')
        self.assertIn(proof,result)
        self.assertIn('démarches réellement établies',llm.prompts[-1])
        self.assertIn('une même affirmation',llm.prompts[-1])
        self.assertNotIn('possible sous certaines conditions',result)
