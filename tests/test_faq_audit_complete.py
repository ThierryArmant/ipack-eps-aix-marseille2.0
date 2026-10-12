"""Vérifier les conditions décisives et les limites des réponses relues."""
import ast
from pathlib import Path
import unittest
import knowledge_catalog as kc

GT = 'Lycée Général & Techno'


class AuditedFAQTests(unittest.TestCase):
    def test_reviewed_reply_bypasses_llm_arbiter_but_legacy_reply_does_not(self):
        tree = ast.parse(Path('app.py').read_text())
        guards = [node.test for node in ast.walk(tree) if isinstance(node, ast.If)
                  and 'openai_api_key' in ast.unparse(node.test)
                  and 'not besoin_ia' in ast.unparse(node.test)]
        self.assertEqual(len(guards), 1)
        condition = compile(ast.Expression(guards[0]), 'app.py', 'eval')
        state = dict(besoin_ia=False, texte_brut='réponse', openai_api_key=True,
                     est_question_trop_courte=False, est_mauvais_onglet=False,
                     demande_precision='', reponse_documentee='réponse relue')
        self.assertFalse(eval(condition, {}, state))
        state['reponse_documentee'] = ''
        self.assertTrue(eval(condition, {}, state))

    def answer(self, question, public=GT):
        return kc.delivered_text(question, public, 'examens')

    def test_medical_candidate_keeps_protocol_even_when_unfit_all_year(self):
        answer = self.answer('Inapte toute l’année, doit-il rester dans le groupe Cyclades ?')
        self.assertIn('reste dans son groupe', answer)
        self.assertIn('doit être associé', answer)
        self.assertNotIn('ne devez pas mettre', answer)

    def test_late_receipt_is_not_equivalent_to_late_issue(self):
        answer = self.answer('Certificat reçu en retard après le CCF : refus automatique ?')
        self.assertIn('ne permet pas de le refuser automatiquement', answer)
        self.assertIn('date d’établissement', answer)

    def test_transfer_does_not_add_two_events_to_two_acquired_events(self):
        answer = self.answer('Élève arrivé avec 2 CCF acquis : quel protocole ?')
        self.assertIn('ne conduisent pas à ajouter deux nouvelles APSA', answer)

    def test_distribution_restart_preserves_existing_grades(self):
        answer = self.answer('Erreur de distribution : supprimer et recommencer ?')
        self.assertIn('aucune note', answer)
        self.assertIn('Si des notes existent, ne pas supprimer', answer)

    def test_gt_only_afl2_afl3_rule_does_not_need_medical_details(self):
        answer = self.answer('Peut-on certifier uniquement AFL2 et AFL3 sans pratiquer ?')
        self.assertIn('ne peut pas reposer', answer)

    def test_three_events_and_technical_single_event_are_not_confused(self):
        answer = self.answer('Au bac, Cyclades accepte un protocole adapté à une seule APSA ?')
        self.assertIn('ne peux donc pas affirmer', answer)
        self.assertIn('DIEC et l’inspection', answer)

    def test_general_train_delay_does_not_trigger_school_blockage(self):
        answer = kc.delivered_text('Grève des transports le jour du CCF : élève bloqué.', GT, 'examens')
        titres = kc.priority_titles('Grève des transports le jour du CCF : élève bloqué.', GT, 'examens')
        self.assertIn('FAQ EPS — Évaluation différée', titres)
        self.assertFalse(any(t.startswith('Blocages des lycées') for t in titres))
        self.assertIn('pas automatiquement', answer)

    def test_negative_cases_do_not_get_unrelated_reviewed_faq(self):
        for question, public in [
            ('Date du CCF : comment la modifier dans un protocole ?', GT),
            ('Mon élève a 14, quelle appréciation de bulletin ?', GT),
            ('Le coordonnateur crée les groupes iPackEPS', GT),
            ('Santorin : les lots sont distribués correctement', GT),
            ('DNB : certificat reçu après une évaluation', 'Collège (DNB)'),
            ('CAP : noter uniquement AFLP2 et AFLP3 ?', 'Lycée Pro / CAP'),
        ]:
            with self.subTest(question=question):
                self.assertFalse(any(t.startswith('FAQ EPS') for t in kc.priority_titles(question, public, 'examens')))
