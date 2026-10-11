"""Les décisions validées (config/decisions_validees.json) ne doivent être contredites par aucune fiche active."""
import json
import re
import unittest
from pathlib import Path

import knowledge_catalog as kc

DECISIONS = json.loads(Path('config/decisions_validees.json').read_text(encoding='utf-8'))['decisions']
CHAMPS = ('id', 'decision', 'diplome', 'session', 'source', 'exceptions', 'portee', 'motifs_interdits')


def sources_actives():
    yield Path('app.py')
    for folder in ('data/ipack', 'data/examens', 'data/textes', 'data/commun', 'data/peda'):
        yield from kc.active_paths(folder)


def contradictions(decision):
    found = []
    for path in sources_actives():
        text = kc.normalise(path.read_text(encoding='utf-8'))
        if decision['portee'] == 'section':
            units = [(text[:m.start()].count('\n') + 1, m.group(0))
                     for m in re.finditer(r'(?:^|\n)###[^\n]*(?:\n(?!###)[^\n]*)*', text)] or [(1, text)]
        else:
            units = list(enumerate(text.splitlines(), 1))
        for line, unit in units:
            if any(re.search(m, unit) for m in decision['motifs_interdits']) and \
                    not any(re.search(s, unit) for s in decision.get('sauf_si', [])):
                found.append(f'{path}:{line}')
    return found


class DecisionsTests(unittest.TestCase):
    def test_each_decision_is_documented(self):
        for decision in DECISIONS:
            with self.subTest(decision=decision.get('id')):
                for champ in CHAMPS:
                    self.assertTrue(decision.get(champ), champ)

    def test_no_active_source_contradicts_a_decision(self):
        for decision in DECISIONS:
            with self.subTest(decision=decision['id']):
                self.assertEqual(contradictions(decision), [], decision['decision'])

    def test_patterns_respect_the_distinctions(self):
        cap = next(d for d in DECISIONS if d['id'] == 'CAP-DEUX-EPREUVES-RETENUES')
        def flagged(text):
            return any(re.search(m, text) for m in cap['motifs_interdits']) and \
                not any(re.search(s, text) for s in cap['sauf_si'])
        self.assertTrue(flagged(kc.normalise("Il n'est pas possible d'affecter des candidats de CAP sur 3 épreuves.")))
        self.assertFalse(flagged(kc.normalise("2 épreuves, pas 3. On peut faire pratiquer 3 activités ; l'élève en retient 2.")))
        self.assertFalse(flagged(kc.normalise("Le CAP comporte deux activités relevant de deux champs, pas trois.")))
        di = DECISIONS[0]
        line = kc.normalise("Point académique à confirmer : une consigne (DI + DI + Note = DI) figure dans une autre fiche")
        self.assertFalse(any(re.search(m, line) for m in di['motifs_interdits']) and
                         not any(re.search(s, line) for s in di['sauf_si']))


if __name__ == '__main__':
    unittest.main()
