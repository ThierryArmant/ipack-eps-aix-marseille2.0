"""Réponses en dur du catalogue : chacune se déclenche sur son sujet et seulement sur lui.
Questions témoins issues de l'audit du 12 octobre 2026 (détournements constatés hors ligne)."""
import unittest
import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
PRO = 'Lycée Pro / CAP'
CAS = [
 # inscriptions GT (doit déclencher)
 ("Notre élève inapte apparaît APTE dans Cyclades à l'inscription. Erreur du secrétariat ?", GT, 'inscriptions terminale GT'),
 ("Session 2027 : mon candidat inapte est inscrit apte dans Cyclades, c'est normal ?", GT, 'inscriptions terminale GT'),
 # inscriptions GT (ne doit pas)
 ("Mon élève est inapte total toute l'année de terminale. Je ne le mets dans aucun groupe Cyclades, c'est bien ça ?", GT, 'FAQ EPS D1'),
 ("Élève inapte : dans quel protocole Cyclades le placer ?", GT, None),
 # candidats absents (doit)
 ("Il manque trois élèves dans la liste des candidats du bac sur Cyclades, est-ce que je dois refaire l'export depuis iPackEPS ?", GT, 'candidats absents'),
 ("Un candidat n'apparaît pas dans Cyclades alors qu'il est dans iPackEPS, que faire ?", PRO, 'candidats absents'),
 # candidats absents (ne doit pas)
 ("Quand je crée mon protocole dans Cyclades, mon APSA n'apparaît pas dans la liste.", GT, 'FAQ EPS F1'),
 ("Mon élève était absent au CCF, que dois-je mettre dans Cyclades ?", GT, None),
 ("Le référentiel de badminton n'apparaît pas dans la liste Cyclades", PRO, None),
 # protocoles 2026 (doit)
 ("Jusqu'à quand peut-on saisir les protocoles dans iPackEPS cette année à Aix-Marseille, et que se passe-t-il s'ils ne sont pas validés ?", GT, 'protocoles et circuit'),
 ("Quelle est la date limite pour déposer les protocoles ?", PRO, 'protocoles et circuit'),
 # protocoles 2026 (ne doit pas)
 ("Cyclades refuse mon protocole à cause d'une date.", GT, 'FAQ EPS F3'),
 ("Il faut ajouter un protocole standard après la validation de la commission. Je demande à la commission d'invalider nos protocoles ?", GT, None),
 ("Je veux changer la date du CCF dans mon protocole, comment faire ?", PRO, None),
 # bac pro une note (doit)
 ("Bac pro : une seule évaluation dans l'année (8/20), puis inapte jusqu'à la fin. On garde le 8 ?", PRO, 'une seule évaluation'),
 ("En bac pro, mon élève inapte n'a qu'une seule note, peut-on la garder ?", PRO, 'une seule évaluation'),
 # bac pro une note (ne doit pas)
 ("En bac pro, mon élève a deux notes et une inaptitude attestée pour le troisième CCF. Je calcule comment ?", PRO, None),
 ("En bac pro, un élève a une entorse et ne peut pas courir pendant six semaines. Peut-on adapter son épreuve au lieu de le dispenser ?", PRO, None),
 ("Faut-il installer iPackEPS sur mon ordinateur ?", GT, 'Accès iPackEPS'),
 ("Où déclarer mes installations sportives ?", GT, None),
 ("Un élève arrivé après la fermeture de l'installation n'a pas de note.", GT, None),
 ("Lycée bloqué : peut-on rattraper le CCF1 en fin d'année ?", GT, 'Blocages'),
 ("iPackEPS me bloque avec un message", GT, None),
 ("Un candidat libre peut-il passer l'option EPS en ponctuel ?", GT, 'Option EPS'),
 ("Notre lycée n'a pas l'option, peut-il la passer en ponctuel ?", GT, None),
 ("Mes élèves n'ont que deux notes à cause d'un professeur non remplacé.", GT, 'activité établissement'),
 ("Je suis chef d'établissement et l'enseignant est absent, puis-je saisir ses notes ?", GT, None),
 ("Cyclades : mon élève absent au CCF, il manque sa note dans la liste", GT, None),
 ("Je suis seul en EPS : l'enseignant est absent, comment certifier le CCF ? ensuite je saisis dans Santorin", GT, None),
 ("Qu'est-ce qui a changé dans la nouvelle version d'iPackEPS ?", GT, None),
 ("Comment mettre à jour iPackEPS vers la nouvelle version sans perdre mes données ?", PRO, 'Accès iPackEPS'),
 ("Un élève assidu a été bloqué par une grève des trains le jour du CCF. Que fait-on ?", GT, 'FAQ EPS C3'),
 ("Le lycée est bloqué par les élèves depuis lundi, le CCF de demain est-il maintenu ?", GT, 'Blocages'),
 ("Bac professionnel : blocage du lycée et CCF annulé", PRO, 'Blocages'),
 ("J'ai 2 enseignants stagiaires qui ont accès à ESTEREL mais qui ne peuvent pas se connecter à iPackEPS, comment débloquer la situation pour entrer nos protocoles ?", PRO, None),
 ("i pack EPS me bloque, comment débloquer la situation au lycée ?", GT, None),
]


def reponse_directe(question, public):
    for mode in ('examens', 'ipack'):
        niveau, m = kc.effective_context(question, public, mode)
        texte, source = kc.documented_response(question, niveau, m)
        if texte:
            return source.get('title', '')
    return ''


class RoutageReponsesDirectesTests(unittest.TestCase):
    def test_chaque_reponse_en_dur_reste_sur_son_sujet(self):
        for question, public, attendu in CAS:
            with self.subTest(question=question):
                titre = reponse_directe(question, public)
                if attendu is None:
                    self.assertEqual(titre, '', f'réponse en dur hors sujet : {titre}')
                else:
                    self.assertIn(attendu.lower(), titre.lower())


if __name__ == '__main__':
    unittest.main()
