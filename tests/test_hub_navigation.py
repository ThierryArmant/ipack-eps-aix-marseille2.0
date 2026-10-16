import ast
import unittest
from pathlib import Path
from hub_session import select_module, new_question, ready_for_question
from academie import request_academy, NON_PRECISEE
from tutorial_links import supporting_tutorials
from knowledge_catalog import priority_context, catalog, reference_notice

class HubNavigationTests(unittest.TestCase):
    def test_next_question_keeps_context_without_reusing_a_question(self):
        state=dict(active_module='examens',niveau_actif_form='Collège (DNB)', academie_utilisateur='Créteil', contexte_valide=True,
                   messages_hub=['ancienne réponse'],current_prompt='ancienne question', reset_steps=True)
        new_question(state)
        self.assertTrue(ready_for_question(state))
        self.assertEqual(state['active_module'],'examens')
        self.assertEqual(state['academie_utilisateur'],'Créteil')
        self.assertEqual(state['messages_hub'],[])
        self.assertNotIn('current_prompt',state)
    def test_only_exams_requires_an_academy(self):
        state=dict(niveau_actif_form='Collège (DNB)',contexte_valide=True)
        for mode,ready in [('ipack',True),('textes',True),('examens',False)]:
            select_module(state,mode)
            self.assertEqual(ready_for_question(state),ready)
        state['academie_utilisateur']='Créteil'
        self.assertTrue(ready_for_question(state))
    def test_ipack_does_not_inherit_previous_academy(self):
        self.assertEqual(request_academy('Supprimer une plage dans mon agenda','ipack','Aix-Marseille'),(NON_PRECISEE,''))
        academy,notice=request_academy('Je suis à Créteil, comment supprimer une plage ?','ipack','Aix-Marseille')
        self.assertEqual(academy,'Créteil')
        self.assertEqual(notice,'')
        self.assertEqual(request_academy('Question sur le CCF','examens','Créteil')[0],'Créteil')
    def test_real_app_no_longer_resets_steps_after_an_answer(self):
        tree=ast.parse(Path('app.py').read_text())
        assigns=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(ast.unparse(t)=='st.session_state.reset_steps' for t in n.targets)]
        self.assertTrue(assigns)
        self.assertTrue(all(ast.literal_eval(a.value) is False for a in assigns))
    def test_tutorial_comes_from_used_source_without_name_in_answer(self):
        path='data/ipack/fiches/ipack_068_article_20_dossiers_dossiereps_edt_saisie_et_gestion_des_emplois_du_temps_edt.txt'
        audit={'documents':[{'id':'D1','path':path}], 'accepted_claims':[{'section':'etape','text':'Clic droit sur la plage puis Supprimer.', 'evidence':[{'document_id':'D1'}]}]}
        self.assertEqual(supporting_tutorials(audit,catalog()),['https://youtu.be/8pHcZ4gw6go'])
        audit['accepted_claims']=[]
        self.assertEqual(supporting_tutorials(audit,catalog()),[])
    def test_unrelated_video_is_not_added_from_retrieval_only(self):
        audit={'documents':[{'id':'D1','path':'guide','text':'- Vidéo : https://example.org/tutorial.mp4'}], 'accepted_claims':[]}
        self.assertEqual(supporting_tutorials(audit,{}),[])
        audit['accepted_claims']=[{'section':'condition','text':'Aucune obligation nationale.', 'evidence':[{'document_id':'D1'}]}]
        self.assertEqual(supporting_tutorials(audit,{}),[])
    def test_existing_timetable_procedure_is_selected(self):
        text=priority_context('Retirer une plage de mon emploi du temps : comment faire ?', 'Collège (DNB)','ipack')
        self.assertIn('[ARTICLE 20]',text)
        self.assertIn('[Supprimer]',text)
        self.assertNotIn('DIEC',text)

class TimetableRecoveryIntentTests(unittest.TestCase):
    def test_delete_procedure_does_not_select_recovery(self):
        selected=reference_notice({'dnb'},'Comment effacer un créneau dans mon EDT ?','Collège (DNB)')
        paths=[p for p,_ in selected]
        self.assertTrue(any('ipack_068_' in p for p in paths))
        self.assertFalse(any('suppression_prudence' in p for p in paths))
    def test_recovery_guard_still_matches_deleted_data(self):
        selected=reference_notice({'dnb'},"J'ai supprimé un groupe par erreur, comment le récupérer ?",'Collège (DNB)')
        self.assertTrue(any('suppression_prudence' in p for p,_ in selected))

class ExclusiveSelectionTests(unittest.TestCase):
    def test_general_exclusive_fiche_does_not_erase_specific_fiche_in_either_tab(self):
        from test_documentation import DocumentationTests
        route=DocumentationTests();route.setUp()
        specific='data/ipack/fiches/ipack_068_article_20_dossiers_dossiereps_edt_saisie_et_gestion_des_emplois_du_temps_edt.txt'
        general='data/commun/audit60/ipack_suppression_prudence.txt'
        route.env['reference_notice']=lambda *args:[
            (specific,{'title':'Procédure précise','priorite':300}),
            (general,{'title':'Garde-fou général','priorite':0,'exclusif_motifs':['.*']})]
        for mode in ('ipack','examens'):
            text,_,_,error=route.route('Manipuler une plage de mon agenda','Collège (DNB)',mode)
            self.assertEqual(error,'')
            self.assertIn('[ARTICLE 20]',text)
