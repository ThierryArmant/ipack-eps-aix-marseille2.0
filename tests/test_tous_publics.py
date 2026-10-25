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
