"""Conditions et réserves : vraie chaîne documentaire, modèles simulés sans réseau."""
import json
from pathlib import Path
import unittest
from documentary_review import (mark_excerpt, source_packets, source_limits_for_rejections,
                                validate_claims, review_exam_answer)
from claim_guards import unsupported_certainty
from test_documentary_review import FakeLLM

CONTACT = 'data/ipack/qui_contacter_assistance_ipackeps.txt'
RENEW = 'data/ipack/fiches/ipack_083_article_94_dossiers_dossier_sss_evolution_demande_de_reconduction_ou_fermeture_d_une_sss.txt'
COORD = 'data/ipack/complement_cyclades_cas_pratiques.txt'
COLLEGE = 'data/ipack/visite_college_2026_10_18/college_pas_de_dossier_certificatif.txt'

class ComparisonFollowupTests(unittest.TestCase):
    def test_contact_orientation_survives_misquoted_bounded_reserve_without_repair(self):
        docs = mark_excerpt(Path(CONTACT).read_text(), path=CONTACT)
        packet = source_packets(docs)[0]
        role = next(s for s in packet['passages'] if s['text'].startswith('- La DEC'))
        wrong = next(s for s in packet['passages'] if s['text'].startswith('- Académie'))
        proposal = {'claims': [
            {'section': 'decision', 'text': 'Pour une incohérence de données, contacter la DEC (division des examens et concours) de son académie.',
             'evidence': [{'document_id': 'D1', 'passage_ids': [role['id']]}]},
            {'section': 'limite', 'text': "Les informations concernant la DEC pour l'académie de Lyon ne sont pas spécifiquement documentées dans les passages fournis.",
             'evidence': [{'document_id': 'D1', 'passage_ids': [wrong['id']]}]}]}
        llm, audit = FakeLLM([proposal]), {}
        answer = review_exam_answer(llm, question='Qui contacter à la division des examens pour une incohérence de données ?',
                                   public='GT', mode='examens', documents=docs, audit=audit)
        self.assertEqual(len(llm.prompts), 1)
        self.assertTrue(audit['documentary_limit_extraction'])
        self.assertFalse(audit['repair_performed'])
        self.assertFalse(audit['final_rejections'])
        self.assertIn('contacter la DEC', answer)
        self.assertIn('coordonnées de DEC', answer)
        self.assertNotIn('ipackeps@', answer)

    def test_reserve_recovery_does_not_infer_silence_from_unrelated_document(self):
        packets = source_packets(mark_excerpt(Path(CONTACT).read_text(), path=CONTACT))
        wrong = packets[0]['passages'][-1]['id']
        claim = {'section': 'limite', 'text': 'Les informations concernant la procédure ne sont pas documentées dans les passages fournis.',
                 'evidence': [{'document_id': 'D1', 'passage_ids': [wrong]}]}
        err = {'claim': claim, 'errors': ['passage cité sans rapport avec l’affirmation : choisir le passage qui l’énonce']}
        self.assertEqual(source_limits_for_rejections([err], packets, 'Comment déposer une convention sportive ?'), [])
        claim['text'] += ' Vous devez déposer la convention.'
        self.assertEqual(source_limits_for_rejections([err], packets, 'Qui contacter à la division des examens ?'), [])
        claim['text'] = 'Les informations concernant la procédure ne sont pas documentées dans les passages fournis.'
        err['errors'].append('document inconnu')
        self.assertEqual(source_limits_for_rejections([err], packets, 'Qui contacter à la division des examens ?'), [])

    def test_explicit_limit_does_not_authorize_annex_upload(self):
        packets = source_packets(mark_excerpt(Path(RENEW).read_text(), path=RENEW))
        proof = next(s['text'] for s in packets[0]['passages'] if 'la possibilité de déposer' in s['text'])
        all_proofs = '\n'.join(s['text'] for s in packets[0]['passages'])
        self.assertIn('signature obligatoire', all_proofs)
        self.assertIn('Projet Annuel SSS', all_proofs)
        self.assertTrue(unsupported_certainty('Les pièces en annexe doivent être déposées dans [Évolution].', [proof]))
        self.assertTrue(unsupported_certainty('Les pièces complémentaires doivent être jointes à la demande dans le même module [Évolution].', [proof]))
        self.assertFalse(unsupported_certainty('Les passages ne permettent pas de confirmer la possibilité de déposer ces pièces en annexe dans [Évolution].', [proof]))

    def test_role_prerequisite_is_self_contained_after_real_splitting(self):
        packets = source_packets(mark_excerpt(Path(COORD).read_text(), path=COORD))
        text = next(s['text'] for p in packets for s in p['passages'] if s['text'].startswith('- Gestion des examens — préalable'))
        self.assertIn('Responsable de la Certification', text)
        self.assertIn('Coordonnateur EPS', text)
        self.assertIn('ne remplace pas', text)
        self.assertIn('Ma fiche professeur > Fonctions', text)

    def test_college_anomaly_and_regular_dossier_remain_documented(self):
        packets = source_packets(mark_excerpt(Path(COLLEGE).read_text(), path=COLLEGE))
        proofs = '\n'.join(s['text'] for p in packets for s in p['passages'])
        self.assertIn('ne sont pas une exigence normale du collège', proofs)
        self.assertIn('Cette Fonctionnalité est désactivée', proofs)
        self.assertIn('[Dossier EPS] > [Vérification]', proofs)
        self.assertIn('moyennes validées en conseil de classe', proofs)
