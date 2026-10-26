import unittest
from types import SimpleNamespace
from unittest import mock
import json

from short_answer import unsupported


class ArrondiTest(unittest.TestCase):
    SRC = "Bac pro : la moyenne des trois notes est arrondie au point entier supérieur après harmonisation."
    Q = "Bac professionnel 2026 CCF : moyenne brute 12,2, quel arrondi ?"

    def test_rounded_value_of_question_average_accepted(self):
        self.assertEqual(unsupported("Une moyenne brute de 12,2 devient 13.", self.SRC, self.Q), [])

    def test_other_number_still_refused(self):
        self.assertIn('nombre:14', unsupported("La moyenne devient 14.", self.SRC, self.Q))

    def test_rounding_needs_a_source_about_rounding(self):
        self.assertIn('nombre:13', unsupported("La moyenne devient 13.", "Sans mention particulière.", self.Q))


class AcademyPassedToGuardTest(unittest.TestCase):
    def test_with_short_answer_passes_user_academy(self):
        import exact_source_answer as esa
        captured = {}

        def fake(llm, **kwargs):
            captured.update(kwargs)
            return ''
        packet = {'id': 'D1', 'passages': [{'id': 'D1P1', 'text': 'À Aix-Marseille, cochez « APTE ».'}]}
        with mock.patch('short_answer.short_answer', fake), mock.patch.object(esa, 'section_label', lambda p, s: ('Titre',)):
            esa.with_short_answer(None, None, {}, 'Comment inscrire ?', [packet], ['D1P1'], None, {}, '<p>x</p>',
                                  public='Lycée Général & Techno', academy='Aix-Marseille')
        self.assertEqual(captured.get('academy'), 'Aix-Marseille')
        self.assertEqual(captured.get('public'), 'Lycée Général & Techno')


if __name__ == '__main__':
    unittest.main()
