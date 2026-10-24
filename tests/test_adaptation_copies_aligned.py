"""Copies de la procédure adaptée : contenu réellement découpé et attribué."""
import unittest
from pathlib import Path
from documentary_review import source_packets,mark_excerpt
from evidence_logic import evidence_logic_errors
BASE=Path('data/ipack/fiches/ipack_212_situation_interdiction_d_improviser_un_controle_adapte_fca_a_la_volee.txt')
COPIES=[Path('data/ipack/complement_cyclades_cas_pratiques.txt'),Path('data/examens/situations_2026_10_13/protocole_adapte_en_cours_annee.txt'),next(Path('data/ipack/fiches').glob('ipack_160*'))]
def spans(path):return [s for p in source_packets(mark_excerpt(path.read_text(),path=str(path)))for s in p['passages']]
class AdaptationCopiesTests(unittest.TestCase):
    def test_all_four_copies_share_complete_annotated_creation_and_calendar(self):
        expected=[s['text']for s in spans(BASE)if 'crée au besoin' in s['text']or s['text'].startswith(('Branche — inaptitude partielle temporaire avant la date butoir :','Branche — inaptitude partielle temporaire après la date butoir :'))]
        self.assertEqual(len(expected),3)
        for path in COPIES:
            actual=spans(path)
            for text in expected:
                with self.subTest(path=str(path),unit=text[:85]):
                    unit=next(s for s in actual if s['text']==text)
                    self.assertEqual(unit['scope']['status'],'passage_attribue')
                    self.assertIn('inaptitude partielle temporaire',unit['text'])
                    if 'date butoir :' in text:self.assertEqual(unit['scope']['academy'],'Aix-Marseille')
    def test_no_course_year_equals_no_transfer_contradiction_remains(self):
        for p in COPIES:
            self.assertNotIn("un protocole adapté créé dans iPackEPS en cours d'année ne serait pas transféré",p.read_text())
        self.assertNotIn("il sera alors transféré avec les autres",COPIES[0].read_text())
    def test_actual_before_only_permission_loses_medical_condition(self):
        proof=next(s['text']for s in spans(COPIES[0])if s['text'].startswith('Branche — inaptitude partielle temporaire avant la date butoir :'))
        bad="Si un élève doit changer de protocole adapté en cours d'année, alors un enseignant peut créer un nouveau protocole adapté dans iPackEPS, à condition que cela soit fait avant la date butoir fixée par la commission académique."
        self.assertTrue(evidence_logic_errors([{'text':bad,'evidence':[{'quote':proof}]}]))
    def test_apsa_preservation_unit_names_cyclades_and_association(self):
        for path in COPIES:
            proof=next(s['text']for s in spans(path)if 'Si un protocole' in s['text']or "si un protocole doit changer" in s['text'])
            self.assertIn('protocole Cyclades',proof)
            self.assertIn('[Associer les élèves à un protocole]',proof)
            self.assertIn("ne décrit pas un menu de création de protocole depuis la fiche individuelle",proof)
