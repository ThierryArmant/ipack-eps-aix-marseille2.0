import ast
import unittest
from pathlib import Path
from knowledge_catalog import clarification


class EarlyClarificationTests(unittest.TestCase):
    def test_ambiguous_goal_requests_new_complete_question(self):
        text = clarification('Déposer une FCA de course de durée et demi-fond ?', 'Lycée Général & Techno')
        self.assertIn('nouvelle question complète', text)
        self.assertIn('demande initiale', text)
        self.assertNotIn('zone de précision', text)

    def test_known_goal_and_distinct_formats_are_not_blocked(self):
        for q in ('Déposer course de durée CA5 et demi-fond CA1 ?',
                  'Déposer course en durée entretien de soi et demi-fond ?',
                  'Déposer deux FCA 3 x 500 et 3 x 1 min 30 pour deux groupes ?'):
            self.assertEqual(clarification(q, 'Lycée Général & Techno'), '')

    def test_no_lycee_clarification_for_primary_or_college(self):
        for public in ('1er degré', 'Collège (DNB)'):
            self.assertEqual(clarification('Quel champ pour la course en durée ?', public), '')

    def test_real_handler_skips_search_and_generation_when_clarification_exists(self):
        # Exécute les vrais tests de branchement, avec des appels qui échouent
        # si le circuit tente malgré tout une recherche ou une génération.
        tree = ast.parse(Path('app.py').read_text())
        search = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                      and ast.unparse(n.test) == 'openai_api_key and (not est_cas_direct)')
        generation = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                          and ast.unparse(n.test) == 'besoin_ia')
        q = 'Déposer course de durée et demi-fond ?'
        precision = clarification(q, 'Lycée Général & Techno')
        self.assertTrue(precision)
        e = dict(openai_api_key=True, est_cas_direct=bool(precision), besoin_ia=False)
        def forbidden():
            self.fail('Un appel coûteux a été exécuté pour une clarification')
        for branch in (search, generation):
            probe = ast.If(test=branch.test,
                           body=[ast.Expr(value=ast.Call(func=ast.Name(id='forbidden',ctx=ast.Load()),args=[],keywords=[]))],
                           orelse=[])
            exec(compile(ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[])), '<routing>', 'exec'),
                 dict(e, forbidden=forbidden))


if __name__ == '__main__':
    unittest.main()
