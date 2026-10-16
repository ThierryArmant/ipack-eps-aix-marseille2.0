"""Sélection documentaire des nouveaux domaines ; aucune génération ni appel réseau."""
import json
import unittest
from pathlib import Path
import knowledge_catalog as kc

class MetierSourcesTests(unittest.TestCase):
    def test_imp_reference_is_selected_in_textes_for_short_and_long_requests(self):
        for q in ('Quelles indemnités pour la coordination EPS ?', 'IMP et quotité de temps partiel'):
            body=kc.priority_context(q,'Lycée Général & Techno','textes')
            self.assertIn('MENH1506032C',body)
            self.assertIn('JORFTEXT000030533649',body)
            self.assertEqual(kc.documented_response(q,'Lycée Général & Techno','textes')[0],'')

    def test_changed_professional_topics_have_their_source_in_selected_context(self):
        cases=[('Quels recours après mon rendez-vous de carrière EPS ?', 'article 9-7'),
               ('Quels viviers pour la classe exceptionnelle ?', 'Depuis la campagne 2024'),
               ('Déclarer un accident de trajet enseignant', 'F33252'),
               ('Cumul activités : coaching rémunéré', 'F1648'),
               ('PAI et adaptation de la pratique sportive', 'MENE2104832C'),
               ('Quelle formation pour le Capeps externe ?', 'transition 2026 et 2027'),
               ('Combien de HSA peuvent être imposées ?', 'LEGIARTI000038375945')]
        for q,reference in cases:
            with self.subTest(q=q):
                self.assertIn(reference,kc.priority_context(q,'Collège (DNB)','textes'))

    def test_sources_are_not_selected_for_a_technical_timetable_request(self):
        body=kc.priority_context("Déplacer un créneau d'emploi du temps",'Collège (DNB)','ipack')
        self.assertNotIn('recours préalable',body)
        self.assertNotIn('mission annuelle donne lieu',body)

    def test_regular_travel_keeps_conditions_and_levels(self):
        body=kc.priority_context('Un collégien peut-il rentrer seul du gymnase ?', 'Collège (DNB)','textes')
        self.assertIn('début ou en fin de temps scolaire',body)
        self.assertIn('règlement intérieur',body)
        self.assertIn('Au lycée',body)

    def test_official_guidance_is_not_relabelled_as_statute(self):
        n=json.loads(Path('config/nature_sources.json').read_text())['fichiers']
        p='data/textes/fiches/ia_usages_pedagogiques.txt'
        self.assertEqual(n[p]['nature'],['a_verifier'])
        self.assertIn('CNIL',Path(p).read_text())

    def test_every_lot_file_has_references_and_registry(self):
        paths=json.loads(Path('docs/lot_metier_eps_fichiers.json').read_text())
        entries=kc.catalog()
        for p in paths:
            with self.subTest(p=p):
                self.assertIn('https://',Path(p).read_text())
                self.assertIn(p,entries)
