"""Thèmes des réponses fausses de la mesure du 13 octobre : chaque situation reçoit sa fiche (formulations reformulées)."""
import unittest

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
PRO = 'Lycée Pro / CAP'


def titres(q, public=GT):
    return kc.priority_titles(q, public, 'examens')


class ThemesMesure(unittest.TestCase):
    def test_situations(self):
        cas = [
            ("Je me suis trompé de note pour un élève dans Santorin, le lot est encore ouvert : je fais Réinitialiser ?", GT, 'Santorin : corriger une note saisie, sans « Réinitialiser »'),
            ("Hier j'ai rentré toutes mes notes dans Santorin et aujourd'hui elles ont disparu", PRO, 'Santorin : notes disparues, saisie non enregistrée'),
            ("On est deux co-évaluateurs sur le lot : chacun saisit sa note et Santorin fait la moyenne ?", GT, "Co-évaluation : une seule saisie, le deuxième correcteur n'est qu'un accès au lot"),
            ("Il a 11, 14 et 15 : je rentre 13,33 comme note finale dans Santorin ?", GT, 'Santorin : saisie des points par AFL, pas de la note finale'),
            ("Élève blessé en avril : je crée son protocole adapté dans iPackEPS, il ira dans Cyclades ?", GT, "Élève blessé en cours d'année : protocole adapté créé dans Cyclades"),
            ("Notre lycée ne propose pas l'option EPS, un élève peut-il la passer en candidat ponctuel ?", GT, "Option EPS : pas d'épreuve ponctuelle pour un élève scolarisé"),
            ("Mon élève de section sportive rugby a-t-il 20 au bac ?", GT, 'Section sportive scolaire : pas de 20/20 à ce titre'),
            ("Un candidat libre ne s'est pas présenté à une de ses deux épreuves ponctuelles : il est éliminé ?", GT, 'Bac GT ponctuel : publics et conditions de neutralisation'),
        ]
        for q, public, attendu in cas:
            self.assertIn(attendu, titres(q, public), q)

    def test_faux_amis(self):
        self.assertNotIn("FAQ EPS — Santorin : clôturer le lot d'un collègue qui a oublié",
                         titres("J'ai tapé une mauvaise note (le lot n'est pas verrouillé), je clique sur Réinitialiser ?"))
        self.assertNotIn('FAQ EPS — Saisie / codes',
                         titres("Un candidat individuel absent à une épreuve ponctuelle est-il éliminé ?"))

    def test_option_ponctuel_note_unique(self):
        self.assertIn("Option EPS : pas d'abandon après clôture des inscriptions (Aix-Marseille, 2027)",
                      titres("Mon élève veut arrêter l'option EPS en février, il peut ?"))
        self.assertNotIn("Élève parti en cours d'année mais toujours inscrit à l'examen",
                         titres("Mon élève veut arrêter l'option EPS en février, il peut ?"))
        self.assertIn('Bac GT : une seule épreuve passée sur trois (note unique ou dispense)',
                      titres("Blessé, il n'a passé qu'une seule épreuve sur trois : on garde sa note ?"))
        from pathlib import Path
        self.assertIn("ne la repasse pas", Path('data/commun/audit60/gt_ponctuel_absence.txt').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
