import copy
import hashlib
import json
import unittest
from types import SimpleNamespace

from documentary_review import mark_excerpt, source_packets, review_exam_answer, validate_claims, TracedLLM
import test_documentation as routing_tests

TEXT = "L'opérateur demande au responsable habilité d'ouvrir le dossier. Une fois ouvert, il corrige la valeur puis referme le dossier."
DOC = mark_excerpt(TEXT + '\nNature de la source : fonctionnement du logiciel ; aucun texte du Bulletin officiel ne prescrit cette procédure.',
                   path='guide.txt', title='Guide de saisie')
CHECKS = dict(supported=True, applicable=True, source_correct=True, conditions_preserved=True)


def claim(text="Demandez au responsable habilité d'ouvrir le dossier.", quote=TEXT, level='logiciel'):
    return {'section': 'decision', 'text': text,
            'evidence': [{'document_id': 'D1', 'quote': quote, 'level': level}], 'checks': CHECKS.copy()}


class FakeLLM:
    model = 'test-model'
    temperature = 0
    def __init__(self, outputs):
        self.outputs, self.prompts = iter(outputs), []
    def complete(self, prompt):
        self.prompts.append(prompt)
        output = next(self.outputs)
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(text=json.dumps(output, ensure_ascii=False) if isinstance(output, dict) else output)


