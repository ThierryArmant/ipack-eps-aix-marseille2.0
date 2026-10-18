import unittest
from pathlib import Path
import knowledge_catalog as kc
class TextRevisionTests(unittest.TestCase):
    def test_current_hours_reach_primary_question(self):
        body=kc.priority_context('Comment se répartissent les 108 heures d’un professeur des écoles ?', '1er degré','textes')
        self.assertIn('36 heures',body); self.assertIn('48 heures',body)
        self.assertNotIn('60 heures pour les APC',body)
    def test_archive_cannot_reenter_active_corpus(self):
        self.assertFalse(any('archives' in str(p) for p in kc.active_paths('data/textes')))
        contents='\n'.join(p.read_text() for p in kc.active_paths('data/textes'))
        self.assertNotIn('sanction quasi-systématique',contents)
        self.assertNotIn('sous 48h adressé à l\'IEN',contents)
    def test_certification_does_not_source_software_or_equivalences(self):
        p=next(Path('data/textes/fiches').glob('base_textes_officiels_016_*'));s=p.read_text()
        self.assertIn('MENE2526679C',s);self.assertIn('MENE2526357C',s)
        self.assertNotIn('ÉQUIVALENCE BPJEPS',s)
        self.assertNotIn('7 pts',s)
