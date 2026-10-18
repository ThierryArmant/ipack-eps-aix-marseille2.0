import ast
import unittest
from pathlib import Path
from claim_guards import unsupported_certainty, operation_errors
from documentary_review import mark_excerpt, source_packets, validate_claims, review_exam_answer
from test_documentary_review import FakeLLM


class ClaimGuardsTests(unittest.TestCase):
    def test_absence_does_not_prove_permission_or_prohibition(self):
        proof = "Communication des notes : aucune consigne écrite n'a été retrouvée dans la documentation disponible."
        for text in ('La communication des notes est interdite avant le jury.',
                     'La communication des notes est autorisée avant le jury.',
                     'La communication des notes est obligatoire. À vérifier auprès du service.'):
            with self.subTest(text=text):
                packets = source_packets(mark_excerpt(proof, title='Communication des notes'))
                accepted, errors = validate_claims({'claims': [{'section': 'decision', 'text': text,
                    'evidence': [{'document_id': 'D1', 'quote': proof}]}]}, packets)
                self.assertFalse(accepted)
                self.assertTrue(any('absence de consigne' in str(e) for e in errors))

    def test_reserve_and_documented_rule_remain_possible(self):
        absence = 'Aucune consigne écrite retrouvée sur la communication des notes.'
        for text in ('On ne peut pas confirmer que la communication des notes est interdite.',
                     'Vous devez faire confirmer la communication des notes auprès du service.'):
            self.assertFalse(unsupported_certainty(text, [absence]))
        self.assertFalse(unsupported_certainty('La communication des notes est interdite.',
                         [absence, 'La communication des notes est interdite avant le jury.']))
        self.assertFalse(unsupported_certainty('La saisie est impossible.', ['La saisie est impossible dans cet outil.']))

    def test_operations_and_tools_are_not_interchanged(self):
        for q, text in [('Comment supprimer ce créneau ?', 'Restaurez le créneau dans le menu.'),
                        ('Comment récupérer ce créneau ?', 'Supprimez le créneau dans le menu.'),
                        ('Supprimer un protocole dans Cyclades', 'Supprimez le protocole dans iPackEPS.')]:
            self.assertTrue(operation_errors([{'text': text}], q))
        for text in ('Supprimez le créneau dans le menu.',
                     'Ne restaurez pas le créneau.',
                     'La restauration du créneau est impossible.',
                     'Dans le menu Restaurer ou Supprimer, supprimez le créneau.',
                     'La restauration ne permet pas de supprimer un créneau.'):
            self.assertFalse(operation_errors([{'text': text}], 'Comment supprimer le créneau ?'))

    def test_failed_operation_repaired_once_only(self):
        proof = 'Pour le créneau, le menu propose Supprimer pour supprimer et Restaurer pour restaurer.'
        def response(text):
            return {'claims': [{'section': 'etape', 'text': text,
                               'evidence': [{'document_id': 'D1', 'quote': proof}]}]}
        llm = FakeLLM([response('Restaurez le créneau dans le menu.'), response('Supprimez le créneau dans le menu.')])
        audit = {}
        answer = review_exam_answer(llm, question='Comment supprimer un créneau ?', public='Collège',
                    documents=mark_excerpt(proof, title='Créneau'), audit=audit, mode='ipack')
        self.assertIn('Supprimez', answer)
        self.assertEqual(len(llm.prompts), 2)
        self.assertTrue(audit['repair_successful'])

    def test_legacy_shortcuts_stay_disabled(self):
        tree = ast.parse(Path('app.py').read_text())
        disabled = {target.id for node in ast.walk(tree) if isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Constant) and node.value.value is False
                    for target in node.targets if isinstance(target, ast.Name)}
        self.assertTrue({'est_date', 'est_tasa', 'est_sujet_secours', 'est_saisir_notes'} <= disabled)

    def test_no_third_call_after_two_failed_answers(self):
        proof = 'Pour le créneau, le menu propose Supprimer pour supprimer et Restaurer pour restaurer.'
        bad = {'claims': [{'section': 'etape', 'text': 'Restaurez le créneau dans le menu.',
                          'evidence': [{'document_id': 'D1', 'quote': proof}]}]}
        llm = FakeLLM([bad, bad])
        with self.assertRaises(ValueError):
            review_exam_answer(llm, question='Comment supprimer un créneau ?', public='Collège',
                               documents=mark_excerpt(proof, title='Créneau'), mode='ipack')
        self.assertEqual(len(llm.prompts), 2)

    def test_documentary_modes_skip_paid_arbiter(self):
        tree = ast.parse(Path('app.py').read_text())
        arbiters = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                    and any(isinstance(call, ast.Assign)
                            and any(isinstance(t, ast.Name) and t.id == '_verdict' for t in call.targets)
                            for stmt in node.body for call in ast.walk(stmt))]
        self.assertTrue(any('mode not in' in ast.unparse(node.test)
                            and all(m in ast.unparse(node.test) for m in ('examens', 'ipack', 'textes'))
                            for node in arbiters))

    def test_corpus_silence_does_not_prove_nonexistence(self):
        proof = "Aucun texte de la base n'interdit ni n'organise cette communication. Faire confirmer la consigne."
        self.assertTrue(unsupported_certainty("Il n'existe pas de règle écrite interdisant cette communication.", [proof]))
        self.assertFalse(unsupported_certainty("Aucun texte de la base ne permet de confirmer une interdiction de cette communication.", [proof]))
