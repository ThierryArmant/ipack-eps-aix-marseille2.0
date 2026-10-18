import unittest
from knowledge_catalog import clarification
from documentary_review import situation_mismatch, dnb_document_mismatch


class TeachingRegistrationIntentTests(unittest.TestCase):
    def test_underspecified_requests_clarify_before_selecting_a_procedure(self):
        for q in ("J'enseigne le foot à mes 6eme4, comment renseigner ça ?",
                  "J’enseigne le badminton à mes 5e2, où le saisir ?",
                  "Je fais de la natation avec mes élèves, comment déclarer ça ?"):
            with self.subTest(q=q):
                result = clarification(q, 'Collège (DNB)', mode='ipack')
                self.assertIn('préciser ce que vous souhaitez renseigner', result)
                self.assertNotIn('certificative', result)
                self.assertNotIn('créer', result)

    def test_legacy_two_argument_call_keeps_the_clarification(self):
        self.assertIn('préciser ce que vous souhaitez renseigner', clarification("J'enseigne le foot à mes 6eme4, comment renseigner ça ?", 'Collège (DNB)'))

    def test_explicit_target_is_not_blocked(self):
        for q in ("J'enseigne le foot à mes 6e4 : comment créer la séquence d'apprentissage ?",
                  "J'enseigne le foot : où renseigner ma spécialité dans ma fiche professeur ?",
                  "Où déclarer le football dans la liste des APSA ?"):
            self.assertEqual(clarification(q, 'Collège (DNB)', mode='ipack'), '')

    def test_teaching_case_cannot_be_justified_by_personal_specialty(self):
        q = "J'enseigne le foot à mes 6eme4, comment renseigner ça ?"
        for text in ('Renseigner sa fiche professeur',
                     'Créer une APSA pour la liste des spécialités sportives.',
                     'Ne pas la déclarer certificative puisqu’elle ne sera pas enseignée : elle apparaît dans la fiche Prof.'):
            self.assertTrue(situation_mismatch(q, text))
        self.assertFalse(situation_mismatch(q, 'Configuration des séquences d’apprentissage du groupe.'))

    def test_real_specialty_request_remains_possible(self):
        self.assertFalse(situation_mismatch("J’enseigne une activité rare : comment renseigner ma spécialité dans ma fiche professeur ?",
                                           'Créer une APSA pour la liste des spécialités sportives.'))

    def test_technical_clarification_does_not_apply_in_textes(self):
        self.assertEqual(clarification("J'enseigne le foot à mes 6e4, comment renseigner ça ?", 'Collège (DNB)', mode='textes'), '')


class CollegeRoutingTests(unittest.TestCase):
    def test_new_wording_with_my_class_also_clarifies(self):
        q = 'je nesais pas comment remplir ipack pour declarer l actiivte foot avec ma classe'
        self.assertEqual(clarification(q, 'Collège (DNB)'),
                         'Pouvez-vous préciser ce que vous souhaitez renseigner dans iPackEPS ?')

    def test_exam_protocol_document_without_scope_is_rejected_for_college(self):
        packet = {'path': 'data/ipack/fiches/ipack_069_article_42_dossiers_dossier_certificatif_protocoles_configuration.txt',
                  'title': 'Configuration des Protocoles des Épreuves certificatives',
                  'text': 'Les protocoles CAP et Bac GT nécessitent une date de rattrapage.', 'origin': 'document'}
        self.assertTrue(dnb_document_mismatch('Comment déclarer une activité ?', 'Collège (DNB)', packet))
        self.assertFalse(dnb_document_mismatch('Comment déclarer une activité ?', 'Lycée Général & Techno', packet))

    def test_dnb_evaluation_document_remains_available(self):
        packet = {'path': 'data/ipack/fiches/evaluation_dnb.txt', 'title': 'Évaluation DNB au collège',
                  'text': 'Protocole d’évaluation du collège.', 'origin': 'document'}
        self.assertFalse(dnb_document_mismatch('Comment évaluer mes élèves ?', 'Collège (DNB)', packet))
