import unittest
from pathlib import Path

from documentary_review import (mark_excerpt, review_exam_answer, render_exam_fallback,
                                lexical_support_details, validate_claims, source_packets)
from test_documentary_review import FakeLLM


class ExamFallbackTests(unittest.TestCase):
    def test_failed_review_does_not_publish_valid_but_incomplete_generated_claims(self):
        document = mark_excerpt(
            "Le responsable ouvre le dossier uniquement après vérification des pièces.\n\n"
            "Il conserve les pièces et referme le dossier.", title="Dossier et pièces", priority=300)
        proposal = {'claims': [
            {'section': 'decision', 'text': 'Décision inventée non justifiée.',
             'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P999']}]},
            {'section': 'etape', 'text': 'Conservez les pièces du dossier.',
             'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P2']}]},
        ]}
        llm, audit = FakeLLM([proposal, proposal]), {}
        with self.assertRaises(ValueError):
            review_exam_answer(llm, question='Comment ouvrir le dossier ?', public='GT',
                               documents=document, audit=audit)
        self.assertTrue(audit['accepted_claims'])
        result = render_exam_fallback(audit, question='Comment ouvrir le dossier ?')
        self.assertIn('Réponse non confirmée', result)
        self.assertIn('uniquement après vérification des pièces', result)
        self.assertNotIn('Décision inventée', result)
        self.assertNotIn('Conservez les pièces du dossier.', result)
        self.assertEqual(len(llm.prompts), 2)
        self.assertEqual(audit['fallback_document_ids'], ['D1'])

    def test_network_failure_preserves_documents_without_exposing_exception(self):
        document = mark_excerpt('Le responsable vérifie les pièces du dossier.', title='Dossier', priority=300)
        audit = {}
        with self.assertRaises(RuntimeError):
            review_exam_answer(FakeLLM([RuntimeError('secret-token')]), question='Dossier ?',
                               public='GT', documents=document, audit=audit)
        result = render_exam_fallback(audit, question='Dossier ?')
        self.assertIn('Le responsable vérifie les pièces du dossier.', result)
        self.assertNotIn('secret-token', result)
        self.assertNotIn('secret-token', str(audit))

    def test_foreign_academy_keeps_scope_and_escaped_literal_excerpt(self):
        path = 'data/commun/audit60/aix_protocoles_2026.txt'
        document = mark_excerpt(Path(path).read_text(), path=path, priority=300)
        audit = {'documents': source_packets(document)}
        result = render_exam_fallback(audit, question='Protocoles 2026 ?', academy='Créteil')
        self.assertIn('Créteil', result)
        self.assertIn('Aix-Marseille', result)
        self.assertTrue(audit['fallback_passage_ids'])

    def test_missing_or_unrelated_documents_produce_only_unconfirmed_message(self):
        for context in ('', mark_excerpt('Le calendrier du calendrier est annuel.', title='Calendrier')):
            with self.subTest(context=context):
                result = render_exam_fallback({}, question='Comment déverrouiller un dossier ?', documents=context)
                self.assertIn('service des examens de votre académie', result)
                self.assertNotIn('<blockquote>', result)

    def test_excerpt_does_not_cut_condition_or_redisplay_html_as_markup(self):
        body = 'Le dossier est ouvert uniquement après vérification. <script>secret</script>\n\n' + 'Condition obligatoire ' * 250 + ' <script>fin</script>'
        audit = {'documents': source_packets(mark_excerpt(body, title='Dossier'))}
        result = render_exam_fallback(audit, question='Dossier ?')
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('Condition obligatoire', result)
        self.assertIn('&lt;script&gt;fin&lt;/script&gt;', result)
        self.assertIn('<details>', result)
        self.assertIn('Afficher la suite du document', result)
        self.assertEqual(audit['fallback_available_passage_ids'], ['D1P1', 'D1P2'])
        self.assertEqual(audit['fallback_passage_ids'], ['D1P1'])
        self.assertIn('Extrait incomplet', result)
        self.assertFalse(audit['fallback_excerpt_complete'])

    def test_rejection_trace_explains_minimum_shared_roots(self):
        ps = source_packets(mark_excerpt('Le calendrier annuel précise les réunions du jury.'))
        rejected = {'section': 'decision', 'text': 'Le professeur sanctionne immédiatement la fraude.',
                    'evidence': [{'document_id': 'D1', 'passage_ids': ['D1P1']}]}
        good, errors = validate_claims({'claims': [rejected]}, ps)
        self.assertFalse(good)
        details = errors[0]['lexical_check']
        self.assertFalse(details['passed'])
        self.assertIsNone(details['minimum_coverage'])
        self.assertEqual(details['coverage'], 0)
        self.assertEqual(details, lexical_support_details(rejected['text'], [ps[0]['text']]))

    def test_supported_paraphrases_from_r04_r08_are_not_rejected_by_length(self):
        cases = [
            ("L'élève ayant un arrêt de trois semaines qui couvre la date de rattrapage du badminton peut conserver ses deux autres notes si un certificat médical est déposé.",
             "La note finale d'EPS est la moyenne des 2 notes déjà obtenues, sous réserve que l'inaptitude médicale soit dûment certifiée."),
            ("Le sportif de haut niveau (SHN) peut obtenir un 20/20 dans Santorin pour son APSA, même si le protocole de sa classe n'inclut pas de sport de combat, à condition que la mention SHN figure pour l'élève dans Santorin.",
             "2. La mention SHN figure-t-elle pour l'élève dans Santorin ? À Aix-Marseille, elle est saisie dans Cyclades par le gestionnaire EPS de la DIEC. Si elle manque, le chef d'établissement le signale à la DIEC : ni l'enseignant ni l'établissement ne peuvent l'ajouter."),
        ]
        for claim, passage in cases:
            with self.subTest(claim=claim):
                details = lexical_support_details(claim, [passage])
                self.assertLess(details['coverage'], 0.3)
                self.assertGreaterEqual(len(details['shared_roots']), 2)
                self.assertTrue(details['passed'])

    def test_document_identifiers_remain_private_and_article_title_is_visible(self):
        body = ('[Base iPackEPS] [DOCUMENT: data/private.txt; statut: synthese_non_revalidee]\n\n'
                '[ARTICLE 55] Dossier certificatif\n\n'
                '[FICHE PRIORITAIRE — statut: verifie] Le dossier conserve les certificats médicaux.')
        audit = {'documents': source_packets(mark_excerpt(body))}
        result = render_exam_fallback(audit, question='Dossier certificatif ?')
        self.assertNotIn('data/private.txt', result)
        self.assertNotIn('synthese_non_revalidee', result)
        self.assertNotIn('FICHE PRIORITAIRE', result)
        self.assertNotIn('statut:', result)
        self.assertIn('[ARTICLE 55] Dossier certificatif', result)
        self.assertEqual(audit['fallback_sources'][0]['title'], '[ARTICLE 55] Dossier certificatif')


if __name__ == '__main__':
    unittest.main()
