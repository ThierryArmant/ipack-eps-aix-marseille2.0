"""Régressions du retest en ligne : routage réel, sans appel OpenAI."""
import unittest
from pathlib import Path

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
        return kc.delivered_text(question, public, mode)

    def test_apte_and_shn_authority_have_separate_answers(self):
        apte = self.answer("Notre élève inapte apparaît APTE dans Cyclades à l'inscription. Erreur du secrétariat ?")
        self.assertIn("ce n'est pas une erreur", apte)
        self.assertNotIn('haut niveau', apte)
        shn = self.answer('Qui coche la mention sportif de haut niveau dans Cyclades ?')
        self.assertIn('seul le gestionnaire EPS de la DIEC', shn)
        # la mention SHN n'est plus une réponse en dur : la fiche d'inscription (qui parle aussi de l'APTE) est transmise à l'IA
        self.assertIn('Aix-Marseille : inscriptions terminale GT, session 2027 (EPS)', kc.priority_titles('Qui coche la mention sportif de haut niveau dans Cyclades ?', 'Lycée Général & Techno', 'examens'))

    def test_session_2027_answer_is_not_transposed_to_2026(self):
        # garde-fou conservé en dur : il ne doit pas répondre pour 2026
        self.assertEqual(kc.documented_response('2026 : notre inapte apparaît APTE dans Cyclades, erreur ?', 'Lycée Général & Techno', 'examens')[0], '')

    def test_option_is_not_eclipsed_by_an_explicitly_excluded_eppcs(self):
        answer = self.answer("Bac général 2026 : enseignement optionnel EPS, pas de l'EPS obligatoire ni de la spécialité EPPCS. Trois CCF dans Cyclades et Santorin ou moyennes dans le livret scolaire ?")
        self.assertIn('LSL', answer)
        self.assertIn('Ne créez pas trois CCF', answer)
        self.assertNotIn('Bac GT : option EPS et LSL', kc.priority_titles('EPPCS : option pratique, quelles notes dans Santorin ?', 'Lycée Général & Techno', 'examens'))

    def test_mixed_cycle3_answer_keeps_the_activity_exclusion(self):
        answer = self.answer('Sortie orientation 24 CM2 et 28 élèves de sixième dans un parc : encadrement ?', '1er degré', 'textes')
        self.assertIn('tranche de quinze', answer)
        self.assertIn('exclut les activités physiques', answer)
        self.assertIn('directeur', answer)
        self.assertIn("chef d'établissement", answer)

    def test_explicit_bac_pro_overrides_the_selected_gt_level(self):
        answer = self.answer("En bac pro, une seule activité évaluée dans l'année, possible ?")
        self.assertIn('qualité et la quantité', answer)
        self.assertIn('différée', answer)
        self.assertNotIn('Bac professionnel : inaptitude et une seule évaluation', kc.priority_titles('CAP : une seule activité évaluée dans l’année ?', 'Lycée Général & Techno', 'examens'))

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


