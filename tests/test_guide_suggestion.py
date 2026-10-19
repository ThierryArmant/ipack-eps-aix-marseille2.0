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


class GuideAsTests(unittest.TestCase):
    def labels(self, q, public):
        return [e['libelle'] for _, e in suggested_entries(q, public)]

    def test_as_l_emporte_sur_l_activite(self):
        self.assertEqual(self.labels('je fais foot dasn las j ele declare ou', 'Lycée voie générale'),
                         ['Groupes AS : créer le groupe et ses élèves'])
        self.assertEqual(self.labels("j'enseigne le foot en AS, je le déclare où ?", 'Collège'),
                         ['Groupes AS : créer le groupe et ses élèves'])

    def test_verbe_avoir_n_est_pas_l_as(self):
        self.assertNotIn('Groupes AS : créer le groupe et ses élèves',
                         self.labels('tu as raison, comment déclarer le hand en terminale ?', 'Lycée voie générale'))


class GuideExamensRequestTests(unittest.TestCase):
    def test_perdu_dans_examens_lycee_ouvre_le_guide(self):
        from guide_request import requests_guide
        for public in ('Lycée Général & Techno', 'Lycée Pro / CAP'):
            self.assertTrue(requests_guide('je suis perdu', 'examens', public))
        self.assertFalse(requests_guide('je suis perdu', 'examens', 'Collège'))
        self.assertFalse(requests_guide('je suis perdu', 'textes', 'Lycée Général & Techno'))

    def test_app_affiche_le_guide_examens_sous_la_reponse(self):
        src = (ROOT / 'app.py').read_text(encoding='utf-8')
        self.assertIn('"mode_guide": "examens" if mode == "examens" else None', src)
        self.assertIn('mode=m.get("mode_guide")', src)
        self.assertIn("'AIDE EXAMENS'", src)


class LienSourceTests(unittest.TestCase):
    def fonction(self):
        import ast
        from response_controls import reference_url
        src = (ROOT / 'app.py').read_text(encoding='utf-8')
        node = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == '_url_source')
        ns = {'re': re, 'reference_url': reference_url}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'app.py', 'exec'), ns)
        return ns['_url_source']

    def test_url_du_catalogue_puis_du_passage(self):
        f = self.fonction()
        self.assertTrue(f('/app/data/textes/fiches/sorties_second_degre_guide_2025.txt', '', '').startswith('https://eduscol'))
        self.assertEqual(f('', 'Source : https://exemple.fr/texte.pdf.', ''), 'https://exemple.fr/texte.pdf')
        self.assertEqual(f('', 'sans lien', ''), '')
