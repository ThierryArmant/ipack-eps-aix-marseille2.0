"""Questions réelles relevées dans le journal du 13 au 17 octobre 2026 (autres académies comprises)."""
import unittest
from pathlib import Path

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
CLG = 'Collège (DNB)'
AJOUT = "iPackEPS : élève absent de la liste, comment l'ajouter"
PRONOTE = '[ARTICLE 88] [Dossiers]/[DossierEPS]/[Élèves] Import d’élèves depuis Pronote / École-Directe'
PONCTUEL = 'Bac GT ponctuel : publics et conditions de neutralisation'
EQUIPE = 'iPackEPS : actualisation de l’équipe EPS'


def titres(q, public=GT, mode='ipack'):
    return kc.priority_titles(q, public, mode)


class QuestionsReellesTests(unittest.TestCase):
    def test_ajout_manuel_d_un_eleve(self):
        self.assertIn(AJOUT, titres("ajouter un eleve manuellement"))
        self.assertIn(AJOUT, titres("Un nouvel élève n'apparaît pas dans ma classe, comment le rajouter ?", CLG))
        self.assertNotIn(AJOUT, titres("Élève arrivé en cours d'année absent de Santorin", GT, 'examens'))
        texte = Path('data/ipack/situations_2026_10_17/eleve_absent_liste_ajout.txt').read_text(encoding='utf-8')
        self.assertIn('[importation élèves] > [Actualiser]', texte)
        self.assertIn('ne décrivent pas de formulaire', texte)

    def test_import_pronote_sans_fiches_de_notes(self):
        t = titres("importer des eleves pronote")
        self.assertIn(PRONOTE, t)
        self.assertFalse(any('notes, moyennes' in x or 'PÉRIMÈTRE' in x for x in t), t)
        # Une question sur les notes garde la fiche de périmètre.
        self.assertIn('iPackEPS : notes, moyennes, résultats et sens des transferts',
                      titres("exporter mes notes ipack vers pronote"))

    def test_ponctuel_candidat_individuel_sans_fiche_ccf(self):
        t = titres("Un candidat individuel choisit-il librement trois activités pour son épreuve ponctuelle ?", GT, 'examens')
        self.assertIn(PONCTUEL, t)
        self.assertNotIn('Bac GT : CCF, activité établissement et harmonisation', t)

    def test_collegue_absent_de_l_equipe(self):
        self.assertIn(EQUIPE, titres("Un collègue n'apparaît pas dans la liste de l'équipe EPS"))

    def test_marque_de_tenue_formulation_des_collegues_acceptee(self):
        from documentary_review import mark_excerpt, source_packets, lexical_support_details
        p = 'data/textes/fiches/fournitures_neutralite_commerciale.txt'
        packet = source_packets(mark_excerpt(Path(p).read_text(encoding='utf-8'), path=p, title='t', priority=330))[0]
        for t in ("Le professeur ne peut pas demander aux familles d'acheter une tenue d'EPS d'une marque précise.",
                  "Non, le professeur ne peut pas imposer une marque de tenue aux familles."):
            self.assertTrue(any(lexical_support_details(t, [s['text']])['passed'] for s in packet['passages']), t)


if __name__ == '__main__':
    unittest.main()
