import unittest
from types import SimpleNamespace

from documentary_review import review_exam_answer, validated_review
import test_documentation as routing_tests


class DocumentaryReviewTests(unittest.TestCase):
    def test_exclusive_general_fiche_preserves_specific_branches(self):
        route = routing_tests.DocumentationTests()
        route.setUp()
        text, sources, _, error = route.route(
            "Mon élève est inapte sur deux épreuves et n'a qu'une note de 14. Je saisis DI+DI+14 ou DI+DI+DI ?",
            'Lycée Général & Techno', 'examens',
        )
        self.assertIn('DI + DI + 14', text)
        self.assertIn('DI + DI + DI', text)
        self.assertIn('Les deux saisies sont possibles', text)
        self.assertTrue(any('DI+DI+Note' in title for title, _ in sources))
        self.assertEqual(error, '')

    def test_review_uses_current_documents_and_returns_generated_answer(self):
        calls = []
        def complete(prompt):
            calls.append(prompt)
            return SimpleNamespace(text='{"verifications":[{"preuve":"GUIDE ACTUALISÉ"}],"reponse_html":"Réponse générée depuis les documents courants"}')
        result = review_exam_answer(
            SimpleNamespace(complete=complete), question='Une situation nouvelle',
            public='Lycée Général & Techno', documents='GUIDE ACTUALISÉ',
            draft='Brouillon contradictoire',
        )
        self.assertEqual(result, 'Réponse générée depuis les documents courants')
        self.assertIn('GUIDE ACTUALISÉ', calls[0])
        self.assertIn('Une situation nouvelle', calls[0])
        self.assertIn('Brouillon contradictoire', calls[0])

    def test_empty_review_does_not_silently_publish_unchecked_draft(self):
        with self.assertRaises(ValueError):
            review_exam_answer(SimpleNamespace(complete=lambda _: SimpleNamespace(text='')),
                               question='Q', public='GT', documents='D', draft='B')

    def test_invented_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            review_exam_answer(SimpleNamespace(complete=lambda _: SimpleNamespace(
                text='{"verifications":[{"preuve":"Passage inventé"}],"reponse_html":"Erreur"}')),
                question='Q', public='GT', documents='Guide fourni', draft='B')

    def test_typographic_variations_keep_the_same_words(self):
        raw = '{"verifications":[{"preuve":"L’enseignant **corrige** la note."}],"reponse_html":"Réponse"}'
        self.assertEqual(validated_review(raw, "L'enseignant corrige la note."), 'Réponse')

    def test_invalid_first_proof_is_retried_against_documents(self):
        replies = iter([
            '{"verifications":[{"preuve":"Inventé"}],"reponse_html":"Erreur"}',
            '{"verifications":[{"preuve":"Guide fourni"}],"reponse_html":"Réponse relue"}',
        ])
        llm = SimpleNamespace(complete=lambda _: SimpleNamespace(text=next(replies)))
        self.assertEqual(review_exam_answer(llm, question='Q', public='GT',
                        documents='Guide fourni', draft='B'), 'Réponse relue')
