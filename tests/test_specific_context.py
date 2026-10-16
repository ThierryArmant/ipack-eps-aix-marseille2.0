import unittest
from documentary_review import mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

class SpecificContextTests(unittest.TestCase):
    def test_specific_document_is_not_completed_by_generic_program_rules(self):
        docs=mark_excerpt('Le responsable peut autoriser la modification après validation du dossier.',title='Procédure précise',priority=300)
        docs+='\n'+mark_excerpt('REPÈRES DOCUMENTAIRES PAR EXAMEN : La modification est automatique.',title='Résumé général',origin='program')
        llm=FakeLLM([{'claims':[{'section':'decision','text':'Le responsable peut autoriser la modification après validation du dossier.', 'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}])
        audit={}
        answer=review_exam_answer(llm,question='Comment modifier le dossier ?',public='GT',documents=docs,audit=audit)
        self.assertNotIn('La modification est automatique',llm.prompts[0])
        self.assertEqual(audit['excluded_generic_program_documents'],['D2'])
        self.assertEqual(audit['model_document_ids'],['D1'])
        self.assertIn('après validation du dossier',answer)
        self.assertEqual(len(llm.prompts),1)
    def test_non_specific_search_keeps_existing_program_context(self):
        docs=mark_excerpt('Le guide décrit la modification.',title='Guide')+'\n'+mark_excerpt('Le résultat calculé vaut 3.',title='Calcul',origin='program')
        llm=FakeLLM([{'claims':[]}]);audit={}
        review_exam_answer(llm,question='Que calcule-t-on ?',public='GT',documents=docs,audit=audit)
        self.assertEqual(audit['model_document_ids'],['D1','D2'])
