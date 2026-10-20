"""Conseils expérimentaux : identifier une information absente sans bloquer."""
import json
import re
import unittest
from pathlib import Path
from clarification_lexicon import suggestions

class ClarificationLexiconTests(unittest.TestCase):
    def test_missing_information_has_a_specific_nonblocking_suggestion(self):
        cases=[
            ('Je voudrais valider mais comment faire ?', 'examens','validation_objet'),
            ('Comment déposer une fiche ?', 'ipack','fiche_depot'),
            ('Je ne peux plus modifier, que faire ?', 'ipack','modification_objet'),
            ('Mes élèves sont introuvables, que faire ?', 'examens','eleves_localisation'),
            ('Je ne peux plus saisir mes notes.', 'ipack','saisie_notes_usage'),
            ('Ça bloque et il y a un message d’erreur.', 'ipack','probleme_ecran'),
            ('L’application bloque à la connexion.', 'textes','logiciel_hors_contexte'),
        ]
        for q,mode,expected in cases:
            with self.subTest(q=q):
                result=suggestions(q,mode=mode)
                self.assertEqual(len(result),1)
                self.assertEqual(result[0]['id'],expected)
                self.assertFalse(result[0]['blocking'])
                self.assertGreaterEqual(len(result[0]['options']),2)
    def test_given_objects_do_not_request_same_information(self):
        for q in ['Comment valider mon protocole ?', 'Comment valider le savoir-nager ?', 'Comment déposer une fiche individuelle ?', 'Je ne peux plus modifier mon groupe.', 'Mes élèves n’apparaissent pas dans Santorin.', 'Les élèves manquent dans mes classes iPackEPS.', 'Je ne peux plus saisir mes notes dans mon lot Santorin.', 'Le message Instance apparaît en rouge dans iPackEPS.']:
            with self.subTest(q=q):self.assertEqual(suggestions(q,mode='ipack'),[])
    def test_selected_exam_context_already_identifies_grade_usage(self):
        q='Je ne peux plus saisir mes notes.'
        self.assertTrue(suggestions(q,mode='ipack'))
        self.assertEqual(suggestions(q,mode='examens'),[])
    def test_releve_and_absence_do_not_mean_missing_list(self):
        for q in ['Précisez ce qui relève du texte national.', 'Un élève est absent et a manqué son épreuve.', 'Le certificat médical concerne mon élève blessé.', 'La relève des collègues est organisée demain.']:
            with self.subTest(q=q):self.assertEqual(suggestions(q,mode='examens'),[])
    def test_ordinary_explanations_are_not_forced_into_a_choice(self):
        for q in ['Quelle différence entre dispense et inaptitude ?', 'Comment se déroule la validation des référentiels ?', 'Comment fonctionne la certification en CCF ?', 'Que faire après la commission d’harmonisation ?']:
            with self.subTest(q=q):self.assertEqual(suggestions(q,mode='examens'),[])
    def test_rule_patterns_compile_and_incomplete_input_is_left_alone(self):
        data=json.loads(Path('config/lexique_clarification.json').read_text())
        self.assertEqual(len({r['id'] for r in data['regles']}),len(data['regles']))
        for rule in data['regles']:
            for p in rule['motifs']+rule['exclure_motifs']:re.compile(p)
        for q in ['', 'valider', 'la relève']:
            self.assertEqual(suggestions(q,mode='examens'),[])
    def test_prototype_is_not_connected_to_live_form(self):
        self.assertNotIn('clarification_lexicon',Path('app.py').read_text())
