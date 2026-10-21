"""Ne pas demander une précision déjà disponible ni détourner une procédure."""
import unittest
from knowledge_catalog import clarification

class RedundantClarifications(unittest.TestCase):
    def test_known_administrative_object_is_not_unspecified_teaching(self):
        for q in ['Comment saisir l’attestation de savoir-nager de mes élèves ?', 'Où déclarer ma classe sport-études et son projet ?', 'Les modules sont colorés : faut-il tout renseigner ?']:
            with self.subTest(q=q):self.assertEqual(clarification(q,'Collège (DNB)',mode='ipack'),'')
        self.assertTrue(clarification('J’enseigne le badminton avec mes élèves, comment renseigner ça ?', 'Collège (DNB)',mode='ipack'))
    def test_document_and_substitution_steps_do_not_choose_a_grade(self):
        for q in ['Où déposer le certificat médical de l’élève déjà dispensé ?', 'Comment saisir une inaptitude partielle dans iPackEPS ?', 'Comment saisir une épreuve de substitution pour une inaptitude temporaire ?']:
            with self.subTest(q=q):self.assertEqual(clarification(q,'Lycée Général & Techno',mode='ipack'),'')
        self.assertTrue(clarification('Il est dispensé, je saisis DI ou zéro ?', 'Lycée Général & Techno',mode='examens'))
        self.assertTrue(clarification('Comment saisir une inaptitude, quel statut choisir ?', 'Lycée Général & Techno',mode='examens'))
    def test_vocabulary_and_order_have_no_unrelated_medical_or_screen_question(self):
        self.assertEqual(clarification('Santorin : Absent ou Dispensé, quelle différence dans le calcul ?', 'Lycée Général & Techno',mode='examens'),'')
        self.assertEqual(clarification('Santorin : si je coche Absent, ça donne zéro ou ça neutralise comme Dispensé ?', 'Lycée Pro / CAP',mode='examens'),'')
        self.assertEqual(clarification('Informations manquantes : dans quel ordre remplir les tuiles ?', 'Lycée Général & Techno',mode='ipack'),'')
        self.assertTrue(clarification('Informations manquantes : que faire ?', 'Lycée Général & Techno',mode='ipack'))

    def test_administrative_wording_does_not_hide_individual_value_choice(self):
        for q in [
            'Comment saisir une inaptitude dans Santorin : je mets Absent ou Dispensé ?',
            'Comment saisir une inaptitude, quelle valeur mettre ?',
        ]:
            with self.subTest(q=q):
                self.assertIn('CAP ou baccalauréat professionnel', clarification(q, 'Lycée Pro / CAP', mode='examens'))
        self.assertTrue(clarification(
            'Comment saisir une inaptitude dans Santorin : je mets Absent ou Dispensé ?',
            'Lycée Général & Techno', mode='examens'))
        for q in [
            'Comment saisir une inaptitude dans Santorin ?',
            'Où déposer le certificat médical de l’élève déjà dispensé ?',
            'Santorin : Absent ou Dispensé, quelle différence dans le calcul ?',
            'Quels libellés Santorin correspondent aux cas Absent et Dispensé ?',
        ]:
            with self.subTest(q=q):
                self.assertEqual(clarification(q, 'Lycée Pro / CAP', mode='examens'), '')
