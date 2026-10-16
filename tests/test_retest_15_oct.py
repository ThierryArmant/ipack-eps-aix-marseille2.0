"""Régressions des mécanismes observés en ligne ; aucun appel réseau/modèle."""
import ast
import unittest
from pathlib import Path
from documentary_review import (case_value_errors, mark_excerpt, render_exam_fallback,
                                review_exam_answer, usage_summary, TracedLLM, situation_mismatch,
                                conditional_extraction_errors)
from knowledge_catalog import priority_context, effective_context
from test_documentary_review import FakeLLM


class RetestOctober15Tests(unittest.TestCase):
    def test_examples_do_not_become_candidate_grades(self):
        claims = [{'text': 'Conserver DI + DI + 13 avec une appréciation.'}]
        self.assertTrue(case_value_errors(claims, 'Deux dispenses et une note : comment saisir ?'))
        self.assertFalse(case_value_errors(claims, 'Deux dispenses et une note de 13 : comment saisir ?'))
        self.assertFalse(case_value_errors([{'text':'Par exemple, DI + DI + 13.'}], 'Comment saisir ?'))

    def test_equivalent_single_grade_questions_select_specific_conditional_source(self):
        for q in ('Deux inaptitudes totales et une note au bac GT : faut-il noter ?',
                  'DI+DI+note : que saisir ?',
                  'Un candidat dispensé sur les deux activités, une note obtenue : que faire ?'):
            text = priority_context(q, 'Lycée Général & Techno', 'examens')
            self.assertIn('DI+DI+Note', text)
            self.assertNotIn('note de 14', text)
            self.assertIn('neutralisation', text)
            self.assertNotIn('Réponse à donner dans cet ordre', text)

    def test_shn_single_cycle_selects_shn_and_not_bac_pro_fallback(self):
        q = "Comment noter le SHN qui n'a participé qu'à un cycle ?"
        text = priority_context(q, 'Lycée Général & Techno', 'examens')
        self.assertIn('note réellement obtenue lors du cycle', text)
        self.assertIn('sans conclure automatiquement que deux notes suffisent', text)
        self.assertNotIn('DI + DI + 20', text)
        result = render_exam_fallback({}, question=q, documents=mark_excerpt('Les BAC PRO déclarent trois APSA dans Cyclades.', title='Passage documentaire', priority=300))
        self.assertNotIn('<blockquote>', result)
        self.assertNotIn('BAC PRO', result)

    def test_fallback_hides_editorial_lines_but_keeps_conditional_alternative(self):
        body = ("### Notation après inaptitude\n"
                "Réponse à donner dans cet ordre : demander le caractère médical.\n"
                "Si deux épreuves sont impossibles, une seule note peut être retenue. Ne pas transformer ces possibilités en décision automatique.\n"
                "Si les éléments sont trop réduits, la dispense neutralise le coefficient.\n")
        result = render_exam_fallback({}, question='Inaptitude : notation ?', documents=mark_excerpt(body))
        self.assertNotIn('Réponse à donner', result)
        self.assertNotIn('Ne pas transformer', result)
        self.assertNotIn('###', result)
        self.assertIn('une seule note peut être retenue', result)
        self.assertIn('dispense neutralise', result)

    def test_editorial_claim_does_not_force_repair_of_valid_answer(self):
        doc = mark_excerpt('Chaque candidat reçoit une note individuelle.')
        proof = [{'document_id':'D1','passage_ids':['D1P1']}]
        llm = FakeLLM([{'claims':[
            {'section':'decision','text':'Chaque candidat reçoit une note individuelle.','evidence':proof},
            {'section':'limite','text':'Une réponse qui ne donne pas cette règle est incomplète.','evidence':proof},
        ]}])
        audit = {}
        result = review_exam_answer(llm, question='Comment noter ?', public='GT', documents=doc, audit=audit)
        self.assertIn('note individuelle', result)
        self.assertNotIn('réponse qui', result)
        self.assertEqual(len(llm.prompts),1)
        self.assertTrue(audit['excluded_editorial_claims'])

    def test_pending_fiche_exposes_limit_instead_of_invented_deadline(self):
        text = priority_context('Mon référentiel reste en attente depuis plusieurs semaines', 'Lycée Général & Techno', 'ipack')
        self.assertIn('ne fixe pas de délai garanti', text)
        self.assertIn("Si l'envoi", text)
        self.assertNotIn('motif exact du refus', text)

    def test_bcp_diploma_overrides_gt_menu(self):
        public, mode = effective_context('En BCP, les cases AFLP sont inactives dans Santorin', 'Lycée Général & Techno', 'examens')
        self.assertEqual(public, 'Lycée Pro / CAP')
        self.assertEqual(mode, 'examens')

    def test_shn_cycle_does_not_imply_terminal_exam(self):
        q='SHN : un seul cycle évalué, comment noter ?'
        self.assertTrue(situation_mismatch(q, "Le 20/20 ne peut pas être l'unique note pour l'examen ponctuel."))
        self.assertFalse(situation_mismatch(q, "En CCF, le 20/20 ne peut pas être l'unique note."))

    def test_shn_cycle_does_not_establish_medical_inaptitude(self):
        c={'section':'limite','text':"Sans autre note, la situation relève des règles d'inaptitude.",'evidence':[]}
        self.assertTrue(conditional_extraction_errors([c], 'SHN avec un seul cycle : comment noter ?'))
        self.assertFalse(conditional_extraction_errors([c], 'SHN avec inaptitude médicale : comment noter ?'))

    def test_shn_source_distinguishes_cycle_grade_from_specialty_twenty(self):
        text=Path('data/examens/audit_lot4_2026_10_13/shn_note_unique.txt').read_text()
        self.assertIn('note réellement obtenue lors du cycle',text)
        self.assertIn('sans conclure automatiquement que deux notes suffisent',text)

    def test_ipack_and_exam_calls_use_the_same_outer_usage_trace(self):
        tree = ast.parse(Path('app.py').read_text())
        expression = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id=='llm_reponse' for t in n.targets))
        self.assertEqual(ast.unparse(expression.test), "mode in ('examens', 'ipack', 'textes')")


if __name__ == '__main__': unittest.main()
