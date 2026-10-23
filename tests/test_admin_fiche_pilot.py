import copy
import json
from pathlib import Path
import tempfile
import unittest
from admin_fiche_pilot import ROOT, available_pilots, load_checker, review

class AdminFichePilotTests(unittest.TestCase):
    def pilot(self):
        return json.loads((ROOT/'docs/fiches_pilotes/santorin_saisie_bloquee.json').read_text())
    def trace(self):
        return {'version':'test','model_document_ids':['D1'],'documents':[
            {'id':'D1','path':self.pilot()['sources'][0]['path']}],
            'proposal':{'claims':[{'text':"Vérifier la présence de la note AFL1 avant la saisie AFL2/AFL3. Vérifier la répartition choisie par l’élève. Demander au chef d'établissement d'intervenir."}]}}
    def test_review_reports_path_and_preserves_original_trace(self):
        trace=self.trace();saved=copy.deepcopy(trace)
        result=review(trace,self.pilot(),['gt','lot_verrouille'])
        self.assertEqual(trace,saved)
        self.assertEqual([f['element'] for f in result['findings']],['[Correction] > [Liste des lots]'])
        self.assertFalse(result['automatic_repair'])
        self.assertEqual(result['target'],'proposition_initiale')
    def test_only_actually_transmitted_sources_are_available(self):
        trace=self.trace();trace['model_document_ids']=[]
        self.assertEqual(available_pilots(trace),[])
        with self.assertRaises(ValueError):review(trace,self.pilot(),['gt'])
    def test_requires_explicit_known_branches(self):
        for branches in ([],['inconnu']):
            with self.assertRaises(ValueError):review(self.trace(),self.pilot(),branches)
    def test_source_change_prevents_coverage(self):
        pilot=self.pilot();pilot['sources'][0]['sha256']='0'*64
        result=review(self.trace(),pilot,['gt'])
        self.assertEqual(result['status'],'prototype_a_revoir')
        self.assertNotIn('findings',result)
    def test_checker_updates_without_mutating_previous_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir();path=root/'scripts/fiche_pilot.py'
            path.write_text('value="before"')
            before=load_checker(root)
            path.write_text('value="after"')
            after=load_checker(root)
            self.assertEqual(before.value,'before');self.assertEqual(after.value,'after')
    def test_admin_ui_integration_is_guarded(self):
        app=(ROOT/'app.py').read_text()
        self.assertIn('m.get("diagnostic_ia") and st.session_state.get("is_admin", False)',app)
        self.assertIn('_render_fiche_pilot(st, m["diagnostic_ia"]',app)

    def test_render_on_existing_trace_adds_report_only(self):
        from contextlib import nullcontext
        from admin_fiche_pilot import render
        class UI:
            def expander(self,*args,**kwargs):return nullcontext()
            def caption(self,*args,**kwargs):pass
            def selectbox(self,label,options,**kwargs):return options[0]
            def multiselect(self,*args,**kwargs):return ['gt','lot_verrouille']
            def button(self,*args,**kwargs):return True
            def warning(self,*args,**kwargs):pass
            def dataframe(self,*args,**kwargs):pass
            def info(self,*args,**kwargs):pass
        trace=self.trace();proposal=copy.deepcopy(trace['proposal'])
        render(UI(),trace,'test')
        self.assertEqual(trace['proposal'],proposal)
        self.assertEqual(trace['fiche_pilot_review']['findings'][0]['step_id'],'chemin_chef')

if __name__=='__main__':unittest.main()
