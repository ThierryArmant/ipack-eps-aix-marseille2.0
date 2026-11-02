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


class ZonesDOmbre(unittest.TestCase):
    CAS = [("Le gymnase a une fuite au plafond et le sol est glissant, puis-je refuser de faire cours ?", 'Tous publics', "Droit de retrait"),
           ("Mon coordo veut m'imposer sa progression en badminton, il a le droit ?", 'Lycée Général & Techno', "Liberté pédagogique"),
           ("Un enseignant peut-il critiquer sa direction sur Facebook ?", 'Tous publics', "Expression publique"),
           ("Combien de jours d'autorisation d'absence pour garder mon enfant malade ?", 'Tous publics', "Autorisations d'absence"),
           ("Un élève est-il obligé de venir à l'AS ?", 'Collège (DNB)', "Association sportive : participation")]

    def test_aiguillage(self):
        for q, public, attendu in self.CAS:
            with self.subTest(q=q):
                self.assertIn(attendu, ' | '.join(kc.priority_titles(q, public, 'textes')))

    def test_pas_de_faux_positifs(self):
        for q in ("Bonjour Enseignante au LP X à X, question sur Santorin",
                  "Mon élève a été absent au deuxième CCF pour un enterrement familial",
                  "Bac GT : Santorin ne veut pas de ma note d’AFL2, un collègue affirme le contraire",
                  "Un élève s'est blessé lors d'un entraînement AS. Qui doit obligatoirement prévenir ?"):
            with self.subTest(q=q):
                t = ' | '.join(kc.priority_titles(q, 'Tous publics', 'textes'))
                for n in ("Droit de retrait", "Liberté pédagogique", "Expression publique", "Autorisations d'absence d'un enseignant",
                          "Association sportive : participation", "Enseignant : obligations"):
                    self.assertNotIn(n, t)
