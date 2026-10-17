"""Une démarche en liste reste attachée à sa phrase d'introduction (cas du centre étranger, 17 octobre 2026)."""
import unittest

from documentary_review import bind_list_items, mark_excerpt, source_packets


def spans(lines, scopes=None):
    body, out, offset = '', [], 0
    for i, line in enumerate(lines):
        out.append({'text': line, 'start': offset, 'end': offset + len(line),
                    'scope': (scopes[i] if scopes else {})})
        body += line + '\n'
        offset += len(line) + 1
    return out, body


class ListBindingTests(unittest.TestCase):
    def test_intro_and_steps_form_one_passage(self):
        s, body = spans(['Démarche, dans cet ordre :', '1. Cocher les fonctions.', '2. Déclarer les APSA.', '3. Compléter les protocoles.', 'Autre fait.'])
        out = bind_list_items(s, body)
        self.assertEqual(len(out), 2)
        self.assertIn('1. Cocher les fonctions.', out[0]['text'])
        self.assertIn('3. Compléter les protocoles.', out[0]['text'])
        self.assertEqual(out[1]['text'], 'Autre fait.')

    def test_local_line_never_merged_with_national_line(self):
        aix = {'academy': 'Aix-Marseille'}
        s, body = spans(['Vérifier dans l’ordre :', '1. Contrôle national.', '2. À Aix-Marseille, consigne locale.'],
                        [{}, {}, aix])
        out = bind_list_items(s, body)
        self.assertEqual(out[-1]['text'], '2. À Aix-Marseille, consigne locale.')

    def test_faq_and_sources_lines_are_not_absorbed(self):
        s, body = spans(['Procédure :', '- étape A', 'Q2 : autre question ?', 'R2 : autre réponse.'])
        out = bind_list_items(s, body)
        self.assertTrue(any(p['text'].startswith('Q2') for p in out))

    def test_plain_lines_unchanged(self):
        s, body = spans(['Première règle.', 'Deuxième règle.'])
        self.assertEqual([p['text'] for p in bind_list_items(s, body)], ['Première règle.', 'Deuxième règle.'])

    def test_registered_sheet_keeps_fraud_steps_together(self):
        path = 'data/examens/fraude_ccf_eps.txt'
        with open(path, encoding='utf-8') as f:
            packet = source_packets(mark_excerpt(f.read(), path=path, title='Fraude'))[0]
        step = next(p for p in packet['passages'] if '1) Faire cesser la fraude' in p['text'])
        self.assertIn('4) Ne pas saisir de zéro', step['text'])


if __name__ == '__main__':
    unittest.main()
