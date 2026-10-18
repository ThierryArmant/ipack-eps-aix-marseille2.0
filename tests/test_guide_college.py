import json
import unittest
from pathlib import Path
from unittest.mock import patch

import guided_navigation as guide


class UI:
    def __init__(self, goal, state=None, click='', rub=None):
        self.goal = goal; self.session_state = {} if state is None else state; self.click = click
        self.rub = rub; self.radios = []; self.infos = []
        self.written = []; self.videos = []; self.inputs = 0
    def selectbox(self, label, options, **k):
        self.options = options; return self.rub
    def radio(self, label, options, **k):
        self.radios.append(options); return self.goal
    def button(self, label, **k):
        self.callbacks = getattr(self, 'callbacks', {}) if 'callbacks' in self.__dict__ else {}
        self.callbacks[label] = k.get('on_click')
        return label == self.click
    def write(self, text): self.written.append(text)
    @property
    def shown(self): return ' '.join(self.written + list(getattr(self, 'callbacks', {})))
    def info(self, text): self.infos.append(text)
    def video(self, url): self.videos.append(url)
    def text_input(self, *a, **k): self.inputs += 1
    def text_area(self, *a, **k): self.inputs += 1
    def expander(self, *a, **k): return self
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def rerun(self): pass
    def columns(self, *a, **k): return (self, self)
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
        ui = UI('Classes', state, rub='Dossier EPS')
        guide.render_guide(ui, 't', 'Collège')
        self.assertIn('[Actualiser]', ui.shown); self.assertEqual(ui.inputs, 0)
        self.assertEqual(ui.videos, [])
        etape = next(l for l in ui.callbacks if l.startswith('▶') and '[Actualiser]' in l)
        ui.callbacks[etape]()
        ui = UI('Classes', state, rub='Dossier EPS')
        guide.render_guide(ui, 't', 'Collège')
        self.assertTrue(ui.videos and ui.videos[0].startswith('https://'))
        self.assertNotIn('📺 Voir comment faire', ui.shown)
        guide.render_guide(UI('Classes', state, 'C’est fait · Suivant →', rub='Dossier EPS'), 't', 'Collège')
        ui = UI('Classes', state, rub='Dossier EPS')
        guide.render_guide(ui, 't', 'Collège (DNB)')
        self.assertIn('Étape 2/4', ui.written[0])
        ui = UI(None, {}, rub='Je ne sais pas par où commencer')
        guide.render_guide(ui, 'u', 'Collège')
        self.assertIn('[Établissement]', ui.shown); self.assertEqual(ui.radios, [])

    def test_menu_suit_les_intitules_de_l_ecran(self):
        ui = UI(None)
        guide.render_guide(ui, 'm', 'Collège')
        self.assertEqual(ui.options[1:4], ['Établissement', 'Ma Fiche Professeur', 'Dossier EPS'])
        self.assertEqual(ui.written, [])
        ui = UI(None, rub='Dossier EPS')
        guide.render_guide(ui, 'm', 'Collège')
        sous = ui.radios[0]
        ordre = ['Projets', 'Équipe EPS', 'Classes', 'APSA', 'Groupes AS', 'Élèves', 'Équipements', 'Emplois du temps']
        pos = [next(i for i, x in enumerate(sous) if x.startswith(o)) for o in ordre]
        self.assertEqual(pos, sorted(pos))
        self.assertEqual(ui.written, [])
        menu = guide.college_menu(self.routes)
        atteints = {e['parcours'] for b in menu for e in b['entrees']}
        self.assertEqual(atteints, set(self.routes))

    def test_sous_menu_unique_ouvre_directement_le_pas_a_pas(self):
        ui = UI(None, rub='Dossier Natation')
        guide.render_guide(ui, 'n', 'Collège')
        self.assertIn('[Dossier Natation]', ui.shown); self.assertEqual(ui.radios, [])

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

    def test_prerequis_remplacent_le_rappel_general(self):
        ui = UI(None)
        guide.render_guide(ui, 'r', 'Collège')
        self.assertEqual(ui.infos, [])
        ui = UI('Projets', rub='Dossier EPS')
        guide.render_guide(ui, 'r', 'Collège')
        self.assertEqual(ui.infos, ['Avant [Projets], vous devez avoir complété : [Établissement] → [Ma Fiche Professeur].'])
        ui = UI(None, rub='Établissement')
        guide.render_guide(ui, 'r', 'Collège')
        self.assertEqual(ui.infos, [])
        ui = UI('Envoyer le dossier pour validation', rub='Dossier EPS')
        guide.render_guide(ui, 'r', 'Collège')
        self.assertTrue(ui.infos[0].startswith('Avant d’envoyer le dossier'))
        for b in guide.college_menu(self.routes):
            for e in b['entrees']:
                self.assertIn('prerequis', e)
        ui = UI('Configurer les périodes')
        guide.render_guide(ui, 'r', 'Lycée voie générale')
        self.assertIn('dans l’ordre', ui.infos[0])
        with patch.object(guide, 'SOURCE', Path('absent.txt')):
            self.assertEqual(guide.order_rule(), '')

    def test_video_etablissement_dans_le_guide_et_les_fiches(self):
        url = 'https://youtu.be/-Ka0fNtMLBk'
        etab = self.routes['Établissement : vérifier la fiche'][0]
        self.assertEqual(guide.video_url(etab['video']), url)
        self.assertEqual(guide.video_url(self.routes['Me repérer depuis le début (ordre de rentrée)'][0]['video']), url)
        cat = json.loads(Path('config/catalogue_documents.json').read_text(encoding='utf-8'))
        for k in ('data/ipack/situations_2026_10_17/ordre_premiere_connexion_fiche_professeur.txt',
                  'data/ipack/visite_college_2026_10_18/classes_actualiser_configurer_organiser_importer.txt'):
            self.assertIn(url, [t['url'] for t in cat[k]['tutoriels']])

    def test_j_ai_trouve_referme_le_guide(self):
        state = {'f_rub': 'Dossier Natation', 'f_position_0': 1, 'autre': 1}
        ui = UI(None, state, rub='Dossier Natation')
        guide.render_guide(ui, 'f', 'Collège', on_done=lambda: state.__setitem__('ferme', True))
        pos = list(guide.college_routes()).index('Imprimer les attestations du savoir-nager (ASNS)')
        state['f_position_' + str(pos)] = 1
        ui = UI(None, state, rub='Dossier Natation')
        guide.render_guide(ui, 'f', 'Collège', on_done=lambda: state.__setitem__('ferme', True))
        ui.callbacks['✓ J’ai trouvé']()
        self.assertTrue(state['ferme']); self.assertEqual(state['autre'], 1)
        self.assertFalse([k for k in state if k.startswith('f_')])

    def test_lycee_garde_ses_parcours(self):
        ui = UI('Configurer les périodes')
        guide.render_guide(ui, 'l', 'Lycée voie générale')
        self.assertIn('Périodes', ui.shown)

    def test_fiches_de_la_visite_sans_donnees_personnelles(self):
        for f in Path('data/ipack/visite_college_2026_10_18').glob('*.txt'):
            t = f.read_text(encoding='utf-8')
            for mot in ('ARMANT', 'Armant', 'Giono', 'GIONO', 'tarmant', 'ORANGE'):
                self.assertNotIn(mot, t, f)
            self.assertIn('Nature de la source', t)


if __name__ == '__main__':
    unittest.main()
