import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from documentary_review import source_packets,mark_excerpt,review_exam_answer,source_limits_for_rejections

class Model:
    model='fake';temperature=0
    def __init__(self,result):self.result=result;self.calls=0
    def complete(self,prompt):
        self.calls+=1
        if self.calls>1:raise AssertionError('No second generation expected')
        return SimpleNamespace(text=json.dumps(self.result))

class LimitRepairTests(unittest.TestCase):
    def fixture(self):
        docs=mark_excerpt("### Notice des accès et des procédures\nLa connexion au module passe par le portail professionnel habituel.\n\nTransmission au comité technique : aucune procédure de transmission à cette instance n’a été trouvée dans la documentation consultée.",title='Notice des accès et des procédures',path='guide.txt')
        packets=source_packets(docs)
        packet=packets[0]
        wrong=next(p for p in packet['passages'] if 'connexion' in p['text'])
        c={'section':'limite','text':'Les passages fournis ne précisent pas la procédure de transmission au comité technique ; cette étape reste non confirmée.',
           'evidence':[{'document_id':'D1','passage_ids':[wrong['id']]}]}
        return docs,packets,c
    def test_unique_literal_limit_repairs_wrong_passage_without_new_generation(self):
        docs,packets,c=self.fixture()
        # Réserve simple : pas d'ajout de règle ou d'autorité de décision.
        llm=Model({'claims':[c]});audit={}
        answer=review_exam_answer(llm,question='Comment transmettre au comité technique ?',public='Lycée Général & Techno',mode='ipack',documents=docs,audit=audit)
        self.assertEqual(llm.calls,1);self.assertTrue(audit['documentary_limit_extraction'])
        self.assertIn('aucune procédure',answer);self.assertFalse(audit['repair_performed'])
    def test_cannot_repair_a_prescription_or_choose_between_two_limits(self):
        _,packets,c=self.fixture()
        c['text']='Il faut transmettre le protocole au comité technique.'
        rejection={'claim':c,'errors':['passage cité sans rapport avec l’affirmation : choisir le passage qui l’énonce']}
        self.assertEqual(source_limits_for_rejections([rejection],packets,'transmettre au comité technique'),[])
        c['text']='Les passages fournis ne précisent pas la procédure de transmission au comité technique.'
        packets[0]['passages'].append(dict(packets[0]['passages'][-1],id='another'))
        self.assertEqual(source_limits_for_rejections([rejection],packets,'transmettre au comité technique'),[])
    def test_college_screen_is_preserved_outside_mixed_submission_fiche(self):
        mixed=Path('data/ipack/situations_2026_10_17/bouton_envoi_dossier_grise.txt').read_text()
        college=Path('data/ipack/complement_cyclades_cas_pratiques.txt').read_text()
        self.assertNotIn('Étapes — Dossier EPS',mixed)
        self.assertIn('État de validation de votre Dossier EPS',college)
        self.assertIn('Protocoles d’Évaluation'.replace('’',"'"),mixed)
