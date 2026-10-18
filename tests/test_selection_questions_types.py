"""Questions types publiques (aucune question privée du journal) : fiche principale attendue et fiches interdites.

Règles communes Claude / GPT (journal du 18 octobre 2026) : dans l'onglet iPackEPS, une question d'opération
logicielle reçoit une fiche de procédure, pas une synthèse de règles d'examen ; un motif ne se déclenche pas
sur un mot seul ; pas de fiche d'un autre diplôme."""
import unittest

import knowledge_catalog as kc

COL, GT, PRO = 'Collège (DNB)', 'Lycée Général & Techno', 'Lycée Pro / CAP'

# (question, public, onglet, début du titre attendu, débuts de titres interdits)
CAS = [
    ('comment importer mes élèves', COL, 'ipack', 'iPackEPS : classes', []),
    ('comment créer un groupe', COL, 'ipack', 'iPackEPS : créer un groupe', []),
    ('je ne vois pas mes élèves pour faire mon groupe', COL, 'ipack', 'iPackEPS : créer un groupe', []),
    ("comment faire l'emploi du temps", COL, 'ipack', 'iPackEPS : équipements sportifs et créneaux', []),
    ('comment associer ma classe au gymnase', COL, 'ipack', 'iPackEPS : équipements sportifs et créneaux', []),
    ('comment valider les protocoles', COL, 'ipack', None, ['DNB : LSU, Cyclades', 'DNB EPS : compétences']),
    ("où saisir les protocoles d'évaluation CAP et bac", PRO, 'ipack', 'iPackEPS lycée : Dossier Certificatif',
     ['cap session 2026', 'bac pro session 2026']),
    ('j\'ai un message moins de 3 APSA certificatives', PRO, 'ipack', 'iPackEPS lycée : réponses du référent', []),
    ("où saisir les protocoles d'évaluation", GT, 'ipack', 'iPackEPS lycée : Dossier Certificatif', []),
    ('le co-évaluateur est-il obligatoire ?', PRO, 'ipack', None, []),
    ('comment ajouter un collègue TZR', COL, 'ipack', 'iPackEPS : équipe EPS', []),
    # Fiche d'accès découpée (18 octobre) : une question ne reçoit que sa situation.
    ("je n'ai pas accès au dossier certificatif", GT, 'ipack', 'iPackEPS : Ma Fiche Professeur', ['Accès iPackEPS et portail ESTEREL']),
    ("iPackEPS n'apparaît pas dans mon portail", COL, 'ipack', 'Accès iPackEPS et portail ESTEREL', []),
    ("erreur 403 quand j'ouvre ipack", COL, 'ipack', 'Accès iPackEPS et portail ESTEREL', ['DNB : calcul']),
    ("j'ai un message instance en rouge", COL, 'ipack', "iPackEPS : message d'erreur « Instance »", ['Accès iPackEPS et portail ESTEREL']),
    ('cité scolaire : il manque des collègues au collège', COL, 'ipack', 'iPackEPS : cité scolaire', ['Accès iPackEPS et portail ESTEREL']),
    # Fiches officielles devenues prioritaires (questions sans fiche du journal, 18 octobre).
    ("une seconde prépa n'existe pas dans la liste des types de classes", GT, 'ipack', '[SITUATION: SECONDE PRÉPA', []),
    ("je suis sur deux établissements, comment passer de l'un à l'autre", COL, 'ipack', '[SITUATION: ENSEIGNANTS TZR OU PARTAGÉS', []),
    ('registre du matériel escalade, que signifient les alertes rouges', COL, 'ipack', '[ARTICLE 26]', []),
    ('où renseigner les installations sportives', COL, 'ipack', '[ARTICLE 19]', ['Accès iPackEPS et portail ESTEREL']),
    ("message : le groupe n'autorise pas le cycle scolaire", COL, 'ipack', '[ARTICLE 18]', []),
    ("à qui m'adresser pour un bug iPackEPS", GT, 'ipack', 'iPackEPS : qui contacter pour quoi', []),
    ('on a transmis nos protocoles, je veux changer une APSA', GT, 'ipack', "Remplacer une activité d'un protocole", []),
    ('où déposer les fiches certificatives d’activité (FCA) ?', GT, 'ipack', 'iPackEPS lycée : Dossier Certificatif', []),
]


class QuestionsTypes(unittest.TestCase):
    def test_fiche_principale_et_fiches_interdites(self):
        for q, public, mode, attendu, interdits in CAS:
            with self.subTest(q=q, public=public):
                titres = kc.priority_titles(q, public, mode)
                if attendu:
                    self.assertTrue(any(t.startswith(attendu) for t in titres), (attendu, titres))
                for i in interdits:
                    self.assertFalse(any(t.startswith(i) for t in titres), (i, titres))


if __name__ == '__main__':
    unittest.main()
