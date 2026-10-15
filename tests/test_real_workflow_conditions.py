"""Contrôles des états de dossier et des antécédents conditionnels, sans réseau."""
import ast
import unittest
from pathlib import Path
from documentary_review import (
    conditional_extraction_errors, mark_excerpt, review_exam_answer, situation_mismatch,
)
from test_documentary_review import FakeLLM


class WorkflowConditionsTests(unittest.TestCase):
    def test_pending_does_not_select_rejection_workflow(self):
        q = 'Mon référentiel reste en attente de validation depuis plusieurs semaines.'
        source = Path('data/ipack/fiches/ipack_199_article_101_dossiers_dossier_certificatif_referentiels_rejet_d_un_referentiel_par_la_commi.txt').read_text()
        self.assertTrue(situation_mismatch(q, source))
        self.assertFalse(situation_mismatch('Mon référentiel est refusé : comment le renvoyer ?', source))
        self.assertFalse(situation_mismatch('Mon référentiel est rejeté : comment le redéposer et repasser en attente ?', source))
        self.assertFalse(situation_mismatch(q, 'Consulter le statut du dossier en attente.'))

    def test_pending_excludes_rejection_before_priority_and_model(self):
        rejected = mark_excerpt('Consulter le motif exact du refus puis renvoyer le référentiel.',
                                title="Rejet d'un référentiel", priority=300)
        waiting = mark_excerpt('Le statut du dossier en attente est visible dans le suivi du dossier.', title='Suivi du dossier')
        llm = FakeLLM([{'claims': []}]); audit = {}
        review_exam_answer(llm, question='Référentiel en attente de validation depuis longtemps',
                           public='Lycée Général & Techno', documents=rejected+'\n'+waiting, audit=audit)
        self.assertEqual(audit['excluded_situation_documents'], ['D1'])
        self.assertEqual(audit['model_document_ids'], ['D2'])
        self.assertNotIn('motif exact du refus', llm.prompts[0])

    def test_pending_rejection_steps_are_never_rendered_after_failed_repair(self):
        source = 'Consulter le motif exact du refus puis renvoyer le référentiel.'
        output = {'claims': [{'section': 'etape', 'text': source,
                             'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}]}
        llm = FakeLLM([output, output]); audit = {}
        with self.assertRaises(ValueError):
            review_exam_answer(llm, question='Référentiel en attente de validation', public='GT',
                               documents=mark_excerpt(source, title='Guide'), audit=audit)
        self.assertTrue(audit['final_rejections'])
        self.assertNotIn('rendered_answer', audit)

    def test_shn_ordinary_conditions_require_late_status_antecedent(self):
        source = Path('data/examens/shn_statut_inscription_gt.txt').read_text()
        claim = {'section': 'decision', 'text': 'Le SHN est évalué dans les conditions ordinaires, sans aménagement spécifique.',
                 'evidence': [{'quote': source}]}
        q = "SHN évalué lors d'un seul cycle : comment le noter ?"
        self.assertTrue(conditional_extraction_errors([claim], q))
        self.assertFalse(conditional_extraction_errors([claim], 'SHN : statut obtenu après la clôture des inscriptions.'))
        claim['text'] = "Si le statut est obtenu après la clôture des inscriptions, le SHN est évalué dans les conditions ordinaires."
        self.assertFalse(conditional_extraction_errors([claim], q))

    def test_shn_generated_error_is_repaired_instead_of_published(self):
        source = Path('data/examens/shn_statut_inscription_gt.txt').read_text()
        def output(text):
            return {'claims': [{'section':'decision', 'text':text,
                               'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}
        llm = FakeLLM([
            output('Le SHN est évalué dans les conditions ordinaires, sans aménagement spécifique.'),
            output("Si le statut est obtenu après la clôture des inscriptions, le candidat est évalué dans les conditions ordinaires."),
        ]); audit = {}
        result = review_exam_answer(llm, question='SHN : un seul cycle évalué, quelle notation ?',
                                   public='Lycée Général & Techno', documents=mark_excerpt(source), audit=audit)
        self.assertTrue(audit['initial_rejections'])
        self.assertIn('Si le statut', result)
        self.assertEqual(len(llm.prompts), 2)

    def test_ipack_uses_proof_review_and_keeps_diagnostic(self):
        tree = ast.parse(Path('app.py').read_text())
        # Vérifier le chemin réel d'appel, pas seulement une consigne dans le prompt.
        branches = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                    and ast.unparse(n.test) == "mode in ('examens', 'ipack')"]
        self.assertTrue(any(any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                                    and x.func.id == 'review_exam_answer'
                                    for child in b.body for x in ast.walk(child)) for b in branches))

if __name__ == '__main__':
    unittest.main()
