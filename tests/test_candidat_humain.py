import unittest
from candidat_humain import animal_candidat, precision_animal


class CandidatHumain(unittest.TestCase):
    def test_animaux_detectes(self):
        self.assertEqual(animal_candidat("si mon chat a fait javelot, peut il faire demi fond avec mon canari"), 'chat')
        self.assertIn('un chat et un canari', precision_animal("si mon chat a fait javelot, peut il faire demi fond avec mon canari"))

    def test_precision_avant_toute_regle(self):
        from question_preflight import prepare_question
        o = prepare_question("si mon chat a fait javelot, peut il faire demi fond avec mon canari sachant que j ai rentre triple saut dans le protocole",
                             'Lycée Général & Techno', 'examens')
        self.assertIn('Parlez-vous d’élèves', o['precision'])

    def test_pas_de_faux_positif(self):
        for q in ["Le chat de l'ENT ne marche plus", "Jeu du chat perché en maternelle", "Mon élève a une entorse",
                  "Comment ouvrir le tchat de l'assistance ?", "jouer au chat et à la souris en échauffement"]:
            self.assertEqual(animal_candidat(q), '', q)
