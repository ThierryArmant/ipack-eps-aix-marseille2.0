import unittest
from pathlib import Path
from knowledge_catalog import priority_context
from source_scope import scoped_segments

ASNS = 'data/ipack/fiches/ipack_086_article_50_mes_eleves_visualisation_asns_validation_et_impression_de_l_asns.txt'
CERT = 'data/ipack/visite_lycee_2026_10_18/dossier_certificatif_lycee_gt.txt'

class TargetedMouldTests(unittest.TestCase):
    def test_asns_composed_request_receives_individual_workflow(self):
        context = priority_context("Comment valider et imprimer l'ASNS depuis Mes élèves ?", 'Collège (DNB)', 'ipack')
        self.assertIn('ARTICLE 50', context)
        self.assertIn('[Mes Élèves] > [Visualisation]', context)
        self.assertIn('[Enregistrer]', context)
        self.assertIn('[Imprimer l’attestation]', context)

    def test_current_workflow_does_not_replace_history_branch(self):
        text = Path(ASNS).read_text()
        self.assertIn('type [sorti étab], sélection [tous]', text)
        self.assertIn('déjà validés l’année précédente', text)
        self.assertIn('Dossier Natation', text)
        self.assertIn('https://www.youtube.com/watch?v=xlXcb8Z5ZQU', text)

    def test_two_export_prerequisites_are_academic_not_software(self):
        segments = scoped_segments(CERT, Path(CERT).read_text())
        prerequisites = [s for s in segments if s['text'].startswith(('Préalable 1 à', 'Préalable 2 à'))]
        self.assertEqual(len(prerequisites), 2)
        for span in prerequisites:
            self.assertEqual(span['scope']['level'], 'academique')
            self.assertEqual(span['scope']['academy'], 'aix-marseille')
        software = next(s for s in segments if s['text'].startswith('2) [Protocole'))
        self.assertEqual(software['scope']['level'], 'logiciel')
