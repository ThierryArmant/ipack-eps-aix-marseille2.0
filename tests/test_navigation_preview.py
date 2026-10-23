import copy
import json
from pathlib import Path
import tempfile
import unittest
from admin_fiche_pilot import ROOT, navigation_preview
from admin_fiche_pilot_loader import load_panel

class NavigationPreviewTests(unittest.TestCase):
    def pilot(self,name='santorin_saisie_bloquee'):
        return json.loads((ROOT/'docs/fiches_pilotes'/f'{name}.json').read_text())
    def fixture(self,name,branch_id,step_id):
        pilot=self.pilot(name)
        step=next(s for b in pilot['branches'] if b['id']==branch_id for s in b['steps'] if s['id']==step_id)
        claim={'section':'etape','text':'Demander une intervention.','evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}
        data={'documents':[{'id':'D1','passages':[{'id':'D1P1','text':step['text']}]}]}
        trace={'version':'test','model_document_ids':['D1'],'documents':[{'id':'D1','path':pilot['sources'][0]['path']}],
               'proposal':{'claims':[copy.deepcopy(claim)]},'final_claims':[claim],
               'calls':[{'stage':'generation','prompt':'DONNEES :\n'+json.dumps(data)}]}
        return pilot,step,trace
    def test_missing_path_replaced_by_whole_cited_passage_only_in_preview(self):
        pilot,step,trace=self.fixture('santorin_saisie_bloquee','lot_verrouille','chemin_chef');before=copy.deepcopy(trace)
        preview=navigation_preview(trace,pilot,['lot_verrouille'])
        self.assertEqual(trace,before)
        self.assertEqual(preview['claims'][0]['text'],step['text'])
        self.assertEqual(preview['claims'][0]['evidence'],trace['final_claims'][0]['evidence'])
        self.assertFalse(preview['automatic_repair']);self.assertFalse(preview['original_response_changed'])
        self.assertIn('Si un cadenas',preview['replacements'][0]['after'])
        self.assertIn("chef d'établissement",preview['replacements'][0]['after'])
    def test_navigation_example_uses_its_own_source(self):
        pilot,step,trace=self.fixture('ipack_multi_etablissements','basculer','retour_tableau')
        self.assertEqual(navigation_preview(trace,pilot,['basculer'])['claims'][0]['text'],step['text'])
    def test_academic_or_regulatory_passages_are_not_reinserted(self):
        pilot,step,trace=self.fixture('gt_absence_ccf','saisie_aix','fiche_individuelle')
        self.assertEqual(navigation_preview(trace,pilot,['saisie_aix'])['replacements'],[])
    def test_no_copy_if_path_present_or_branch_not_selected(self):
        pilot,step,trace=self.fixture('santorin_saisie_bloquee','lot_verrouille','chemin_chef')
        trace['final_claims'][0]['text']=step['text']
        self.assertEqual(navigation_preview(trace,pilot,['lot_verrouille'])['replacements'],[])
        self.assertEqual(navigation_preview(trace,pilot,['gt'])['replacements'],[])
    def test_missing_transmission_changed_quote_or_multiple_evidence_refused(self):
        pilot,step,original=self.fixture('santorin_saisie_bloquee','lot_verrouille','chemin_chef')
        for case in ('no_calls','changed','many'):
            trace=copy.deepcopy(original)
            if case=='no_calls':trace['calls']=[]
            if case=='changed':trace['calls'][0]['prompt']=trace['calls'][0]['prompt'].replace('Liste des lots','Autre menu')
            if case=='many':trace['final_claims'][0]['evidence'][0]['passage_ids'].append('D1P2')
            self.assertEqual(navigation_preview(trace,pilot,['lot_verrouille'])['replacements'],[])
    def test_unaccepted_proposal_not_repaired(self):
        pilot,step,trace=self.fixture('santorin_saisie_bloquee','lot_verrouille','chemin_chef')
        trace['final_claims']=[]
        self.assertEqual(navigation_preview(trace,pilot,['lot_verrouille'])['claims'],[])
    def test_panel_loader_ignores_stale_global_module(self):
        import sys,types
        from unittest.mock import patch
        stale=types.ModuleType('admin_fiche_pilot')
        with patch.dict(sys.modules,{'admin_fiche_pilot':stale}):
            self.assertTrue(callable(load_panel().navigation_preview))
            self.assertIs(sys.modules['admin_fiche_pilot'],stale)

if __name__=='__main__':unittest.main()
