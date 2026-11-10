"""Le hub ne produit ni fiche didactique ni contenu de séance (demande du 10 novembre 2026)."""
import ast
import re
import unicodedata
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'app.py'


def _charger():
    tree = ast.parse(SRC.read_text(encoding='utf-8'))
    ns = {'re': re, 'unicodedata': unicodedata}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in ('contient', 'normaliser', 'demande_contenu_didactique'):
            exec(compile(ast.Module([n], []), 'app.py', 'exec'), ns)
    return ns


NS = _charger()


def refuse(q):
    return bool(NS['demande_contenu_didactique'](NS['normaliser'](q)))


class RefusContenuDidactique(unittest.TestCase):
    def test_demandes_refusees(self):
        for q in ("quel contenu en acrosport sur le site ?", "Fais-moi un cycle de badminton en 5e",
                  "propose moi une séance d'échauffement", "quels exercices pour le demi-fond ?",
                  "fiche didactique escalade"):
            self.assertTrue(refuse(q), q)

    def test_cadre_securite_examens_et_ipack_restent_traites(self):
        for q in ("un élève se blesse pendant la séance, qui est responsable ?",
                  "l'acrosport est dans quel champ d'apprentissage ?", "comment créer mes groupes sss",
                  "quel est le contenu de la fiche établissement ?", "Escalade EPI",
                  "quels exercices pour l'épreuve de bac en natation ?"):
            self.assertFalse(refuse(q), q)

    def test_message_et_consigne(self):
        src = SRC.read_text(encoding='utf-8')
        self.assertIn("Je ne suis pas autorisé à produire des fiches didactiques ou des contenus de séance", src)
        self.assertNotIn("Réponds EN TANT QU'EXPERT PÉDAGOGIQUE", src)
        self.assertIn('or est_mauvais_onglet or demande_contenu_didactique_q', src)
