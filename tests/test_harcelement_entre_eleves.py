"""Questions réelles du 18/11/2026 : un élève rejeté ou harcelé par ses camarades trouve la fiche dédiée."""
import unittest
from pathlib import Path

from knowledge_catalog import reference_notice, has_text_reference

FICHE = 'data/textes/situations_2026_11_19/harcelement_entre_eleves_reconnaitre_alerter.txt'
PUBLICS = {'Collège (DNB)': {'dnb'}, 'Lycée Général & Techno': {'gt'}, 'Lycée Pro / CAP': {'pro', 'cap'}}


def trouve(question, public='Collège (DNB)'):
    return any(p == FICHE for p, _ in reference_notice(PUBLICS[public], question, public))


class HarcelementEntreEleves(unittest.TestCase):
    def test_question_reelle_acrosport(self):
        q = ("dans le cadre d'un cours sur l'accrosport en 6eme une filles est rejeté par les autres groupes "
             "qu'est ce que je dois faire ?")
        for public in PUBLICS:
            self.assertTrue(trouve(q, public), public)
        self.assertTrue(has_text_reference(q, 'Lycée Général & Techno'))

    def test_famille_de_formulations(self):
        for q in ("Personne ne veut se mettre avec lui pour faire les équipes en handball, que faire ?",
                  "On se moque d'un élève dans les vestiaires à chaque séance.",
                  "Un élève me dit qu'il est harcelé sur les réseaux par des camarades de classe.",
                  "Une élève est mise à l'écart par son groupe en danse depuis plusieurs semaines.",
                  "Que dois-je faire si je soupçonne un cyberharcèlement entre élèves ?"):
            self.assertTrue(trouve(q), q)

    def test_questions_voisines_non_concernees(self):
        for q in ("demain c jour de greve, je suis chef d etablissement, je naurai pas mes AED, "
                  "puis je mettre mes 5 classes seules devant un film ?",
                  "Mon référentiel a été rejeté par la commission, puis-je le corriger ?",
                  "Mon ensemble volley, basket et badminton est rejeté pour mes bac pro, pourquoi ?",
                  "Un parent m'insulte et me menace devant le gymnase. Que puis-je faire ?",
                  "Mon chef d'établissement me harcèle, que faire ?",
                  "Un élève isolé peut-il bénéficier d'un aménagement individuel sport-études sans classe dédiée ?"):
            self.assertFalse(trouve(q), q)

    def test_fiche_sans_consigne_au_modele(self):
        texte = Path(FICHE).read_text(encoding='utf-8')
        self.assertNotIn('Ne pas confondre', texte)
        self.assertNotIn("L'IA", texte)
        self.assertIn('ostracisme', texte)
        self.assertIn('L. 111-6', texte)


if __name__ == '__main__':
    unittest.main()
