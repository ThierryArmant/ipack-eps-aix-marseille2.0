"""Cas révélés par le test public de 60 questions : routage documentaire réel."""
import unittest
from pathlib import Path
import knowledge_catalog as kc
import test_documentation as documentation


class Audit60Tests(unittest.TestCase):
    setUp = documentation.DocumentationTests.setUp
    route = documentation.DocumentationTests.route
    def test_pronote_export_selects_direction_and_perimeter(self):
        text, _, _, _ = self.route("L'export vers Pronote ne fonctionne pas, que vérifier ?", 'Collège (DNB)', 'ipack')
        self.assertIn('source, la destination', text)
        self.assertIn('ne calcule pas les moyennes', text)
        self.assertEqual(text.count('[FICHE PRIORITAIRE'), 1)
        self.assertNotIn('Configuration des classes', text)

    def test_results_history_does_not_receive_class_path_as_grade_history(self):
        text, _, _, _ = self.route("Comment suivre les résultats d'un élève sur plusieurs années de la 6e à la 3e ?", 'Collège (DNB)', 'ipack')
        self.assertIn('pas un historique de notes', text)
        self.assertEqual(text.count('[FICHE PRIORITAIRE'), 1)

    def test_college_certificate_does_not_impose_santorin(self):
        text, _, _, _ = self.route("Certificat d'inaptitude de 3 mois : comment l'enregistrer pour la moyenne ?", 'Collège (DNB)', 'ipack')
        self.assertIn('ne calcule aucune moyenne', text)
        self.assertIn('[Inaptitudes]', text)
        self.assertNotIn('CCF EPS : l’enseignant', text)

    def test_written_copies_do_not_get_only_ccf_mission(self):
        text, _, _, _ = self.route('Comment me connecter à Santorin et où trouver mes copies ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('Correction de copies écrites', text)
        self.assertIn('service organisateur / DEC', text)

    def test_validation_describes_two_circuits(self):
        text, _, _, _ = self.route('Comment valider définitivement mes notes dans Santorin ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('coordinateur ou référent', text)
        self.assertIn('c’est l’enseignant qui verrouille à nouveau', text)

    def test_gt_menu_limit_not_academic_limit(self):
        text, _, _, _ = self.route('Comment faire valider ma liste APSA et menu établissement ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('pas le menu d’établissement', text)

    def test_general_medical_information_is_not_blocked_but_code_is(self):
        self.assertEqual(kc.clarification('Un élève inapte à une épreuve : comment est calculée sa note ?', 'Lycée Général & Techno'), '')
        self.assertTrue(kc.clarification('Il est inapte : je saisis DI ou zéro ?', 'Lycée Général & Techno'))

    def test_ipack_perimeter_is_not_injected_into_epccs_exam(self):
        text, _, _, _ = self.route('Comment fonctionne EPPCS au bac : écrit, oral, pratique ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('MENE2622650N', text)
        self.assertNotIn('source, la destination', text)

    def test_connection_uses_documents_instead_of_absolute_direct_answer(self):
        code = Path('app.py').read_text()
        self.assertIn('est_connexion = False', code)


if __name__ == '__main__':
    unittest.main()
