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
        # L'inspection ne dit pas « je suis IPR » : elle répond à un lycée, à un prof, valide le dossier d'un autre.
        cas = {
            "comment répondre à un lycée ?": 'certif',
            "comment répondre à un prof ?": 'certif',
            "comment je réponds à un prof qui a mis un commentaire sur son référentiel": 'certif',
            "quelle réponse au lycée sur son référentiel": 'certif',
            "comment répondre à l'équipe EPS d'un lycée sur son dossier certificatif": 'certif',
            "comment valider le référentiel du lycée ?": 'certif',
            "je veux refuser le référentiel de badminton d'un lycée": 'certif',
            "comment demander des ajustements à un lycée sur son référentiel ?": 'certif',
            "un lycée m'a écrit dans le dossier certificatif, où je lis son message ?": 'certif',
            "où sont les référentiels à lire ?": 'certif',
            "comment mettre un avis sur le référentiel": 'certif',
            "je suis IA-IPR, comment valider un référentiel à réajuster ?": 'certif',
            "comment valider le projet SSS d'un collège ?": 'sss',
            "comment répondre à un collège sur sa demande d'ouverture de section sportive ?": 'sss',
            "comment débloquer le bilan SSS d'un établissement": 'sss',
            "un établissement ne peut pas créer de groupe SSS": 'sss',
            "comment valider la sortie APPN d'un collège ?": 'appn',
            "comment répondre à un prof sur sa demande APPN ?": 'appn',
            "comment refuser la demande APPN du lycée ?": 'appn',
            "où sont les dossiers attendus ?": 'menus',
            "comment créer les sous-commissions ?": 'menus',
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
            "comment répondre à la commission qui a mis un commentaire ?",
            "je réponds comment à la commission ?",
            "la commission a demandé des ajustements sur notre référentiel",
            "comment déposer le référentiel de l'établissement ?",
            "comment valider les protocoles de mes élèves ?",
            "comment ajouter un collègue dans l'équipe EPS ?",
            "un prof est absent le jour du CCF, que faire ?",
            "comment valider le dossier EPS ?",
            "le chef d'établissement doit-il signer le dossier SSS ?",
            "comment saisir les notes du CCF ?",
            "où déposer les référentiels d'évaluation ?",
        ):
            with self.subTest(question=question):
                self.assertEqual(fiches(question), set())


if __name__ == '__main__':
    unittest.main()
