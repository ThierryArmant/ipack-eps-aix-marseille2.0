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

    def test_new_apsa_does_not_receive_teacher_specialty_procedure(self):
        text, _, _, _ = self.route("Comment créer une nouvelle APSA qui n'existe pas dans la liste ?", 'Collège (DNB)', 'ipack')
        self.assertIn('peut être enseignée', text)
        self.assertEqual(text.count('[FICHE PRIORITAIRE'), 1)

    def test_ccf_definition_does_not_receive_formative_mixed_passages(self):
        text, _, _, _ = self.route("Quelle est la différence entre le CCF et l'épreuve ponctuelle terminale en EPS ?", 'Lycée Général & Techno', 'examens')
        self.assertIn('ne se confond pas', text)
        self.assertEqual(text.count('[FICHE PRIORITAIRE'), 1)

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

    def test_video_missing_feature_is_not_a_noncompliance_verdict(self):
        text, _, _, _ = self.route("Est-ce que l'utilisation de la vidéo dans iPackEPS est conforme au RGPD ?", 'Collège (DNB)', 'ipack')
        self.assertIn('ne signifie pas', text)
        self.assertEqual(text.count('[FICHE PRIORITAIRE'), 1)

    def test_epccs_terminal_does_not_receive_compulsory_eps_reference(self):
        text, _, _, _ = self.route("Comment fonctionne EPPCS au bac : écrit, oral, pratique ?", 'Lycée Général & Techno', 'examens')
        self.assertIn('MENE2622650N', text)
        self.assertNotIn('MENE2531948N', text)
        code = Path('app.py').read_text()
        self.assertIn("if _exams and not re.search", code)

    def test_academic_harmonisation_is_not_mixed_with_national_presidency(self):
        text, _, _, _ = self.route("Qu'est-ce que la commission d'harmonisation pour l'EPS ?", 'Lycée Général & Techno', 'examens')
        self.assertIn('commission académique', text)
        self.assertNotIn('présidée par un membre de l’Inspection générale', text)


if __name__ == '__main__':
    unittest.main()
