"""Fiches côté inspection (interface IA-IPR EPS, relevé du 22/11/2026) : elles répondent aux questions
de l'inspection ou de la commission, et ne doivent pas capter les questions des professeurs."""
import unittest

from knowledge_catalog import priority_context

PUBLIC = 'Lycée Général & Techno'
TITRES = {
    'menus': 'plan des menus et dossiers attendus',
    'certif': 'Dossier Certificatif, valider les référentiels',
    'sss': 'côté inspection : Dossier Section Sportive',
    'appn': 'côté inspection : Dossier APPN',
}


def fiches(question):
    texte = priority_context(question, PUBLIC, 'ipack')
    return {k for k, v in TITRES.items() if v in texte}


class FichesInspection(unittest.TestCase):
    def test_questions_inspection(self):
        cas = {
            "en tant qu'IPR comment je réponds au commentaire d'un lycée sur son dossier certificatif ?": 'certif',
            "comment répondre à un lycée qui a déposé un commentaire dans son dossier certificatif": 'certif',
            "je suis IA-IPR, comment valider un référentiel à réajuster ?": 'certif',
            "un établissement ne peut pas créer de groupe SSS, côté inspection que faut-il cocher ?": 'sss',
            "comment valider le dossier SSS d'un établissement ?": 'sss',
            "IPR : comment valider une demande APPN ?": 'appn',
            "où sont les dossiers attendus ?": 'menus',
        }
        for question, attendu in cas.items():
            with self.subTest(question=question):
                self.assertIn(attendu, fiches(question))

    def test_questions_professeurs_non_captees(self):
        for question in (
            "comment proposer mon dossier certificatif à la commission ?",
            "mon référentiel est en attente de validation par l'inspection, que faire ?",
            "le référentiel du lycée a été validé par l'inspection mais à réajuster, que faire ?",
            "comment créer une demande APPN kayak ?",
            "l'inspection a dit que notre dossier APPN est incomplet",
            "je ne vois pas ma section sportive dans iPackEPS",
            "comment faire la demande de reconduction de notre section ?",
            "comment créer un groupe SSS ?",
            "comment remplir le bilan SSS ?",
            "comment déclarer mes groupes d'option ?",
        ):
            with self.subTest(question=question):
                self.assertEqual(fiches(question), set())


if __name__ == '__main__':
    unittest.main()
