"""Régressions métier EPS : recherche réelle, sources contrôlées, portée et repli.

Le faux modèle vérifie le circuit, pas la justesse d'une génération réelle.
"""
import ast
import unittest
from pathlib import Path

import knowledge_catalog as kc
from documentary_review import (
    mark_excerpt, render_exam_fallback, review_exam_answer, scoped_claim_text,
    source_packets,
)
from test_documentary_review import FakeLLM
import test_documentation as routing_tests


class TextesProofWorkflowTests(unittest.TestCase):
    def test_textes_calls_the_same_proof_workflow(self):
        tree = ast.parse(Path('app.py').read_text())
        parents = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'review_exam_answer']
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertTrue(any(k.arg == 'mode' and isinstance(k.value, ast.Name)
                            and k.value.id == 'mode' for k in call.keywords))
        node = parents[call]
        # Le premier If est désormais le choix du mode fidèle : la revue libre
        # est dans son else. Vérifier le garde de domaine qui englobe les deux.
        while not (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                   and isinstance(node.test.left, ast.Name) and node.test.left.id == 'mode'):
            node = parents[node]
        for mode in ('textes', 'examens', 'ipack'):
            self.assertTrue(eval(compile(ast.Expression(node.test), 'app.py', 'eval'), {'mode': mode}))

    def test_real_imp_request_reaches_identified_national_source(self):
        route = routing_tests.DocumentationTests()
        route.setUp()
        body, _, _, error = route.route(
            'Nous sommes six professeurs EPS pour huit cents élèves : combien d’IMP de coordo ?',
            'Collège (DNB)', 'textes')
        self.assertFalse(error)
        packets = source_packets(body)
        national = [p for p in packets if 'base_textes_officiels_061_' in p['path']]
        self.assertEqual(len(national), 1)
        self.assertIn('équivalent temps plein', national[0]['text'])
        self.assertIn('MENH1506032C', national[0]['text'])

    def test_used_source_and_cost_are_traced_without_unrelated_dnb(self):
        docs = mark_excerpt('La coordination concerne plus de quatre équivalents temps plein.',
                            title='Coordination EPS', priority=320)
        docs += '\n\n' + mark_excerpt('La moyenne annuelle EPS participe au brevet.', title='Calcul DNB')
        llm = FakeLLM([{'claims': [{'section': 'condition',
                                  'text': 'La coordination concerne plus de quatre équivalents temps plein.',
                                  'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}]}])
        audit = {}
        result = review_exam_answer(llm, question='IMP de coordination EPS ?', public='Collège (DNB)',
                                    documents=docs, audit=audit, mode='textes', academy='Non précisée')
        self.assertEqual(len(llm.prompts), 1)
        self.assertEqual(audit['model_document_ids'], ['D1'])
        self.assertNotIn('Calcul DNB', llm.prompts[0])
        self.assertIn('équivalents temps plein', result)
        self.assertEqual(audit['accepted_claims'][0]['evidence'][0]['document_id'], 'D1')

    def test_missing_passage_is_not_published_as_a_citation(self):
        docs = mark_excerpt('La coordination dépend des équivalents temps plein.', title='Coordination EPS')
        invented = {'claims': [{'section': 'decision', 'text': 'Six personnes prouvent six temps pleins.',
                                'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P999']}]}]}
        llm = FakeLLM([invented, {'claims': []}])
        audit = {}
        result = review_exam_answer(llm, question='Combien d’IMP ?', public='Collège (DNB)',
                                    documents=docs, mode='textes', audit=audit)
        self.assertTrue(audit['initial_rejections'])
        self.assertEqual(len(llm.prompts), 2)
        self.assertNotIn('Six personnes', result)
        self.assertNotIn('service des examens', result)

    def test_textes_local_reserve_does_not_send_career_to_exam_service(self):
        claim = {'text': 'Le service local confirme la procédure.',
                 'evidence': [{'scope': {'academy': 'Aix-Marseille', 'not_confirmed_for': 'Créteil'}}]}
        self.assertIn('service compétent', scoped_claim_text(claim, mode='textes'))
        self.assertIn('service des examens', scoped_claim_text(claim, mode='examens'))
        self.assertNotIn('service des examens', render_exam_fallback({}, question='recours PPCR', mode='textes'))

    def test_regulatory_topics_keep_decisive_conditions_in_retrieval(self):
        cases = [
            ('Surveillance des vestiaires en EPS', 'peut être nécessaire'),
            ('Parade et contacts corporels en EPS', 'ne permet pas de qualifier automatiquement'),
            ('Punition collective et zéro pour bavardage', 'motif exclusivement disciplinaire'),
            ('Pollution ozone et EPS en intérieur', 'population générale'),
            ('Mutation : contestation du barème ou recours', 'deux contestations différentes'),
        ]
        for question, condition in cases:
            with self.subTest(question=question):
                self.assertIn(condition, kc.priority_context(question, 'Collège (DNB)', 'textes'))


if __name__ == '__main__':
    unittest.main()

