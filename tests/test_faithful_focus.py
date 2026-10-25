import html
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from exact_source_answer import exact_answer
from generation_runtime import load_runtime


class FaithfulFocusTests(unittest.TestCase):
    def run_case(self, texts, choose):
        dr = load_runtime().documentary_review
        docs = '\n\n'.join(dr.mark_excerpt(text, path=f'data/source{i}.txt', title=f'Source {i}')
                           for i, text in enumerate(texts))
        packets = dr.source_packets(docs)
        choice = choose(packets)
        llm = SimpleNamespace(model='fake', temperature=0,
            complete=Mock(return_value=SimpleNamespace(text=json.dumps(choice))))
        audit = {}
        answer = exact_answer(llm, reviewer=dr, tracer=dr.TracedLLM, documents=docs,
            question='Comment effectuer cette action ?', public='p', mode='examens',
            academy='Aix-Marseille', audit=audit)
        return answer, audit, llm

    def test_whole_passages_first_context_preserved_for_several_families(self):
        families = [
            ('Le chef réaffecte le lot dans le suivi. Mission EPS dans Imag’in requise.',
             'Clôturer le lot exige les notes complètes.'),
            ('Si l’attestation est validée, sélectionner les élèves puis [Imprimer].',
             'La validation d’une nouvelle attestation est une autre opération.'),
            ('Après avoir déclaré les APSA, configurer les épreuves dans [Protocoles].',
             'Importer les élèves est une autre opération.'),
            ('Pour changer d’établissement, revenir au [Tableau de bord].',
             'Un changement de classe concerne un élève.')]
        for action, neighbour in families:
            with self.subTest(action=action):
                answer, audit, llm = self.run_case([action+'\n\n'+neighbour],
                    lambda ps: dict(principal='D1', complements=[], passages=[ps[0]['passages'][0]['id']]))
                lead, context = answer.split('<details><summary>Consulter', 1)
                self.assertIn(html.escape(action), lead)
                self.assertNotIn(html.escape(neighbour), lead)
                self.assertIn(html.escape(neighbour), context)
                self.assertFalse(audit['exact_extracts']['focus_completeness_proven'])
                llm.complete.assert_called_once()
                self.assertEqual(load_runtime().documentary_review.usage_summary(audit)['generation_calls'], 0)

    def test_prerequisite_and_limit_from_other_source_keep_order_and_exact_text(self):
        texts = ['Action si la condition est satisfaite.', 'Préalable dans un autre outil.\n\nNe pas supprimer les notes.']
        def choose(ps):
            return dict(principal='D1', complements=['D2'], passages=[
                ps[0]['passages'][0]['id'], ps[1]['passages'][0]['id'], ps[1]['passages'][1]['id']])
        answer, audit, _ = self.run_case(texts, choose)
        lead = answer.split('<details><summary>Consulter')[0]
        for text in ['Action si la condition est satisfaite.', 'Préalable dans un autre outil.', 'Ne pas supprimer les notes.']:
            self.assertIn(text, lead)
        self.assertEqual(audit['exact_extracts']['focused_passage_ids'], ['D1P1','D2P1','D2P2'])

    def test_foreign_empty_null_and_invented_ids_do_not_trigger_retry(self):
        for focus in [[], None, ['MENU_INVENTE']]:
            with self.subTest(focus=focus):
                answer, audit, llm = self.run_case(['Action documentée.', 'Voisin.'],
                    lambda ps: dict(principal='D1', complements=[], passages=focus))
                self.assertEqual(audit['exact_extracts']['status'], 'invalid_selection_no_retry')
                self.assertNotIn('MENU_INVENTE', answer)
                llm.complete.assert_called_once()

    def test_mixed_operation_passage_is_never_cut_and_html_is_escaped(self):
        action = 'Action A si X ; action B si Y. <script>danger()</script>'
        answer, _, _ = self.run_case([action],
            lambda ps: dict(principal='D1', complements=[], passages=['D1P1']))
        self.assertIn(html.escape(action), answer.split('<details><summary>Consulter')[0])
        self.assertNotIn('<script>', answer)


if __name__ == '__main__':
    unittest.main()
