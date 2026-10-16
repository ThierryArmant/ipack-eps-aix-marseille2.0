import unittest
from knowledge_catalog import reference_notice

class AtomicSHNSelection(unittest.TestCase):
    def selected(self,q):
        return reference_notice(['gt'],q,'Lycée Général & Techno')
    def test_recognition_does_not_select_twenty_procedure(self):
        text=str(self.selected('Repérer le statut SHN dans mon lot Santorin'))
        self.assertIn('reperer_mention_santorin',text)
        self.assertNotIn('k4_procedure_verifiee',text)
    def test_twenty_procedure_remains(self):
        text=str(self.selected('SHN : le 20 ne se propose pas dans Santorin'))
        self.assertIn('k4_procedure_verifiee',text)
        self.assertNotIn('reperer_mention_santorin',text)
    def test_cycle_and_medical_cases_are_distinct(self):
        text=str(self.selected('Un SHN a suivi un seul cycle de cours : comment évaluer ?'))
        self.assertIn('cycle_notes_disponibles_gt',text)
        self.assertNotIn('shn_note_unique.txt',text)
        medical=str(self.selected('SHN : DI DI 20 est-ce possible ?'))
        self.assertIn('shn_note_unique.txt',medical)
        self.assertNotIn('cycle_notes_disponibles_gt',medical)
