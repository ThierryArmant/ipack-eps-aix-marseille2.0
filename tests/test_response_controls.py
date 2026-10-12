import unittest
from response_controls import complete_gt_shn_conditions, documented_dnb_dispense, reference_url, constrain_santorin_unlock, prevent_invented_gt_medical_sequence

CTX = '### Bac général et technologique : SHN et sportifs non listés MENE2531948N'

class ResponseControlsTests(unittest.TestCase):
    def test_omitted_conditions_are_completed(self):
        answer = complete_gt_shn_conditions('Bac GT EPS SHN', 'L’élève peut bénéficier d’un aménagement.', CTX)
        for word in ('justifié', 'comité de pilotage', 'validation par le recteur'):
            self.assertIn(word, answer)

    def test_complete_answer_is_not_duplicated(self):
        answer = 'Statut justifié, proposition du comité de pilotage et validation par le recteur.'
        self.assertEqual(complete_gt_shn_conditions('Bac GT SHN', answer, CTX), answer)

    def test_other_diplomas_options_errors_and_missing_source_are_preserved(self):
        answer = 'Une seule activité au CAP.'
        self.assertEqual(complete_gt_shn_conditions('CAP SHN', answer, '[PORTEE: cap]'), answer)
        self.assertEqual(complete_gt_shn_conditions('Option EPS SHN', answer, CTX), answer)
        self.assertEqual(complete_gt_shn_conditions('EPPCS SHN', answer, CTX), answer)
        self.assertEqual(complete_gt_shn_conditions('Bac GT', answer, ''), answer)
        self.assertEqual(complete_gt_shn_conditions('Bac GT', 'Erreur de traitement IA : timeout', CTX), 'Erreur de traitement IA : timeout')

    def test_school_sport_etudes_question_does_not_add_exam_conditions(self):
        answer = 'Un aménagement individuel sport-études est possible.'
        self.assertEqual(complete_gt_shn_conditions('Un élève isolé peut-il bénéficier d’un sport-études ?', answer, CTX), answer)

    def test_documented_dnb_dispense_is_distinct_from_unresolved_medical_status(self):
        self.assertTrue(documented_dnb_dispense('DNB 2027 : dispense réglementaire attestée, mention LSU ?', 'Collège (DNB)'))
        self.assertFalse(documented_dnb_dispense('DNB inaptitude, zéro ou DI ?', 'Collège (DNB)'))
        self.assertFalse(documented_dnb_dispense('CAP dispense réglementaire attestée', 'Lycée Pro / CAP'))

    def test_reference_url_tracks_explicit_session(self):
        md = {'url': 'current', 'urls_par_session': {'2026': 'old', '2027': 'current'}}
        self.assertEqual(reference_url(md, 'DNB 2026 LSU'), 'old')
        self.assertEqual(reference_url(md, 'DNB 2027 LSU'), 'current')
        self.assertEqual(reference_url(md, '2026 ou 2027 ?'), 'current')

    def test_unlock_rights_are_not_inferred_from_unverified_document(self):
        self.assertIn('ne permettent pas de confirmer', constrain_santorin_unlock('Santorin mon lot est fermé', 'Seul le chef peut déverrouiller.', 'statut: synthese_non_revalidee'))
        self.assertEqual(constrain_santorin_unlock('Santorin saisir une note', 'Réponse', ''), 'Réponse')
        self.assertEqual(constrain_santorin_unlock('Santorin déverrouiller', 'Guide confirmé', 'statut: guide_technique_actuel_verifie'), 'Guide confirmé')

    def test_gt_inaptitude_does_not_invent_third_activity(self):
        answer = 'Saisissez DI sur la 3e épreuve.'
        q = 'Bac GT 2026 : inaptitude partielle temporaire, préserver les évaluations possibles ?'
        self.assertIn('ne précise pas', prevent_invented_gt_medical_sequence(q, answer, 'MENE2531948N'))
        self.assertEqual(prevent_invented_gt_medical_sequence(q + ' troisième épreuve empêchée', answer, 'MENE2531948N'), answer)
        self.assertEqual(prevent_invented_gt_medical_sequence('CAP inaptitude temporaire', answer, 'MENE2531948N'), answer)


class VideoPlaceholderTests(unittest.TestCase):
    def test_lien_video_sans_adresse_est_nettoye(self):
        from response_controls import clean_video_placeholders
        texte = "📺 Tutoriel associé : [Saisie_protocoles_iPackEPS.mp4](lien à insérer si disponible)."
        self.assertEqual(clean_video_placeholders(texte), "📺 Tutoriel associé : Saisie_protocoles_iPackEPS.mp4.")

    def test_vrai_lien_conserve(self):
        from response_controls import clean_video_placeholders
        texte = "Voir [la vidéo](https://youtu.be/Bq7_ooQuZtU)."
        self.assertEqual(clean_video_placeholders(texte), texte)
