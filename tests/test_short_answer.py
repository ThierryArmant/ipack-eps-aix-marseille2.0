"""Réponse courte : rédigée à partir des seuls extraits retenus, contrôlée phrase par phrase."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from generation_runtime import load_runtime
import short_answer as sa


def _llm(*outputs):
    llm = Mock()
    llm.complete.side_effect = [SimpleNamespace(text=o if isinstance(o, str) else json.dumps(o)) for o in outputs]
    return llm


PASSAGES = [('Réaffecter un lot', "Dans Santorin, le suivi des lots permet au chef d'établissement de réaffecter un lot à un autre examinateur."),
            ('Réaffecter un lot', "Le nouvel enseignant doit avoir une mission d'évaluation EPS dans Imag'in.")]


class ControlesPhrases(unittest.TestCase):
    def run_sa(self, phrases):
        audit = {}
        out = sa.short_answer(_llm({'phrases': phrases}), tracer=lambda llm, a, stage: llm,
                              audit=audit, question='Comment réaffecter un lot ?', passages=PASSAGES)
        return out, audit['short_answer']

    def test_phrase_appuyee_conservee_avec_ses_numeros(self):
        out, rep = self.run_sa([{'texte': "Demandez au chef d'établissement de réaffecter le lot dans le suivi des lots de Santorin.", 'passages': [1]},
                                {'texte': "Le nouvel enseignant doit avoir sa mission dans Imag'in.", 'passages': [2]}])
        self.assertEqual(rep['status'], 'rendered')
        self.assertIn('<sup>1</sup>', out)
        self.assertIn('<sup>2</sup>', out)

    def test_interlocuteur_menu_nombre_inventes_retires(self):
        out, rep = self.run_sa([{'texte': 'Contactez la DEC.', 'passages': [1]},
                                {'texte': 'Allez dans [Lots] > [Réaffecter].', 'passages': [1]},
                                {'texte': 'Vous avez 15 jours.', 'passages': [2]},
                                {'texte': "Le nouvel enseignant doit avoir sa mission dans Imag'in.", 'passages': [2]}])
        self.assertEqual([r['texte'] for r in rep['rejected']], ['Contactez la DEC.', 'Allez dans [Lots] > [Réaffecter].', 'Vous avez 15 jours.'])
        self.assertNotIn('DEC', out)
        self.assertIn("Imag&#x27;in", out)

    def test_numero_absent_ou_hors_liste_refuse(self):
        out, rep = self.run_sa([{'texte': 'Phrase sans source.', 'passages': []},
                                {'texte': 'Autre.', 'passages': [9]}])
        self.assertEqual(out, '')
        self.assertEqual(rep['status'], 'nothing_kept')

    def test_json_invalide_sans_relance(self):
        audit = {}
        llm = _llm('pas du json')
        out = sa.short_answer(llm, tracer=lambda l, a, stage: l, audit=audit, question='q', passages=PASSAGES)
        self.assertEqual(out, '')
        self.assertEqual(audit['short_answer']['status'], 'invalid_no_retry')
        llm.complete.assert_called_once()


class Integration(unittest.TestCase):
    def setUp(self):
        self.rt = load_runtime()
        dr = self.rt.documentary_review
        self.docs = dr.mark_excerpt("Dans Santorin, le suivi des lots permet au chef d'établissement de réaffecter un lot à un autre examinateur.",
                                    path='data/exemple.txt', title='Réaffecter un lot')

    def answer(self, llm, synthesis):
        audit = {}
        out = self.rt.exact_source_answer.exact_answer(llm, reviewer=self.rt.documentary_review,
            tracer=lambda l, a, stage: l, documents=self.docs, question='Comment réaffecter un lot ?',
            public='Lycée Général & Techno', mode='examens', academy='Aix-Marseille', audit=audit, synthesis=synthesis)
        return out, audit

    def selection(self):
        dr = self.rt.documentary_review
        pid = dr.source_packets(self.docs)[0]['passages'][-1]['id']
        return {'principal': 'D1', 'complements': [], 'passages': [pid]}

    def test_reponse_courte_en_tete_et_extraits_replies(self):
        llm = _llm(self.selection(), {'phrases': [{'texte': "Le chef d'établissement réaffecte le lot dans le suivi des lots de Santorin.", 'passages': [1]}]})
        out, audit = self.answer(llm, True)
        self.assertEqual(llm.complete.call_count, 2)
        self.assertLess(out.index('réaffecte le lot'), out.index('<details>'))
        self.assertIn('Voir les extraits des fiches (1)', out)
        self.assertIn('<strong>1.</strong>', out)

    def test_echec_de_la_reponse_courte_garde_les_extraits(self):
        llm = _llm(self.selection(), {'phrases': [{'texte': 'Contactez la DEC.', 'passages': [1]}]})
        out, audit = self.answer(llm, True)
        self.assertNotIn('Voir les extraits des fiches', out)
        self.assertIn('suivi des lots', out)

    def test_sans_option_un_seul_appel(self):
        llm = _llm(self.selection())
        self.answer(llm, False)
        llm.complete.assert_called_once()


if __name__ == '__main__':
    unittest.main()
