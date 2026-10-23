import copy
import json
from pathlib import Path
import unittest
from scripts.fiche_pilot import ROOT, validate, coverage

class FichePilotTests(unittest.TestCase):
    def load(self, name='santorin_saisie_bloquee'):
        return json.loads((ROOT/'docs/fiches_pilotes'/f'{name}.json').read_text())
    def test_three_pilots_keep_real_quotes(self):
        paths=list((ROOT/'docs/fiches_pilotes').glob('*.json'))
        self.assertEqual(len(paths),3)
        for path in paths:
            self.assertEqual(validate(json.loads(path.read_text())),[])
    def test_changed_source_detected(self):
        p=self.load();p['sources'][0]['sha256']='0'*64
        self.assertTrue(any('source modifiée' in e for e in validate(p)))
    def test_invented_quote_or_menu_detected(self):
        for field in ('text','navigation'):
            p=self.load();step=p['branches'][0]['steps'][0]
            step[field]='instruction inventée' if field=='text' else ['[Menu inexistant]']
            self.assertTrue(validate(p))
    def test_unknown_scope_or_repeated_step_detected(self):
        p=self.load();p['branches'][0]['scope']['diplomas']=['inconnu']
        self.assertTrue(validate(p))
        p=self.load();p['branches'][0]['steps'].append(copy.deepcopy(p['branches'][0]['steps'][0]))
        self.assertTrue(any('étape dupliquée' in e for e in validate(p)))
    def test_menu_omission_detected_without_repair(self):
        p=self.load();report=coverage(p,['lot_verrouille'],"Demander au chef d'établissement d'intervenir.")
        self.assertTrue(any(f['element']=='[Correction] > [Liste des lots]' for f in report['findings']))
        self.assertFalse(report['automatic_repair']);self.assertFalse(report['semantic_validation'])
    def test_complete_text_and_unselected_branches(self):
        p=self.load();branch=p['branches'][0]
        answer=' '.join(s['text'] for s in branch['steps'])
        self.assertEqual(coverage(p,['gt'],answer)['findings'],[])
        self.assertEqual(coverage(p,[],answer)['findings'],[])
    def test_unknown_branch_not_silently_selected(self):
        with self.assertRaises(ValueError): coverage(self.load(),['inconnu'],'réponse')
    def test_procedure_and_regulation_both_supported(self):
        nav=self.load('ipack_multi_etablissements');rule=self.load('gt_absence_ccf')
        self.assertTrue(coverage(nav,['basculer'],'Changer d’établissement')['findings'])
        self.assertTrue(coverage(rule,['absence_injustifiee'],'La note est zéro')['findings'])
        self.assertEqual(rule['branches'][2]['scope']['academies'],['Aix-Marseille'])

if __name__=='__main__':unittest.main()
