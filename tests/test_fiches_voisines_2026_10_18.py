"""Fiches voisines : une fiche ciblée ne doit pas se déclencher sur un mot pris dans un autre sens (18 octobre 2026)."""
import unittest

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
CLG = 'Collège (DNB)'


def t(q, p=GT, m='examens'):
    return kc.priority_titles(q, p, m)


class FichesVoisines(unittest.TestCase):
    def test_fiche_generale_gt_decoupee(self):
        self.assertIn("Bac GT : ensemble certificatif, listes d'activités et commission académique",
                      t("Combien d'activités peut compter la liste académique ?"))
        self.assertIn('Bac GT : absence prolongée du professeur et CCF',
                      t("Notre collègue est en arrêt depuis deux mois, nos terminales n'ont pas fait le cycle de CCF, que faire ?"))
        self.assertNotIn("Bac GT : ensemble certificatif, listes d'activités et commission académique",
                         t("Un élève blessé peut faire un badminton adapté, faut-il une validation ?"))

    def test_absence_longue_n_est_pas_co_evaluation(self):
        r = t("Notre collègue est en arrêt depuis deux mois, nos terminales n'ont pas fait le cycle de CCF, que faire ?")
        self.assertFalse(any('co-évaluateur absent' in x for x in r), r)
        self.assertTrue(any('co-évaluateur absent' in x for x in t("Mon binôme est malade le jour du CCF, je peux évaluer seul ?")))
        r = t("Mon binôme est malade le jour du CCF, je peux évaluer seul ?")
        self.assertFalse(any('inaptitude' in x.lower() for x in r), r)

    def test_accident_hors_cours_n_appelle_pas_le_rapport(self):
        r = t("Mon élève a eu un accident de ski pendant les vacances, il est inapte pour le CCF")
        self.assertNotIn('Accident scolaire : rapport et communication aux parents', r)
        self.assertIn('Accident scolaire : rapport et communication aux parents',
                      t("Un élève s'est blessé pendant le cours, que dois-je faire ?", CLG, 'textes'))

    def test_mots_larges(self):
        self.assertEqual([], t("Qui encadre l'AS le mercredi après-midi ?", CLG, 'textes'))
        self.assertEqual([], t("Le transport des élèves en car pour aller à la piscine : qui paie ?", CLG, 'textes'))
        self.assertEqual([], t("Le coordonnateur EPS doit-il faire la programmation de toute l'équipe ?", CLG, 'textes'))
        self.assertFalse(any('Sorties' in x for x in t("Je pars en voyage scolaire, qui me remplace pour le CCF ?")))
        self.assertIn('Transport d’élèves en véhicule personnel : recours exceptionnel et garanties',
                      t("Puis-je emmener des élèves dans ma voiture au cross ?", CLG, 'textes'))
        self.assertTrue(any('Sorties' in x for x in t("Faut-il une autorisation des parents pour une sortie scolaire à la journée ?", CLG, 'textes')))


if __name__ == '__main__':
    unittest.main()
