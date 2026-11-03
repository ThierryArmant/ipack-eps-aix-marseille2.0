"""Fiche jurisprudence des accidents d'élèves : déclenchement ciblé (3 novembre 2026)."""
import unittest

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
FICHE = "Jurisprudence de référence : accident d'élève en EPS (enseignant, État, collectivité)"


def t(q, m='textes'):
    return kc.priority_titles(q, GT, m)


class JurisprudenceAccidents(unittest.TestCase):
    def test_declenche(self):
        for q in ("Un parent m'attaque au tribunal pour la blessure de son enfant en cours d'EPS. Est-ce que je paie personnellement ?",
                  "Y a-t-il de la jurisprudence sur les accidents en EPS ?",
                  "Un élève fait un malaise en course, que dois-je faire ?"):
            self.assertIn(FICHE, t(q), q)

    def test_ne_declenche_pas(self):
        for q, m in (("Que doit contenir le procès-verbal (PV) d'une épreuve de CCF EPS et qui le signe ?", 'textes'),
                     ("Le transport des élèves en car pour aller à la piscine : qui paie ?", 'textes'),
                     ("Comment transmettre les procès-verbaux de la commission d'établissement au pôle examens ?", 'textes')):
            self.assertNotIn(FICHE, t(q, m), q)

    def test_pas_de_decision_non_verifiee(self):
        texte = open('data/textes/situations_2026_11_03/jurisprudence_accidents_eleves_eps.txt', encoding='utf-8').read()
        for faux in ('Thonon', 'Bastia', 'Rouen, 2011', '11 mai 2004'):
            self.assertNotIn(faux, texte)


if __name__ == '__main__':
    unittest.main()
