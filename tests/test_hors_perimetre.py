import ast
import re
import unicodedata
import unittest
from pathlib import Path


def filtre_hors_perimetre():
    """Reconstruit le filtre « HORS PÉRIMÈTRE » de l'onglet Textes à partir d'app.py."""
    tree = ast.parse(Path('app.py').read_text(encoding='utf-8'))
    env = dict(re=re, unicodedata=unicodedata)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in ('normaliser', 'contient_mot_cle'):
            exec(compile(ast.Module(body=[n], type_ignores=[]), 'app.py', 'exec'), env)
    listes = {n.targets[0].id: n.value for n in ast.walk(tree)
              if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
              and n.targets[0].id in ('mots_cles_intention_peda', 'mots_cles_eps_admin')}
    env['mots_cles_intention_peda'] = eval(compile(ast.Expression(listes['mots_cles_intention_peda']), 'app.py', 'eval'), env)
    mots = [env['normaliser'](m) for m in eval(compile(ast.Expression(listes['mots_cles_eps_admin']), 'app.py', 'eval'), env)]
    return lambda question: not env['contient_mot_cle'](env['normaliser'](question), mots)


class HorsPerimetreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hors_sujet = staticmethod(filtre_hors_perimetre())

    def test_questions_legitimes_ne_sont_pas_rejetees(self):
        for q in ("Le tiers-temps est-il automatiquement accordé avec un PAP ?",
                  "Un but mobile semble instable. Dois-je le pousser fortement puis le coucher moi-même au sol ?",
                  "Faut-il obligatoirement trois heures d’accompagnement personnalisé en sixième cette année ?",
                  "Dans quel délai le rectorat répond-il à une demande d'aménagement d'examen, et peut-on contester ?",
                  "Pour les fiches individuelles, c'est un format particulier ou feuille libre ?",
                  "Comment remplir mes listes de non nageurs"):
            self.assertFalse(self.hors_sujet(q), q)

    def test_questions_etrangeres_restent_rejetees(self):
        for q in ("Quelle est la meilleure recette de tarte aux pommes ?",
                  "Comment réparer ma machine à laver ?"):
            self.assertTrue(self.hors_sujet(q), q)


if __name__ == '__main__':
    unittest.main()
