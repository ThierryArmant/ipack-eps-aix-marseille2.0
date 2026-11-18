"""Préparation des concours : réponse fixe ; conditions d'accès toujours traitées (18 novembre 2026)."""
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
        if isinstance(n, ast.FunctionDef) and n.name in ('contient', 'normaliser', 'demande_preparation_concours'):
            exec(compile(ast.Module([n], []), 'app.py', 'exec'), ns)
    return ns


NS = _charger()


def refuse(q):
    return bool(NS['demande_preparation_concours'](NS['normaliser'](q)))


class RefusPreparationConcours(unittest.TestCase):
    def test_preparation_refusee(self):
        for q in ("Qu'est ce que je dois préférentiellement connaitre pour passer le capeps",
                  "Comment préparer l'oral du CAPEPS ?", "Quel est le programme de l'agrégation d'EPS ?",
                  "quels sujets tombent à l'écrit du capeps", "méthode pour réussir le concours de professeur d'EPS"):
            self.assertTrue(refuse(q), q)

    def test_acces_et_examens_restent_traites(self):
        for q in ("Un étudiant en L3 STAPS peut-il passer le CAPEPS cette année ?",
                  "Quelles conditions de diplôme pour le Capeps externe ?",
                  "que me faut il comme connaissance minimal pour devenir professeur d'EPS",
                  "Un élève a manqué son CCF parce qu'il passait un concours post-bac le même jour",
                  "voeux de jury pour le capeps dans ipack", "Comment préparer l'épreuve de CCF en natation ?"):
            self.assertFalse(refuse(q), q)

    def test_reponse_fixe_branchee(self):
        src = SRC.read_text(encoding='utf-8')
        self.assertIn('or demande_contenu_didactique_q or demande_concours_q', src)
        self.assertIn('elif demande_concours_q:', src)


if __name__ == '__main__':
    unittest.main()
