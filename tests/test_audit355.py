"""Régressions du retest en ligne : routage réel, sans appel OpenAI."""
import unittest

import knowledge_catalog as kc
import test_documentation as documentation


class Audit355Tests(unittest.TestCase):
    def test_general_questions_are_not_blocked_by_a_medical_or_diploma_prompt(self):
        questions = [
            "Nous sommes un CFA et nos apprentis n'apparaissent pas dans iPackEPS, comment faire pour le CCF ?",
            "Un élève est inapte à toutes les épreuves : comment le saisir dans Santorin ?",
            "En bac pro, un élève a une entorse et ne peut pas courir pendant six semaines. Peut-on adapter son épreuve au lieu de le dispenser ?",
            "Au bac GT, si un élève est dispensé de l'épreuve d'EPS, est-ce qu'on lui met 0 ?",
            "Mon élève est inapte à une épreuve : c'est moi qui choisis entre l'épreuve différée et la note sur deux activités ?",
            "Pour un élève de terminale générale dont l’inaptitude partielle est enregistrée dans iPackEPS, dois-je saisir ses notes de CCF EPS dans Santorin ?",
            "J'ai saisi une note mais je veux la transformer en dispense, est-ce possible ?",
            "Un élève est dispensé sur deux activités et noté sur la troisième, que saisir ?",
            "Je n'ai pas de note en AFLP1, puis-je saisir les autres ?",
            "Mon collègue a saisi mes protocoles à ma place dans Cyclades et du coup je ne vois pas mes lots pour noter. Comment régler ça ?",
            "Je me suis trompé sur une note dans Santorin alors que j'ai déjà saisi les deux autres activités. Je peux cliquer sur réinitialiser ?",
            "Est-ce qu'on a le droit de faire passer un CCF un mercredi après-midi, en dehors de l'emploi du temps de la classe ?",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertEqual(kc.clarification(question, 'Lycée Pro / CAP'), '')

    def test_individual_code_still_requires_the_medical_facts(self):
        self.assertTrue(kc.clarification('CAP inaptitude temporaire : je mets zéro ou DI ?', 'Lycée Pro / CAP'))

    def answer(self, question, public='Lycée Général & Techno', mode='examens'):
        return kc.documented_response(question, public, mode)[0]

    def test_apte_and_shn_authority_have_separate_answers(self):
        apte = self.answer("Notre élève inapte apparaît APTE dans Cyclades à l'inscription. Erreur du secrétariat ?")
        self.assertIn("ce n'est pas une erreur", apte)
        self.assertNotIn('haut niveau', apte)
        shn = self.answer('Qui coche la mention sportif de haut niveau dans Cyclades ?')
        self.assertIn('seul le gestionnaire EPS de la DIEC', shn)
        self.assertNotIn('APTE', shn)

    def test_session_2027_answer_is_not_transposed_to_2026(self):
        self.assertEqual(self.answer('2026 : notre inapte apparaît APTE dans Cyclades, erreur ?'), '')

    def test_option_is_not_eclipsed_by_an_explicitly_excluded_eppcs(self):
        answer = self.answer("Bac général 2026 : enseignement optionnel EPS, pas de l'EPS obligatoire ni de la spécialité EPPCS. Trois CCF dans Cyclades et Santorin ou moyennes dans le livret scolaire ?")
        self.assertIn('LSL', answer)
        self.assertIn('Ne créez pas trois CCF', answer)
        self.assertEqual(self.answer('EPPCS : option pratique, quelles notes dans Santorin ?'), '')

    def test_mixed_cycle3_answer_keeps_the_activity_exclusion(self):
        answer = self.answer('Sortie orientation 24 CM2 et 28 élèves de sixième dans un parc : encadrement ?', '1er degré', 'textes')
        self.assertIn('quatre adultes', answer)
        self.assertIn('exclut les activités physiques', answer)
        self.assertIn('directeur', answer)
        self.assertIn("chef d'établissement", answer)

    def test_explicit_bac_pro_overrides_the_selected_gt_level(self):
        answer = self.answer("En bac pro, une seule activité évaluée dans l'année, possible ?")
        self.assertIn('qualité et la quantité', answer)
        self.assertIn('différée', answer)
        self.assertEqual(self.answer('CAP : une seule activité évaluée dans l’année ?'), '')

    def test_pap_does_not_automatically_grant_an_adapted_eps_exam(self):
        answer = self.answer('PAP dyspraxie : droit à une épreuve EPS adaptée au bac ?')
        self.assertIn('ne donne pas, à lui seul', answer)
        self.assertIn('indications médicales', answer)

    def test_referee_status_does_not_guarantee_twenty(self):
        answer = self.answer('Arbitre de haut niveau en handball, droit au 20/20 au bac ?')
        self.assertIn("n'est pas acquise", answer)
        self.assertIn('validation par le recteur', answer)

    def test_as_substitution_has_the_deadline_and_service_condition(self):
        answer = self.answer("Remplacer mes 3 heures d'AS par des heures de cours, quand demander ?", 'Collège (DNB)', 'ipack')
        self.assertIn('15 février', answer)
        self.assertIn("intérêt du service", answer)

    def test_password_question_and_installation_receive_a_documented_answer(self):
        self.assertTrue(self.answer("Quel est le mot de passe administrateur d'iPackEPS ?", mode='ipack'))
        self.assertIn('rien à installer', self.answer('Installer iPackEPS sur Mac ?', mode='ipack'))

    def test_scope_with_spaces_is_respected(self):
        self.assertTrue(kc.incompatible('[PORTEE: gt, pro, cap]', {'dnb'}))
        self.assertFalse(kc.incompatible('[PORTEE: gt, pro, cap]', {'pro'}))

    def test_rentree_priority_keeps_the_real_year_change_procedure(self):
        runner = documentation.DocumentationTests()
        runner.setUp()
        text, _, _, error = runner.route("Que faut-il refaire au passage d'année dans iPackEPS ?", 'Collège (DNB)', 'ipack')
        self.assertIn('Organisation des classes', text)
        self.assertIn('dates de début et de fin', text)
        self.assertEqual(error, '')
