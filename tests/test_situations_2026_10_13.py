"""Fiches de situation du 13 octobre 2026 : absence en CAP, bac pro avec deux notes, établissement hors SIECLE."""
import unittest
from pathlib import Path

import knowledge_catalog as kc

PRO = 'Lycée Pro / CAP'
GT = 'Lycée Général & Techno'
CAP_ABS = 'CAP : absence sans justification à une ou à toutes les situations de CCF'
PRO_2N = 'Bac professionnel : inapte sur une épreuve, deux notes sur trois'
PRO_1N = 'Bac professionnel : inaptitude et une seule évaluation'
HORS = 'Établissement hors SIECLE (CFA, GRETA, MFR, AEFE) : associer les candidats dans Cyclades'


def titres(q, public=PRO):
    return kc.priority_titles(q, public, 'examens')


class SituationsTests(unittest.TestCase):
    def test_cap_absence_a_toutes_les_situations(self):
        self.assertIn(CAP_ABS, titres("En CAP, un apprenti ne s'est présenté à aucune situation de CCF et n'a pas de justificatif."))
        self.assertIn(CAP_ABS, titres("CAP : il a séché une des deux épreuves, quelle note ?"))
        texte = Path('data/examens/situations_2026_10_13/cap_absence_injustifiee.txt').read_text(encoding='utf-8')
        self.assertIn('non-délivrance du diplôme', texte)
        self.assertIn("Ce n'est pas une moyenne de zéros", texte)

    def test_absence_enseignant_cap_ne_declenche_pas_la_fiche(self):
        self.assertNotIn(CAP_ABS, titres("En CAP, le professeur est absent le jour du CCF : qui évalue ?"))

    def test_bac_pro_deux_notes_et_inaptitude(self):
        q = "Bac pro : blessé avant la troisième épreuve, il a déjà deux notes. Quelle note finale ?"
        self.assertIn(PRO_2N, titres(q))
        self.assertNotIn(PRO_1N, titres(q))
        self.assertIn('moyenne des deux notes',
                      Path('data/examens/situations_2026_10_13/bac_pro_deux_notes_inaptitude.txt').read_text(encoding='utf-8'))

    def test_bac_pro_note_unique_garde_sa_fiche(self):
        q = "Mon élève de bac pro n'a eu qu'une seule note dans l'année à cause d'une inaptitude, que faire ?"
        self.assertIn(PRO_1N, titres(q))
        self.assertNotIn(PRO_2N, titres(q))

    def test_deux_notes_bac_gt_hors_fiche_bac_pro(self):
        self.assertNotIn(PRO_2N, titres("Bac GT : inapte au troisième CCF, il a deux notes. Comment calculer ?", GT))

    def test_hors_siecle(self):
        self.assertIn(HORS, titres("Nous sommes un CFA, aucun apprenti n'apparaît dans iPackEPS : comment les mettre dans les protocoles ?"))
        self.assertIn(HORS, titres("Lycée agricole : pas d'élèves à importer dans iPackEPS pour Cyclades."))
        texte = Path('data/examens/situations_2026_10_13/hors_siecle_association_cyclades.txt').read_text(encoding='utf-8')
        self.assertIn('[Associer les élèves à un protocole]', texte)

    def test_bac_gt_arret_avec_deux_notes(self):
        gt = 'Bac GT CCF : inaptitude, adaptation puis calcul conditionnel'
        self.assertIn(gt, titres("Son arrêt couvre la date du dernier CCF ; il a ses deux autres notes.", GT))
        self.assertNotIn(gt, titres("Le collègue est en arrêt maladie, qui saisit les deux notes manquantes ?", GT))
        # La saisie DI+DI+14 garde sa fiche (d3), non évincée par la fiche générale.
        q = "Inapte sur deux épreuves, mon élève n'a qu'une note (14). Je saisis quoi : DI+DI+14 ou DI partout ?"
        self.assertIn('FAQ EPS — Inaptitude / DI+DI+Note', titres(q, GT))

    def test_absent_au_ccf_saisie_santorin(self):
        k5 = 'FAQ EPS — Saisie / codes'
        self.assertIn(k5, titres("Un candidat est absent lors d'un CCF. Comment le noter sur Santorin ?", GT))
        self.assertNotIn(k5, titres("Le collègue est absent le jour du CCF, qui saisit les notes ?", GT))
        self.assertNotIn(k5, titres("Élève arrivé en cours d'année absent de Santorin", GT))

    def test_groupes_eps_non_importes_ipack(self):
        t = 'iPackEPS : élèves importés mais pas les groupes EPS'
        q = "La synchronisation avec BEE a importé les élèves mais pas les groupes d'EPS. Dois-je faire une manipulation ?"
        self.assertIn(t, kc.priority_titles(q, GT, 'examens'))
        self.assertIn(t, kc.priority_titles(q, GT, 'ipack'))
        self.assertNotIn(t, titres("Cyclades affiche après l'import : le groupe élève importé ne correspond à aucun groupe lié aux protocoles", GT))


if __name__ == '__main__':
    unittest.main()
