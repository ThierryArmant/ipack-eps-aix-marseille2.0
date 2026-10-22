import unittest
import json
from types import SimpleNamespace
from documentary_review import review_exam_answer, mark_excerpt
from claim_guards import unrelated_retrospective_limit

TEXT="La possibilité de saisir rétrospectivement une enquête pour une année précédente n'est pas confirmée. Cette vérification doit être faite séparément."
class PeriodRelevanceTests(unittest.TestCase):
    def test_simple_current_request_omits_only_knowledge_limit(self):
        self.assertTrue(unrelated_retrospective_limit({'section':'limite','text':TEXT},'Où remplir mon enquête ?'))
    def test_historical_requests_keep_limit(self):
        for q in ['Saisir pour n-1','Saisir pour l’année précédente','Consulter les archives','Modifier 2025','Récupérer les données de l’an dernier','Combien de temps conserver les données ?']:
            self.assertFalse(unrelated_retrospective_limit({'section':'limite','text':TEXT},q),q)
    def test_never_removes_a_business_condition_or_other_section(self):
        for text in ['La saisie est interdite pour une année précédente.', TEXT+' La validation du responsable est obligatoire.',"La possibilité de saisir pour une année précédente n'est pas confirmée et le dépôt doit être validé."]:
            self.assertFalse(unrelated_retrospective_limit({'section':'limite','text':text},'Où saisir ?'))
        self.assertFalse(unrelated_retrospective_limit({'section':'condition','text':TEXT},'Où saisir ?'))
    def test_current_procedure_is_unchanged(self):
        self.assertFalse(unrelated_retrospective_limit({'section':'etape','text':'Ouvrir le module puis imprimer la sélection.'},'Comment imprimer ?'))

    def test_pipeline_keeps_procedure_without_repair_for_unrelated_limit(self):
        procedure='Pour imprimer les documents, ouvrir le module puis sélectionner les documents et cliquer sur Imprimer.'
        docs=mark_excerpt(procedure+'\n\n'+TEXT,title='Impression des documents',path='guide.txt')
        class Writer:
            calls=0
            def complete(self,prompt):
                self.calls+=1
                if self.calls>1:
                    raise AssertionError('Aucune seconde rédaction attendue')
                return SimpleNamespace(text=json.dumps({'claims':[
                    {'section':'etape','text':procedure,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]},
                    {'section':'limite','text':TEXT,'evidence':[{'document_id':'D1','passage_ids':['D1P2']}]}]}))
        writer=Writer();audit={}
        answer=review_exam_answer(writer,question='Comment imprimer les documents ?',public='Collège',mode='ipack',documents=docs,audit=audit)
        self.assertEqual(writer.calls,1)
        self.assertFalse(audit['repair_performed'])
        self.assertEqual(len(audit['excluded_unrelated_period_limits']),1)
        self.assertIn('cliquer sur Imprimer',answer)
        self.assertNotIn('rétrospectivement',answer)
