import unittest
from pathlib import Path
from documentary_review import source_packets, mark_excerpt, render_claims
from source_scope import select_academy


class IpackSoftwareScopeTests(unittest.TestCase):
    def test_staff_technical_document_has_no_academic_reservation(self):
        path = 'data/ipack/fiches/equipe_eps_actualisation_logiciel.txt'
        packets = source_packets(mark_excerpt(Path(path).read_text(), path=path, title='Équipe EPS'))
        for academy in ('Non précisée', 'Versailles', 'Aix-Marseille'):
            selected, marked = select_academy(packets, academy)
            self.assertEqual(marked, [])
            evidence = [{'document_id': selected[0]['id'], 'scope': selected[0]['passages'][0]['scope']}]
            result = render_claims([{'section': 'decision', 'text': 'Tous les enseignants peuvent actualiser la liste.', 'evidence': evidence}], selected, mode='ipack')
            self.assertNotIn('Portée académique', result)
            self.assertNotIn('application locale', result)
            self.assertIn('Documentation du logiciel', result)

    def test_local_or_mixed_procedure_keeps_its_scope(self):
        for kinds in (['consigne_academique'], ['consigne_academique', 'logiciel']):
            packet = {'id': 'D1', 'passages': [{'id': 'P1', 'scope': {'nature': kinds, 'academy': 'Aix-Marseille'}}]}
            selected, marked = select_academy([packet], 'Versailles')
            self.assertTrue(marked)
            self.assertEqual(selected[0]['passages'][0]['scope']['not_confirmed_for'], 'Versailles')
