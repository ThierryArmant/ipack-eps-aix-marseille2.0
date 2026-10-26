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


class DesaccordEntreCollegues(unittest.TestCase):
    def test_verdict_et_routage(self):
        src = open('app.py', encoding='utf-8').read()
        self.assertIn('Les deux propositions sont compatibles', src)
        self.assertIn('« CC5 » mis pour CA5', src)
        import json, re, knowledge_catalog as kc
        md = json.load(open('config/catalogue_documents.json', encoding='utf-8'))['data/examens/situations_2026_10_25/protocole_refuse_par_la_commission.txt']
        q = kc.normalise("Mr Chat a crée un protocole en javelot, mais mr Vache refuse car il veut ajouter la durée pour la CC5")
        self.assertTrue(any(re.search(m, q) for m in md['exclure_motifs']))
        self.assertFalse(any(re.search(m, kc.normalise("La commission a refusé notre protocole")) for m in md['exclure_motifs']))
