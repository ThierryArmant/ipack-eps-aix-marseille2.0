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
