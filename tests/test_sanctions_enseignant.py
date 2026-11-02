"""Une question sur la sanction d'un enseignant ne reçoit plus la discipline des élèves."""
import unittest
import knowledge_catalog as kc

ENS = 'data/textes/situations_2026_11_02/enseignant_obligations_manquements_sanctions.txt'
ELEVES = 'data/textes/fiches/base_textes_officiels_019_situation_13e_section_code_disciplinaire_cadre_des_punitions_et_des_sanctions.txt'


def paths(q, public='Tous publics'):
    return [p for p in kc.priority_paths(q, public, 'textes')] if hasattr(kc, 'priority_paths') else None


class SanctionsEnseignant(unittest.TestCase):
    def titres(self, q, public='Tous publics'):
        return ' | '.join(kc.priority_titles(q, public, 'textes'))

    def test_enseignant_et_as(self):
        for q in ("quelles sont les sanctions prévues contre un enseignant qui refuse d’assurer son AS ?",
                  "quelles sont les sanctions possibles en cas de non-respect des 3H d’AS ?",
                  "Un collègue refuse d'appliquer le projet EPS, que risque-t-il ?"):
            with self.subTest(q=q):
                t = self.titres(q)
                self.assertIn('Enseignant : obligations', t)
                self.assertNotIn('punitions, sanctions et évaluation scolaire', t)

    def test_discipline_des_eleves_inchangee(self):
        t = self.titres("Puis-je exclure un élève de mon cours ?", 'Collège (DNB)')
        self.assertIn('punitions, sanctions et évaluation scolaire', t)
        self.assertNotIn('Enseignant : obligations', t)

    def test_fiche_sourcee(self):
        body = open(ENS, encoding='utf-8').read()
        for ref in ('L. 533-1', 'L. 121-10', 'n° 03918', 'service-public.gouv.fr', '29 juillet 1961'):
            self.assertIn(ref, body)
