"""Questions réellement bloquées lors du retest, sans appel au modèle."""
import unittest
import knowledge_catalog as kc


class Retest25CatalogTests(unittest.TestCase):
    def answer(self, question, level, mode='ipack'):
        level, mode = kc.effective_context(question, level, mode)
        return kc.documented_response(question, level, mode)[0]

    def test_protocol_deadline_does_not_recycle_previous_session(self):
        answer = self.answer("Jusqu'à quand peut-on saisir les protocoles dans iPackEPS cette année à Aix-Marseille, et que se passe-t-il s'ils ne sont pas validés ?", 'Lycée Général & Techno')
        self.assertIn('Pour 2027', answer)
        self.assertIn('non validé', answer)
        self.assertIn("ce n'est ni une date limite", answer)

    def test_version_and_update_do_not_route_to_student_change(self):
        for question in ["Quelle version minimale d'iPackEPS faut-il pour l'interfaçage avec Cyclades et Santorin ?", "Comment mettre à jour iPackEPS vers la nouvelle version sans perdre mes données ?"]:
            answer = self.answer(question, 'Lycée Pro / CAP')
            self.assertIn('application en ligne', answer)
            self.assertIn('ESTEREL', answer)
            self.assertNotIn('changement de classe', answer)

    def test_third_year_replacement_overrides_pro_level_and_cites_2027(self):
        answer = self.answer("Un élève de 3e ne s'est pas présenté à l'évaluation de remplacement, sans justificatif. Quelle note ?", 'Lycée Pro / CAP', 'examens')
        self.assertIn('MENE2623194N', answer)
        self.assertIn('zéro', answer)
        self.assertIn('à nouveau convoqué', answer)
        self.assertIn('abroge', answer)
