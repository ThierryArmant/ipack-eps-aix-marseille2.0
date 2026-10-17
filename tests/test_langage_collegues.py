"""Langage courant des collègues (config/langage_collegues.json) : sélection des fiches de situation."""
import json
import re
import unittest
from pathlib import Path

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
PRO = 'Lycée Pro / CAP'


def titres(q, public=GT):
    return kc.priority_titles(q, public, 'examens')


class LangageCollegues(unittest.TestCase):
    def test_motifs_compilent(self):
        for e in json.loads(Path('config/langage_collegues.json').read_text(encoding='utf-8'))['equivalences']:
            re.compile(e['motif'])

    def test_rien_n_est_remplace(self):
        q = "Il a séché le CCF"
        self.assertTrue(kc.enrich(q).startswith(kc.normalise(q)))

    def test_formulations_familieres(self):
        cas = [
            ("Un élève a séché le CCF de badminton, je mets quoi sur Santorin ?", GT, 'FAQ EPS — Saisie / codes'),
            ("Mon lot est bloqué, je peux plus modifier une note", GT, 'FAQ EPS — Verrouillage'),
            ("Mon binôme est malade le jour du CCF, je note seul ?", GT, "FAQ EPS — Absence d'enseignant : co-évaluateur absent le jour du CCF (bac GT)"),
            ("Il a copié sur le carton de son copain en course d'orientation", GT, 'Fraude en EPS : examen et cours ordinaire'),
            ("La piscine est fermée pour travaux, on ne peut pas faire la natation au bac", GT, 'Installation fermée pour une classe : autorisation puis CE'),
            ("CAP : l'apprenti est jamais venu aux CCF", PRO, 'CAP : absence sans justification à une ou à toutes les situations de CCF'),
            ("En bac pro, blessé pour la 3e épreuve, je fais la moyenne des deux ?", PRO, 'Bac professionnel : inapte sur une épreuve, deux notes sur trois'),
        ]
        for q, public, attendu in cas:
            self.assertIn(attendu, titres(q, public), q)

    def test_pas_de_faux_ami(self):
        # Un collègue parti (convocation) n'est pas un professeur absent ; « absent des lots » n'est pas le code Absent.
        self.assertNotIn('FAQ EPS — Saisie / codes', titres("Je n'ai aucun lot dans Santorin"))
        self.assertNotIn('Accès iPackEPS et portail ESTEREL', titres("Le gymnase est indisponible, on ne pourra pas faire la troisième activité"))



class VerificationSynonymesTests(unittest.TestCase):
    def test_synonymes_stricts_acceptes_par_le_controle(self):
        from documentary_review import lexical_support
        src = ["La circulaire interdit aux enseignants d'exiger l'achat d'un matériel d'une marque donnée."]
        self.assertTrue(lexical_support("Le professeur ne peut pas imposer aux familles d'acheter une marque.", src))

    def test_preuve_sans_rapport_toujours_rejetee(self):
        from documentary_review import lexical_support
        self.assertFalse(lexical_support("Le professeur doit noter la fraude au CCF.",
                                         ["Le modèle de procès-verbal est signé par le chef d'établissement."]))

if __name__ == '__main__':
    unittest.main()
