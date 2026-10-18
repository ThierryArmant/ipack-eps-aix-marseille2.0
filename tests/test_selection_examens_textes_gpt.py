"""Cas publics indépendants des questions privées de mesure."""
import unittest
import knowledge_catalog as kc

class SelectionExamensTextesTests(unittest.TestCase):
    def test_cas_publics_et_portee(self):
        cases = [
            ('Un élève est absent sans justification au CCF en CAP', 'Lycée Pro / CAP', 'examens',
             'CAP : absence sans justification', ['Bac GT : inaptitude']),
            ('Un sportif sur liste Espoirs peut-il demander le ponctuel au bac ?', 'Lycée Général & Techno', 'examens',
             'Bac GT : SHN et examen ponctuel à sa demande', ['CAP : absence']),
            ('Un élève inapte totalement toute l’année doit-il être noté zéro au bac ?', 'Lycée Général & Techno', 'examens',
             'Bac GT : inaptitude totale annuelle', ['CAP : absence']),
            ('Un professeur peut-il imposer une marque de tenue aux familles ?', 'Collège', 'textes',
             'Fournitures et équipements demandés aux familles', ['Bac GT :']),
            ('Comment demander la protection fonctionnelle après une menace ?', 'Collège', 'textes',
             'Violences, discriminations et harcèlement', ['CAP : absence']),
        ]
        for q, public, mode, expected, forbidden in cases:
            with self.subTest(q=q):
                titles = kc.priority_titles(q, public, mode)
                self.assertTrue(any(t.startswith(expected) for t in titles), titles)
                self.assertFalse(any(t.startswith(f) for t in titles for f in forbidden), titles)
