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

    def test_general_inaptitude_paraphrases_do_not_block(self):
        for question in (
            'Un élève inapte sur une épreuve du CCF, quelle note finale ?',
            'Élève inapte à une épreuve de CCF : on fait la moyenne des deux autres notes ?',
            'Comment calculer la note finale en cas d’inaptitude à une épreuve ?',
        ):
            with self.subTest(question=question):
                self.assertEqual(kc.clarification(question, 'Lycée Général & Techno'), '')
                self.assertTrue(kc.clarification(question, 'Lycée Pro / CAP'))

    def test_general_wording_does_not_bypass_code_clarification(self):
        for question in (
            'Il est inapte : quelle note finale, DI ou zéro ?',
            'Il est inapte : on fait la moyenne ou je saisis AB ?',
        ):
            self.assertTrue(kc.clarification(question, 'Lycée Général & Techno'))

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

    def test_risk_cases_exclude_adjacent_procedures(self):
        cases = [
            ("Comment paramétrer un barème personnalisé pour une APSA ?", 'Collège (DNB)', 'ne pas envoyer', 'valider la commission'),
            ("Comment faire le passage d’année sans perdre l’historique des élèves ?", 'Collège (DNB)', 'ne constituent pas une procédure', '[Configuration des classes] puis'),
            ("Comment utiliser iPackEPS sur tablette sans connexion internet ?", 'Collège (DNB)', 'Cette limite concerne iPackEPS uniquement', 'impossible de noter les élèves directement sur tablette'),
            ("J’ai supprimé une évaluation : peut-on la récupérer ?", 'Collège (DNB)', "y compris dans iPackEPS", 'il vous faut recréer'),
            ("Quels élèves passent EPS en ponctuel plutôt qu’en CCF ?", 'Lycée Général & Techno', 'CHACUNE DES DEUX ÉPREUVES', 'Configuration des classes'),
            ("Un élève est inapte sur une des trois épreuves du CCF : comment est calculée sa note ?", 'Lycée Général & Techno', "Présenter d'abord", 'Configuration des classes'),
        ]
        hostile = [documentation.SimpleNamespace(text='[PORTEE: gt] Il vous faut recréer. Configuration des classes. Neutralisation automatique.', metadata={'source':'ancienne.txt'})]
        for question, public, expected, excluded in cases:
            with self.subTest(question=question):
                text, _, _, _ = self.route(question, public, 'ipack' if public.startswith('Collège') else 'examens', hostile)
                self.assertIn(expected, text)
                self.assertEqual(text.count('[FICHE PRIORITAIRE'), 1)
                self.assertNotIn(excluded, text)
                self.assertNotIn('Neutralisation automatique.', text)

    def test_gt_targeted_fiches_do_not_leak_into_cap(self):
        text, _, _, _ = self.route('CAP inapte à une épreuve : comment calculer la note ?', 'Lycée Pro / CAP', 'examens')
        self.assertNotIn('CHACUNE DES DEUX ÉPREUVES', text)
        self.assertNotIn('Bac GT CCF : inaptitude, adaptation', text)

    def test_programmation_gets_actionable_sequence_without_lycee_protocol(self):
        text, _, _, _ = self.route("Comment créer une programmation d’APSA sur l’année pour l’établissement ?", 'Collège (DNB)', 'ipack')
        for step in ('[APSA]', '[Périodes]', '[Groupes]', '[Élèves]', '[EDT]'):
            self.assertIn(step, text)
        self.assertEqual(text.count('[FICHE PRIORITAIRE'), 1)
        self.assertNotIn('### Bac GT', text)

    def test_pv_does_not_invent_mandatory_signatures(self):
        text, _, _, _ = self.route('Que doit contenir le PV de CCF EPS et qui le signe ?', 'Lycée Général & Techno', 'examens')
        self.assertIn("modèle académique vérifié", text)
        self.assertIn('Ce passage ne fixe pas de durée', text)
        self.assertNotIn('doit être signé par les examinateurs', text)

    def test_academic_protocol_preserves_session_and_roles(self):
        text, _, _, _ = self.route("Qu’est-ce que le protocole d’évaluation académique et où trouver les référentiels d’Aix-Marseille ?", 'Lycée Général & Techno', 'examens')
        self.assertIn('session 2026', text)
        self.assertIn('transmission des protocoles assurée par l’inspection'.replace('’', "'"), text)
        self.assertIn('ne sont pas des échéances', text)

    def test_academic_certificates_do_not_replace_college_framework(self):
        text, _, _, _ = self.route('Collège certificat inaptitude : où le déclarer ?', 'Collège (DNB)', 'ipack')
        self.assertNotIn('annexe 7 pour le candidat individuel', text)


if __name__ == '__main__':
    unittest.main()
