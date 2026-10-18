import json
import unittest
from pathlib import Path
from unittest.mock import patch

import guided_navigation as guide


class UI:
    def __init__(self, goal, state=None, click=''):
        self.goal = goal; self.session_state = {} if state is None else state; self.click = click
        self.written = []; self.videos = []; self.inputs = 0
    def radio(self, *a, **k): return self.goal
    def button(self, label, **k): return label == self.click
    def write(self, text): self.written.append(text)
    def video(self, url): self.videos.append(url)
    def text_input(self, *a, **k): self.inputs += 1
    def text_area(self, *a, **k): self.inputs += 1
    def expander(self, *a, **k): return self
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def rerun(self): pass
    def __getattr__(self, name): return lambda *a, **k: None


class GuideCollegeTests(unittest.TestCase):
    def setUp(self):
        self.routes = guide.college_routes()
        self.raw = json.loads(Path('config/guide_ipack_college.json').read_text(encoding='utf-8'))['parcours']

    def test_toutes_les_etapes_sont_prouvees_par_leur_fiche(self):
        self.assertEqual(set(self.routes), set(self.raw))
        videos = {t['etape'] for t in json.loads(Path('config/tutoriels_parcours_college.json').read_text(encoding='utf-8'))['tutoriels']}
        for goal, steps in self.routes.items():
            for step in steps:
                self.assertIn(step['preuve'], Path(step['source']).read_text(encoding='utf-8'), (goal, step))
                self.assertTrue(step['video'] is None or step['video'] in videos, step)
                self.assertLessEqual(len(step['clic']), 95, step['clic'])

    def test_question_foot_6e4_activite_enseignee(self):
        steps = [s['clic'] for s in self.routes["Déclarer l'activité enseignée à une classe"]]
        self.assertIn('[APSA]', steps[0]); self.assertIn('[Créer une nouvelle Période]', steps[1])
        self.assertIn('[Gérer les S.A.]', steps[2]); self.assertIn('[Ajouter]', steps[3])
        self.assertFalse(any('Fiche Professeur' in s or 'spécialit' in s for s in steps))

    def test_classes_ordre_et_boutons_exacts(self):
        steps = [s['clic'] for s in self.routes['Voir mes classes et importer mes élèves']]
        self.assertIn('[Actualiser]', steps[0]); self.assertIn('[Importer]', steps[-1])
        self.assertIn('[Organisation des Classes]', steps[2])

    def test_ordre_de_rentree(self):
        steps = ' '.join(s['clic'] for s in self.routes['Me repérer depuis le début (ordre de rentrée)'])
        order = ['[Établissement]', '[Ma Fiche Professeur]', '[Projets]', '[Équipe EPS', '[Classes]', '[APSA]',
                 '[Périodes]', '[Groupes]', '[Élèves]', '[Équipements Sportifs]', '[Emplois du temps]']
        pos = [steps.index(x) for x in order]
        self.assertEqual(pos, sorted(pos))

    def test_groupe_as_avant_placement(self):
        steps = [s['clic'] for s in self.routes["Créer un groupe d'AS et y placer des élèves"]]
        self.assertIn('[Créer un groupe]', steps[0]); self.assertIn('[Ajouter -->]', steps[-1])
        self.assertIn('Classes', steps[3])

    def test_affichage_college_clics_video_sans_saisie(self):
        state = {}
        ui = UI('Voir mes classes et importer mes élèves', state)
        guide.render_guide(ui, 't', 'Collège')
        self.assertIn('[Actualiser]', ui.written[0]); self.assertEqual(ui.inputs, 0)
        self.assertTrue(ui.videos and ui.videos[0].startswith('https://'))
        guide.render_guide(UI('Voir mes classes et importer mes élèves', state, 'C’est fait · Suivant →'), 't', 'Collège')
        ui = UI('Voir mes classes et importer mes élèves', state)
        guide.render_guide(ui, 't', 'Collège (DNB)')
        self.assertIn('Étape 2/4', ui.written[0])
        ui = UI('Je ne sais pas encore', {})
        guide.render_guide(ui, 'u', 'Collège')
        self.assertIn('[Établissement]', ui.written[0])

    def test_etape_sans_preuve_retire_le_parcours(self):
        bad = json.loads(Path('config/guide_ipack_college.json').read_text(encoding='utf-8'))
        bad['parcours']['Modifier un équipement sportif'][0]['preuve'] = 'phrase absente de la fiche'
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d) / 'guide.json'
            tmp.write_text(json.dumps(bad, ensure_ascii=False), encoding='utf-8')
            with patch.object(guide, 'COLLEGE', tmp):
                routes = guide.college_routes()
        self.assertNotIn('Modifier un équipement sportif', routes)
        self.assertIn('Voir mes classes et importer mes élèves', routes)

    def test_lycee_garde_ses_parcours(self):
        ui = UI('Configurer les périodes')
        guide.render_guide(ui, 'l', 'Lycée voie générale')
        self.assertIn('Périodes', ui.written[0])

    def test_fiches_de_la_visite_sans_donnees_personnelles(self):
        for f in Path('data/ipack/visite_college_2026_10_18').glob('*.txt'):
            t = f.read_text(encoding='utf-8')
            for mot in ('ARMANT', 'Armant', 'Giono', 'GIONO', 'tarmant', 'ORANGE'):
                self.assertNotIn(mot, t, f)
            self.assertIn('Nature de la source', t)


if __name__ == '__main__':
    unittest.main()
