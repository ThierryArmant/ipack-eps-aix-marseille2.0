import unittest
from admin_retest_113 import parse_csv
from hub_session import allowed_modules, select_public, select_module, ready_for_question
from knowledge_catalog import effective_context


class TousPublicsTests(unittest.TestCase):
    def parse(self,mode,level='',default=None):
        return parse_csv(('mode;public;question\n'+mode+';'+level+';Question générale\n').encode(),None,default)

    def test_textes_blank_or_explicit_all_public(self):
        for value in ['', 'Tous publics', 'tout public']:
            self.assertEqual(self.parse('texte',value)[0]['public'],'Tous publics')
        self.assertEqual(self.parse('texte','', 'Collège')[0]['public'],'Collège (DNB)')
        self.assertEqual(self.parse('texte','Lycée voie générale')[0]['public'],'Lycée Général & Techno')

    def test_other_modes_still_require_school_level(self):
        for mode in ['ipack','examen']:
            for value in ['', 'Tous publics']:
                with self.assertRaises(ValueError):self.parse(mode,value)

    def test_navigation_is_textes_only_and_ready(self):
        state={'niveau_actif_form':'Tous publics','active_module':'examens'}
        select_public(state,'Tous publics')
        self.assertEqual(allowed_modules('Tous publics'),('textes',))
        self.assertTrue(ready_for_question(state))
        select_module(state,'ipack')
        self.assertEqual(state['active_module'],'textes')

    def test_general_question_has_no_implicit_level_but_explicit_diploma_is_recognized(self):
        self.assertEqual(effective_context('Quelles obligations de service ?', 'Tous publics','textes'),('Tous publics','textes'))
        self.assertEqual(effective_context('Que prévoit le bac professionnel ?', 'Tous publics','textes'),('Lycée Pro / CAP','textes'))


if __name__=='__main__':unittest.main()


class TousPublicsCaseTextes(unittest.TestCase):
    def test_public_tous_publics_absent_du_choix_de_public(self):
        from pathlib import Path
        app = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('["1er degré", "Collège", "Lycée Général & Techno", "Lycée Pro / CAP"],', app)
        self.assertIn('key="textes_tous_publics"', app)
        self.assertIn('if mode == "textes" and st.session_state.get("textes_tous_publics"):', app)

    def test_rejeu_remet_la_case_a_zero_a_chaque_ligne(self):
        from test_admin_replay_usage import Surface
        from admin_retest_113_live import render
        # La première ligne est déjà répondue dans Surface : le rendu lance la suivante.
        rows=[{'n':'0','question':'P ?','mode':'textes','public':'Collège (DNB)','academie':''},
              {'n':'1','question':'Q ?','mode':'textes','public':'Tous publics','academie':''},
              {'n':'2','question':'R ?','mode':'textes','public':'Collège (DNB)','academie':''}]
        ui=Surface(rows); render(ui)
        self.assertTrue(ui.session_state['textes_tous_publics'])
        ui.session_state['messages_hub']=[{'role':'assistant','type':'text','content':'ok'}]; render(ui)
        self.assertFalse(ui.session_state['textes_tous_publics'])
