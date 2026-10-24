"""Réserve explicite rétablie depuis sa preuve, sans nouvelle génération."""
import unittest
from documentary_review import mark_excerpt,review_exam_answer
from test_documentary_review import FakeLLM

class LiteralReserveFormatTests(unittest.TestCase):
    def test_faq_non_entailment_replaces_obligation_without_repair(self):
        text = ("Q3 : Comment transmettre les pièces ?\n- R3 : La description du dossier ne suffit pas à confirmer la possibilité de déposer les pièces dans ce module. Le mode de transmission des pièces reste à vérifier auprès de l'autorité qui les demande.")
        bad = {'claims':[{'section':'etape','text':'Les pièces doivent être déposées dans ce module.',
                         'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}
        llm,audit=FakeLLM([bad]),{}
        answer=review_exam_answer(llm,question='Comment déposer les pièces dans ce module ?',public='Collège',
                                  documents=mark_excerpt(text),audit=audit)
        self.assertEqual(len(llm.prompts),1)
        self.assertTrue(audit['documentary_limit_extraction'])
        self.assertFalse(audit['repair_performed'])
        self.assertIn('ne suffit pas à confirmer',answer)
        self.assertNotIn('Q3 :',answer)
        self.assertFalse(audit['final_rejections'])

    def test_documentary_limit_does_not_hide_an_unsupported_neighbor_prescription(self):
        from claim_guards import unsupported_certainty
        proof='La description du dossier ne suffit pas à confirmer la possibilité de déposer les pièces dans ce module.'
        self.assertTrue(unsupported_certainty('Les pièces doivent être déposées dans ce module.',[proof]))

    def test_limit_format_alias_does_not_trigger_paid_repair(self):
        proof='Le lieu de transmission des pièces reste à vérifier auprès du responsable.'
        llm=FakeLLM([{'claims':[{'section':'limit','text':proof,
                             'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}]);audit={}
        review_exam_answer(llm,question='Où transmettre les pièces ?',public='Collège',documents=mark_excerpt(proof),audit=audit)
        self.assertEqual(len(llm.prompts),1)
        self.assertEqual(audit['normalized_section_aliases'],1)
        self.assertFalse(audit['repair_performed'])
        self.assertEqual(audit['accepted_claims'][0]['section'],'limite')
