"""Routage des sources officielles et blocages révélés par l'audit 90."""
import ast
import unittest
from pathlib import Path
import knowledge_catalog as kc
import test_documentation as doc

class Audit90SourcesTests(unittest.TestCase):
    setUp = doc.DocumentationTests.setUp
    route = doc.DocumentationTests.route

    def test_2027_registration_is_separate_by_diploma(self):
        for public, expected, excluded in (
            ('Lycée Général & Techno', 'aix_inscriptions_2027_gt.txt', 'aix_inscriptions_2027_voie_pro.txt'),
            ('Lycée Pro / CAP', 'aix_inscriptions_2027_voie_pro.txt', 'aix_inscriptions_2027_gt.txt')):
            text, sources, _, _ = self.route('Session 2027 : inscrire un candidat inapte dans Cyclades', public, 'examens')
            targets = ['gt'] if 'Techno' in public else ['pro', 'cap']
            paths = [p for p, _ in kc.reference_notice(targets, 'Session 2027 : inscrire un candidat inapte dans Cyclades')]
            self.assertIn('data/commun/audit60/' + expected, paths)
            self.assertNotIn('data/commun/audit60/' + excluded, paths)
            self.assertIn('APTE' if 'Techno' in public else 'apte', text)

    def test_lsu_does_not_select_gt_option(self):
        paths = [p for p, _ in kc.reference_notice(['gt'], 'Où saisir la note dans le LSU ?')]
        self.assertNotIn('data/commun/gt_option_eps_lsl.txt', paths)
        paths = [p for p, _ in kc.reference_notice(['gt'], 'Option EPS : LSL ?')]
        self.assertIn('data/commun/gt_option_eps_lsl.txt', paths)

    def test_accommodation_appeal_does_not_get_grade_appeal(self):
        paths = [p for p, _ in kc.reference_notice(['gt'], "Recours après refus d'aménagement d'examen ?")]
        self.assertIn('data/commun/audit60/aix_amenagements_2027.txt', paths)
        self.assertNotIn('data/commun/audit60/contestation_note.txt', paths)

    def test_general_procedures_do_not_choose_individual_status(self):
        for question in ('Qui valide une dispense ?', 'Comment enregistrer un certificat médical ?',
                         'Comment inscrire un candidat inapte dans Cyclades ?',
                         'Formation continue : dispense EPS ?'):
            for public in ('Lycée Général & Techno', 'Lycée Pro / CAP'):
                self.assertEqual(kc.clarification(question, public), '')
        self.assertTrue(kc.clarification('Il est inapte : je saisis DI ou zéro ?', 'Lycée Général & Techno'))

    def test_functional_protection_has_perimeter_keyword_and_source(self):
        tree = ast.parse(Path('app.py').read_text())
        self.assertTrue(any(isinstance(n, ast.Constant) and n.value == 'protection fonctionnelle' for n in ast.walk(tree)))
        text, _, _, _ = self.route('Comment demander la protection fonctionnelle ?', 'Lycée Général & Techno', 'textes')
        self.assertIn('agent poursuivi', text)

    def test_second_degree_guide_excludes_primary(self):
        path = 'data/textes/fiches/sorties_second_degre_guide_2025.txt'
        self.assertNotIn(path, [p for p,_ in kc.reference_notice(['primaire'], 'Sortie scolaire')])
        self.assertIn(path, [p for p,_ in kc.reference_notice(['dnb'], 'Sortie scolaire')])
