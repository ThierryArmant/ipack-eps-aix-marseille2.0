import unittest
from knowledge_catalog import clarification
from documentary_review import source_packets, mark_excerpt, situation_mismatch


class VerifierContextTests(unittest.TestCase):
    def test_unspecified_verifier_asks_for_screen_instead_of_choosing_courses(self):
        q = "Le vérificateur me dit que je n’ai pas assez d’APSA certificatives alors que j’en ai mis plus que 3. Comment faire ?"
        result = clarification(q, 'Lycée Général & Techno')
        self.assertIn('écran', result)
        self.assertIn('message exact', result)
        self.assertNotIn('Courses', result)

    def test_explicit_protocol_is_not_blocked_by_clarification(self):
        self.assertEqual(clarification('Dans iPack mon protocole a un nombre insuffisant d’APSA certificatives.', 'Lycée Général & Techno'), '')

    def test_course_remapping_requires_matching_context(self):
        procedure = 'Sélectionnez l’APSA Courses et déclarez-la certificative.'
        self.assertTrue(situation_mismatch('Je manque d’APSA certificatives, pourquoi ?', procedure))
        self.assertFalse(situation_mismatch('Comment remplacer mon relais-vitesse par Courses ?', procedure))

    def test_faq_substeps_keep_the_original_specific_question(self):
        body = '- Q1 : J’ai créé une musculation adaptée et la coche est grisée.\n- R1 : Distinguer deux points.\n  - Référentiels : cas adapté.\n  - Coche grisée : cette APSA ne peut pas être certificative.\n- Q2 : Autre problème.\n- R2 : Autre réponse.'
        packets = source_packets(mark_excerpt(body, path='data/ipack/fiches/ipack_061_article_15_dossiers_dossiereps_apsas_declaration_des_apsas.txt'))
        relevant = [p['text'] for p in packets[0]['passages'] if 'cette APSA ne peut' in p['text']]
        self.assertEqual(len(relevant), 1)
        self.assertIn('Q1', relevant[0])
        self.assertNotIn('Q2', relevant[0])
