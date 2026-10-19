import unittest
from documentary_review import coherence_errors, situation_mismatch


class ShnGuardScopeTests(unittest.TestCase):
    def claim(self, text):
        return {'section': 'condition', 'text': text}

    def test_specialty_mark_and_sufficiency_are_different_objects(self):
        statements = [self.claim("Le candidat peut obtenir le 20/20 pour sa spécialité."),
                      self.claim("Le 20/20 ne peut pas être l'unique note retenue.")]
        self.assertFalse(coherence_errors(statements, 'Comment configurer le protocole SHN ?'))

    def test_specialty_mark_and_manual_entry_are_different_operations(self):
        statements = [self.claim("Le candidat peut obtenir le 20/20 pour sa spécialité."),
                      self.claim("Il ne peut pas saisir 20/20 manuellement à la main.")]
        self.assertFalse(coherence_errors(statements, 'Comment configurer le protocole SHN ?'))

    def test_genuine_contradictions_are_still_rejected(self):
        for positive, negative in [
            ('Il peut obtenir le 20/20.', 'Il ne peut pas obtenir le 20/20.'),
            ("Le 20/20 peut être la seule note.", "Le 20/20 ne peut pas être la seule note.")]:
            self.assertTrue(coherence_errors([self.claim(positive), self.claim(negative)], 'Statut SHN ?'))

    def test_comparative_diploma_reminder_is_not_a_foreign_branch(self):
        question = 'Quels aménagements pour un sportif de haut niveau ?'
        self.assertFalse(situation_mismatch(question,
            "Rappel : l'éligibilité repose sur les catégories du bac GT ; des textes propres au bac pro et au CAP existent."))
        self.assertTrue(situation_mismatch(question, 'Au CAP, le candidat passe une seule activité.'))
        self.assertTrue(situation_mismatch(question, 'Bac pro : la moyenne résulte de deux activités.'))
