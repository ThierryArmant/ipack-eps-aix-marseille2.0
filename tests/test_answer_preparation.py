import unittest
from documentary_review import mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

class AnswerPreparationTests(unittest.TestCase):
    def test_outline_stays_in_audit_without_extra_call_or_public_leak(self):
        outline={'request':'choisir une procédure','known':[],'missing':['symptôme exact'],
                 'branches':[{'condition':'si le dossier est ouvert','outcome':'corriger la valeur','passage_ids':['D1P1']}]}
        llm=FakeLLM([{'answer_outline':outline,'claims':[{
            'section':'etape','text':'Si le dossier est ouvert, corriger la valeur.',
            'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}])
        audit={}
        result=review_exam_answer(llm,question='Comment corriger ?',public='GT',documents=mark_excerpt('Si le dossier est ouvert, corriger la valeur.'),audit=audit)
        self.assertEqual(len(llm.prompts),1)
        self.assertEqual(audit['answer_outline'],outline)
        self.assertEqual(audit['final_answer_outline'],outline)
        self.assertNotIn('symptôme exact',result)
        self.assertIn('Si le dossier est ouvert',result)
    def test_outline_alone_is_never_an_answer_or_evidence(self):
        llm=FakeLLM([{'answer_outline':{'branches':[{'outcome':'autoriser sans source'}]},'claims':[]}])
        result=review_exam_answer(llm,question='Comment faire ?',public='GT',documents=mark_excerpt('Le guide décrit le dossier.'))
        self.assertNotIn('autoriser sans source',result)
        self.assertEqual(len(llm.prompts),1)
