import json
import re
import unittest
from pathlib import Path

from guided_navigation import DECLENCHEURS, college_menu, college_routes, guide_file, suggested_entries

ROOT = Path(__file__).resolve().parents[1]


class GuideSuggestionTests(unittest.TestCase):
    def labels(self, question, public, mode=None):
        return [e['libelle'] for _, e in suggested_entries(question, public, mode)]

    def test_activite_enseignee_college_mene_au_parcours_apsa(self):
        self.assertEqual(self.labels("J'enseigne le foot à mes 6eme4, comment renseigner ça ?", 'Collège'),
                         ["APSA · Périodes · Groupes : déclarer l'activité d'une classe"])

    def test_renseigner_ne_compte_pas_comme_enseigner(self):
        self.assertEqual(self.labels('Comment renseigner la fiche ?', 'Collège'), [])

    def test_lycee_propose_apsa_certificative_et_protocole(self):
        self.assertIn('APSA : déclarer une APSA certificative',
                      self.labels("J'enseigne le badminton à mes terminales", 'Lycée voie générale'))

    def test_question_sans_rapport_ne_propose_rien(self):
        self.assertEqual(self.labels('Combien de temps iPackEPS conserve-t-il les données ?', 'Lycée voie générale'), [])
        self.assertEqual(self.labels('Je ne peux plus saisir mes notes.', 'Collège'), [])

    def test_examens_et_public_inconnu_sans_proposition(self):
        self.assertEqual(self.labels('Comment exporter vers Cyclades ?', 'Lycée voie générale', 'examens'), [])
        self.assertEqual(self.labels("J'enseigne le foot", ''), [])

    def test_declencheurs_compilent_et_visent_des_parcours_existants(self):
        config = json.loads(DECLENCHEURS.read_text(encoding='utf-8'))
        re.compile(config['apsa'])
        noms = set()
        for public in ('Collège', 'Lycée voie générale', 'Lycée voie professionnelle'):
            path = guide_file(public)
            for block in college_menu(college_routes(path), path):
                noms.update(e['parcours'] for e in block['entrees'])
        for parcours, patterns in config['parcours'].items():
            self.assertIn(parcours, noms, parcours)
            for p in patterns:
                if p != '@apsa':
                    re.compile(p)


if __name__ == '__main__':
    unittest.main()


class GuideMessageTests(unittest.TestCase):
    def test_message_adapte_quand_le_parcours_est_affiche(self):
        from guide_request import MESSAGE_PARCOURS
        self.assertNotIn('choisissez simplement une rubrique', MESSAGE_PARCOURS)
        src = (ROOT / 'app.py').read_text(encoding='utf-8')
        self.assertIn('GUIDE_MESSAGE = GUIDE_MESSAGE_PARCOURS', src)


class GuideExplicationTests(unittest.TestCase):
    def test_explication_ne_cite_que_des_boutons_du_parcours(self):
        for name in ('ipack_college', 'ipack_lycee_gt', 'ipack_lycee_pro', 'examens_lycee'):
            g = json.loads((ROOT / f'config/guide_{name}.json').read_text(encoding='utf-8'))
            for block in g['menu']:
                for entry in block['entrees']:
                    texte = entry.get('explication', '')
                    if not texte:
                        continue
                    clics = ' '.join(s['clic'] for s in g['parcours'][entry['parcours']]) + ' ' + ' '.join(entry.get('prerequis') or [])
                    for bouton in re.findall(r'\[[^\]]+\]', texte):
                        self.assertIn(bouton, clics, (name, entry['parcours'], bouton))

    def test_chaque_guide_explique_chaque_parcours(self):
        for name in ('ipack_college', 'ipack_lycee_gt', 'ipack_lycee_pro', 'examens_lycee'):
            g = json.loads((ROOT / f'config/guide_{name}.json').read_text(encoding='utf-8'))
            for block in g['menu']:
                for entry in block['entrees']:
                    self.assertTrue(entry.get('explication'), (name, entry['parcours']))
