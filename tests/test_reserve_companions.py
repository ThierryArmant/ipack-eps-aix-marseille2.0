import unittest
import json
from types import SimpleNamespace
from unittest.mock import patch
from document_selector import reserve_companions, select_documents
from documentary_review import source_packets, mark_excerpt, source_limits_for_rejections, validate_claims, review_exam_answer

LIMIT = ('La consultation de l’enquête piscine ne démontre pas la possibilité de saisir '
         'rétrospectivement les données pour une année précédente. Cette possibilité n’a pas été relevée.')

class ReserveTests(unittest.TestCase):
    def setUp(self):
        self.selected = {'id':'D1', 'title':'Enquête piscine', 'text':'Ouvrir le dossier et remplir l’enquête piscine.'}
        self.reserve = {'id':'D2','title':'Piscine et attestations', 'text': LIMIT + '\nImprimer les diplômes.', 'path':'data/ipack/test.txt'}

    def test_preserves_only_literal_reserve_on_previous_period(self):
        result = reserve_companions([self.selected, self.reserve], [self.selected], 'Comment saisir l’enquête piscine pour l’année précédente ?')
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['text'],LIMIT)
        self.assertNotIn('Imprimer',result[0]['text'])
        self.assertEqual(self.reserve['text'], LIMIT + '\nImprimer les diplômes.')

    def test_no_reserve_on_printing_or_excluded_document(self):
        self.assertEqual(reserve_companions([self.reserve],[self.selected],'Imprimer les attestations piscine'),[])
        self.assertEqual(reserve_companions([self.reserve],[self.selected],'Enquête piscine année précédente', ['D2']),[])

    def test_preserves_passage_ids_and_scope(self):
        packet={**self.reserve,'passages':[{'id':'D2P7','text':LIMIT,'scope':{'level':'logiciel'}}, {'id':'D2P8','text':'Imprimer les diplômes.'}]}
        result=reserve_companions([packet],[self.selected],'Enquête piscine année précédente')[0]
        self.assertEqual(result['passages'],packet['passages'][:1])

    def test_missing_citation_can_only_recover_unique_explicit_source_limit(self):
        packets=source_packets(mark_excerpt(LIMIT,title='Enquête piscine'))
        rejection={'errors':['preuves absentes ou trop nombreuses'], 'claim':{
            'section':'limite','text':'Les passages ne précisent pas la saisie de l’enquête piscine pour une année précédente.', 'evidence':[]}}
        recovered=source_limits_for_rejections([rejection],packets,'Saisir l’enquête piscine pour une année précédente')
        self.assertEqual(len(recovered),1)
        accepted,errors=validate_claims({'claims':recovered},packets)
        self.assertFalse(errors)
        self.assertEqual(accepted[0]['text'],LIMIT)
        rejection['claim']['section']='decision'
        self.assertEqual(source_limits_for_rejections([rejection],packets,'Enquête piscine année précédente'),[])
        self.assertEqual(source_limits_for_rejections([rejection],[], 'Enquête piscine année précédente'),[])

    def test_does_not_recover_ambiguous_or_unrelated_reserve(self):
        packets=source_packets(mark_excerpt(LIMIT,title='Enquête piscine')+'\n'+mark_excerpt(LIMIT,title='Autre relevé'))
        rejection={'errors':['preuves absentes ou trop nombreuses'], 'claim':{'section':'limite','text':'Les passages ne précisent pas la saisie de l’enquête piscine pour une année précédente.', 'evidence':[]}}
        self.assertEqual(source_limits_for_rejections([rejection],packets,'Enquête piscine année précédente'),[])
        self.assertEqual(source_limits_for_rejections([rejection],packets,'Installer un équipement sportif'),[])

    def test_selection_keeps_reserve_when_model_chooses_only_procedure(self):
        class Selector:
            def complete(self, prompt):
                return SimpleNamespace(text=json.dumps({'status':'selected','ids':['D1'],'objet':'enquête',
                    'compatibilites':[{'id':'D1','operation':'directe','conditions':'etablies'}]}))
        docs=source_packets(mark_excerpt(self.selected['text'],title='Enquête piscine',path='procedure.txt')+'\n'+
                            mark_excerpt(self.reserve['text'],title='Piscine et attestations',path='reserve.txt'))
        audit={}
        with patch('document_selector.catalogue_candidates',return_value=[]):
            selected=select_documents(Selector(),docs,question='Saisir l’enquête piscine pour l’année précédente',
                public='Collège',mode='ipack',academy='Non précisée',audit=audit)
        self.assertEqual(audit['selected_ids'],['D1'])
        self.assertEqual(audit['reserve_ids'],['D2'])
        self.assertEqual([p['id'] for p in selected],['D1','D2'])
        self.assertNotIn('Imprimer les diplômes',selected[1]['text'])

    def test_pipeline_preserves_sourced_caveat_without_second_generation(self):
        class Writer:
            calls=0
            def complete(self,prompt):
                self.calls+=1
                if self.calls>1:
                    raise AssertionError('Une seule rédaction attendue')
                return SimpleNamespace(text=json.dumps({'claims':[{'section':'limite',
                    'text':'Les passages ne précisent pas la saisie de l’enquête piscine pour une année précédente.',
                    'evidence':[]}]}))
        docs=mark_excerpt(LIMIT,title='Enquête piscine',path='reserve.txt')
        writer=Writer();audit={}
        answer=review_exam_answer(writer,question='Saisir l’enquête piscine pour une année précédente',
            public='Collège',mode='ipack',documents=docs,audit=audit)
        self.assertTrue(audit['documentary_limit_extraction'])
        self.assertFalse(audit['repair_performed'])
        self.assertEqual(writer.calls,1)
        self.assertIn('rétrospectivement',answer)
