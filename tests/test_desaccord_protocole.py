"""Un désaccord dans l'équipe ne devient pas un refus de la commission."""
import unittest

import knowledge_catalog as kc
import short_answer as sa
from question_preflight import prepare_question

REFUS = 'data/examens/situations_2026_10_25/protocole_refuse_par_la_commission.txt'
REGLES = 'data/commun/audit60/gt_regles_decisives.txt'
PUBLIC = 'Lycée Général & Techno'
QUESTION = ("Mr Chat a créé un protocole en javelot, mais mr Vache refuse car il veut ajouter "
            "la durée pour la CC5, les 2 conditions sont elles viables pour valider le protocole ?")
SOURCE = "Un protocole refusé doit être corrigé selon les remarques de la commission académique."


def paths(question):
    return [p for p, _ in kc.reference_notice({'gt'}, question, PUBLIC)]


class DesaccordProtocole(unittest.TestCase):
    def test_reponse_collegues_cherche_champs_sans_refus_officiel(self):
        self.assertNotIn(REFUS, paths(QUESTION))
        self.assertIn(REGLES, paths(QUESTION))
        self.assertNotEqual(prepare_question(QUESTION, PUBLIC, 'examens')['kind'], 'clarification')

    def test_refus_explicite_commission_reste_trouve(self):
        for q in ("Mon protocole a été refusé par la commission académique, que faire ?",
                  "La commission a refusé mon protocole, que faire ?",
                  "La CAHPN a rejeté mon protocole EPS, que faire ?"):
            with self.subTest(question=q):
                self.assertIn(REFUS, paths(q))

    def test_auteur_absent_ne_devient_pas_automatiquement_commission(self):
        self.assertNotIn(REFUS, paths("Mon protocole EPS est refusé, que faire ?"))
        self.assertNotIn(REFUS, paths("Une collègue refuse notre protocole, que faire ?"))
        self.assertNotIn(REFUS, paths("Mon collègue refuse le protocole ; la commission doit-elle le valider ?"))
        self.assertNotIn(REFUS, paths("La commission a validé notre protocole, mais mon collègue refuse l'activité."))

    def test_refus_collegue_ne_devient_pas_decision_officielle(self):
        for q in (QUESTION, "Mon collègue refuse le protocole ; la commission doit-elle le valider ?",
                  "La commission a validé notre protocole, mais mon collègue refuse l'activité."):
            with self.subTest(question=q):
                self.assertIn('premisse:refus_commission_non_etabli', sa.unsupported(SOURCE, SOURCE, q))

    def test_refus_reel_et_conditionnel_ne_sont_pas_ecartes(self):
        q = "Mon collègue est inquiet : la commission a refusé notre protocole. Que faire ?"
        self.assertNotIn('premisse:refus_commission_non_etabli', sa.unsupported(SOURCE, SOURCE, q))
        conditional = "Si le protocole est refusé par la commission, il faut le corriger."
        self.assertNotIn('premisse:refus_commission_non_etabli', sa.unsupported(conditional, SOURCE, QUESTION))


if __name__ == '__main__':
    unittest.main()