class DocumentaryReviewTests(unittest.TestCase):
    def test_exclusive_general_fiche_preserves_specific_branches(self):
        route = routing_tests.DocumentationTests()
        route.setUp()
        text, sources, _, error = route.route(
            "Mon élève est inapte sur deux épreuves et n'a qu'une note de 14. Je saisis DI+DI+14 ou DI+DI+DI ?",
            'Lycée Général & Techno', 'examens')
        self.assertIn('DI + DI + 14', text)
        self.assertIn('DI + DI + DI', text)
        self.assertTrue(any('DI+DI+Note' in title for title, _ in sources))
        self.assertEqual(error, '')

    def test_review_uses_exact_current_documents_and_never_untrusted_draft(self):
        llm = FakeLLM([{'claims': [claim()]}, {'claims': [claim()]}])
        audit = {}
        result = review_exam_answer(llm, question='Comment corriger mon dossier ?', public='GT', documents=DOC,
                                   draft='BROUILLON : le décret oblige à ouvrir le dossier.', audit=audit)
        self.assertIn("Demandez au responsable", result)
        self.assertIn('Documentation du logiciel', result)
        self.assertEqual(len(llm.prompts), 2)
        self.assertNotIn('BROUILLON', '\n'.join(llm.prompts))
        self.assertEqual(audit['context_exact'], DOC)
        self.assertEqual([c['prompt'] for c in audit['calls']], llm.prompts)
        self.assertEqual(audit['context_sha256'], hashlib.sha256(DOC.encode()).hexdigest())
        self.assertEqual(audit['accepted_claims'][0]['evidence'][0]['quote'], TEXT)

    def test_unknown_document_or_misattributed_literal_quote_rejected(self):
        other = mark_excerpt("Le décret définit le calendrier annuel, sans fixer de menu logiciel.", title='Décret')
        bad = claim()
        bad['evidence'][0]['document_id'] = 'D2'
        accepted, rejected = validate_claims({'claims': [bad]}, source_packets(DOC + '\n\n' + other))
        self.assertFalse(accepted)
        self.assertIn('citation absente', ' '.join(rejected[0]['errors']))
        bad['evidence'][0]['document_id'] = 'D999'
        self.assertFalse(validate_claims({'claims': [bad]}, source_packets(DOC))[0])

    def test_software_packet_cannot_be_relabeled_as_regulatory(self):
        bad = claim(level='reglementaire')
        accepted, errors = validate_claims({'claims': [bad]}, source_packets(DOC))
        self.assertFalse(accepted)
        self.assertIn('nature de source incompatible', ' '.join(errors[0]['errors']))

    def test_reference_anywhere_in_context_does_not_support_claim(self):
        bad = claim(text='Selon MENE1234567N, ouvrez le dossier.')
        other = mark_excerpt('NOR MENE1234567N : calendrier annuel de certification.', title='Calendrier')
        self.assertFalse(validate_claims({'claims': [bad]}, source_packets(DOC + '\n\n' + other))[0])
        # Même dans le bon document, un NOR sans rapport avec la citation ne suffit pas.
        self.assertFalse(validate_claims({'claims': [bad]}, source_packets(DOC + '\nNOR MENE1234567N'))[0])

    def test_typographic_quote_is_tolerated_but_paraphrase_is_not(self):
        good = claim(quote=TEXT.replace("'", '’').replace(' ', '\n'))
        self.assertTrue(validate_claims({'claims': [good]}, source_packets(DOC))[0])
        bad = claim(quote='Le professeur ouvre lui-même le dossier puis le clôture.')
        self.assertFalse(validate_claims({'claims': [bad]}, source_packets(DOC))[0])

    def test_false_applicability_and_missing_conditions_stop_publication(self):
        for key in CHECKS:
            bad = claim()
            bad['checks'][key] = False
            llm = FakeLLM([{'claims': [claim()]}, {'claims': [claim(), bad]}])
            with self.subTest(key=key), self.assertRaises(ValueError):
                review_exam_answer(llm, question='Q', public='GT', documents=DOC)

    def test_invalid_json_is_repaired_by_verification_not_published(self):
        llm = FakeLLM(['Réponse non structurée avec une référence inventée', {'claims': [claim()]}])
        audit = {}
        self.assertIn('Demandez', review_exam_answer(llm, question='Q', public='GT', documents=DOC, audit=audit))
        self.assertTrue(audit['initial_rejections'])
        self.assertIn('ERREURS MECANIQUES', llm.prompts[-1])

    def test_empty_or_invalid_final_does_not_fall_back_to_draft(self):
        for output in ('', {'claims': []}, {'claims': [claim(quote='Citation inventée suffisamment longue.')]}):
            with self.subTest(output=output), self.assertRaises(ValueError):
                review_exam_answer(FakeLLM([{'claims': [claim()]}, output]),
                                   question='Q', public='GT', documents=DOC, draft='à ne jamais afficher')

    def test_model_error_is_traced_without_copying_secret_exception(self):
        audit = {}
        with self.assertRaises(RuntimeError):
            TracedLLM(FakeLLM([RuntimeError('secret-not-to-save')]), audit).complete('PROMPT EXACT')
        self.assertEqual(audit['calls'][0]['prompt'], 'PROMPT EXACT')
        self.assertEqual(audit['calls'][0]['error'], 'RuntimeError')
        self.assertNotIn('secret-not-to-save', str(audit))

    def test_all_packets_and_complementary_context_preserved(self):
        context = 'FAITS DE DÉPART\n' + DOC + '\n' + mark_excerpt('Une seconde possibilité conditionnelle est documentée.', title='Complément')
        packets = source_packets(context)
        self.assertEqual(len(packets), 3)
        self.assertIn('FAITS DE DÉPART', packets[0]['text'])
        self.assertEqual(packets[1]['path'], 'guide.txt')
        self.assertIn('seconde possibilité', packets[2]['text'])

    def test_metadata_only_and_markup_are_not_publishable_claims(self):
        for bad in (claim(quote='Nature de la source : fonctionnement du logiciel ; aucun texte du Bulletin officiel ne prescrit cette procédure.'),
                    claim(text='<script>alert(1)</script>')):
            self.assertFalse(validate_claims({'claims': [bad]}, source_packets(DOC))[0])

    def test_real_routing_preserves_identity_and_declared_nature(self):
        route = routing_tests.DocumentationTests()
        route.setUp()
        text, _, _, _ = route.route("J'ai verrouillé mon lot par erreur et je dois corriger une note.",
                                   'Lycée Général & Techno', 'examens')
        packets = source_packets(text)
        relevant = next(p for p in packets if p['path'].endswith('j2_procedure_verifiee.txt'))
        self.assertNotIn('reglementaire', relevant['niveaux_autorises'])
        self.assertIn('aucun texte du Bulletin officiel', relevant['nature_declaree'])


if __name__ == '__main__':
    unittest.main()