class Audit355RoutageTests(unittest.TestCase):
    """Deuxième passe du retest : demandes de diplôme inutiles, collège mal reconnu, CAP à 3 épreuves."""

    def test_tool_questions_in_pro_cap_are_not_asked_for_the_diploma(self):
        for question in (
            "Comment exporter les notes d'EPS vers Pronote ?",
            "Comment saisir les absences en EPS dans iPackEPS ?",
            "J'ai vidé le cache de mon navigateur sur la tablette. Ai-je perdu les notes de mes élèves ?",
            "Les notes de la spécialité EPPCS se saisissent où ?",
            "Avant quelle date doivent être remontées les notes de CCF EPS ?",
            "Santorin affiche une alerte d'incohérences de données sur des candidats alors qu'il y a zéro candidat non affecté",
        ):
            with self.subTest(question=question):
                self.assertEqual(kc.clarification(question, 'Lycée Pro / CAP'), '')

    def test_medical_and_code_questions_in_pro_cap_still_ask_for_the_diploma(self):
        self.assertIn('CAP ou baccalauréat professionnel',
                      kc.clarification('Il est dispensé et il manque une note : je mets zéro ou DI ?', 'Lycée Pro / CAP'))

    def test_college_classes_switch_the_public_to_college(self):
        for question in ("Un élève de 3e ne s'est pas présenté à l'évaluation de remplacement, sans justificatif. Quelle note ?",
                         "Peut-on mettre zéro à un élève de quatrième absent à une évaluation ?"):
            with self.subTest(question=question):
                self.assertEqual(kc.effective_context(question, 'Lycée Pro / CAP', 'examens')[0], 'Collège (DNB)')
        self.assertEqual(kc.effective_context("La 3e épreuve du CCF de bac pro", 'Lycée Pro / CAP', 'examens')[0],
                         'Lycée Pro / CAP')

    def test_cap_three_events_follows_the_academic_bulletin(self):
        code = open('app.py', encoding='utf-8').read()
        self.assertNotIn('UN ENSEMBLE CERTIFICATIF À 2 ÉPREUVES, PAS 3', code)
        self.assertIn('retient 2 épreuves en début d\'année', code)
        self.assertIn('re.search(r"\\bcap\\b", p_low)', code)

    def test_partial_context_is_answered_instead_of_absence_sentence(self):
        code = open('app.py', encoding='utf-8').read()
        self.assertIn('Path("config/consignes_fiabilite.txt").read_text', code)
        consignes = Path('config/consignes_fiabilite.txt').read_text()
        self.assertIn('Si les sources répondent partiellement, donne cette réponse', consignes)
        self.assertIn('Un cas voisin ne démontre pas la règle du cas posé', consignes)
        self.assertNotIn("Si la réponse n'y est pas, dis simplement que tu ne disposes pas", code)


class Audit355Retest11Tests(unittest.TestCase):
    """Relance des 11 questions : fiche collège servie au lycée, phrase d'absence malgré une fiche prioritaire."""

    def test_college_scale_notice_is_not_served_to_lycee(self):
        question = 'Comment paramétrer un barème de notation personnalisé pour une APSA ?'
        bareme = 'data/commun/audit60/ipack_bareme_college.txt'
        for public, targets in (('Lycée Général & Techno', {'gt'}), ('Lycée Pro / CAP', {'pro', 'cap'})):
            with self.subTest(public=public):
                self.assertNotIn(bareme, [p for p, _ in kc.reference_notice(targets, question, public)])
        self.assertIn(bareme, [p for p, _ in kc.reference_notice({'dnb'}, question, 'Collège (DNB)')])

    def test_absence_sentence_with_priority_notice_is_asked_again(self):
        code = open('app.py', encoding='utf-8').read()
        self.assertIn('"[FICHE PRIORITAIRE" in extraits_doc', code)
        self.assertIn('consigne_ia + RELANCE_FICHE_PRIORITAIRE', code)
        self.assertIn('reference_notice(_cibles, search_prompt or prompt, niveau_actuel_form)', __import__('pathlib').Path('document_retrieval.py').read_text())


class Audit355Retest13Tests(unittest.TestCase):
    """Relance des 13 questions après la PR 21."""

    def test_question_about_ipackeps_itself_stays_in_ipack(self):
        q = "Quelle version minimale d'iPackEPS faut-il pour l'interfaçage avec Cyclades et Santorin ?"
        self.assertEqual(kc.effective_context(q, 'Lycée Général & Techno', 'ipack')[1], 'ipack')
        self.assertEqual(kc.effective_context('Bac pro : comment associer les candidats dans Cyclades ?',
                                              'Lycée Général & Techno', 'ipack')[1], 'examens')

    def test_absence_sentence_after_an_answer_is_removed(self):
        import ast
        tree = ast.parse(open('app.py', encoding='utf-8').read())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'retirer_phrase_absence_apres_reponse')
        env = {'re': __import__('re')}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'app.py', 'exec'), env)
        retirer = env['retirer_phrase_absence_apres_reponse']
        absence = ("Je ne dispose pas de la procédure exacte dans ma base pour cette demande. Pour iPackEPS, écrivez "
                   "à l'assistance. Pour Santorin, adressez-vous à la DEC de votre académie.")
        self.assertEqual(retirer(absence), absence)
        texte = "<p>Les absences se saisissent dans Pronote.</p>\n<p>" + absence + "</p>\n<p>Fin.</p>"
        resultat = retirer(texte)
        self.assertIn('Pronote', resultat)
        self.assertIn('Fin.', resultat)
        self.assertNotIn('ne dispose pas', resultat)
