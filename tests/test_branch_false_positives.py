"""Non-prescription et condition propre à la conservation d'une note."""
import unittest
from pathlib import Path
from evidence_logic import evidence_logic_errors
from documentary_review import source_packets,mark_excerpt

def claim(text,proof):return {'text':text,'evidence':[{'quote':proof}]}
PROOF="Branche — inaptitude partielle temporaire en cours d'année : l'adaptation de l'épreuve sur indications médicales est transmise pour information à la commission. La validation du projet annuel de l'établissement ne démontre pas qu'une nouvelle validation de chaque adaptation temporaire soit nécessaire."
class BranchFalsePositiveTests(unittest.TestCase):
    def test_exact_first_negative_statement_is_not_an_obligation(self):
        text="La validation du projet annuel de l'établissement ne démontre pas qu'une nouvelle validation de chaque adaptation temporaire soit nécessaire."
        self.assertFalse(evidence_logic_errors([claim(text,PROOF)]))
    def test_exact_repaired_pair_preserves_condition_and_negative_statement(self):
        text="Pour une inaptitude partielle temporaire, l'adaptation de l'épreuve sur indications médicales est transmise pour information à la commission. La validation du projet annuel de l'établissement ne démontre pas qu'une nouvelle validation de chaque adaptation temporaire soit nécessaire."
        self.assertFalse(evidence_logic_errors([claim(text,PROOF)]))
    def test_categorical_obligation_before_reserve_is_still_flagged(self):
        text="Une nouvelle validation est nécessaire, mais le projet ne démontre pas cette nécessité."
        self.assertTrue(evidence_logic_errors([claim(text,PROOF)]))
    def test_missing_permanent_condition_still_fails(self):
        proof="Branche — handicap ou inaptitude partielle permanente : les propositions sont soumises à la commission."
        self.assertTrue(evidence_logic_errors([claim('Les propositions doivent être soumises à la commission.',proof)]))
    def test_note_preservation_uses_its_real_software_condition(self):
        paths=[Path('data/ipack/complement_cyclades_cas_pratiques.txt'),Path('data/examens/situations_2026_10_13/protocole_adapte_en_cours_annee.txt'),next(Path('data/ipack/fiches').glob('ipack_160*'))]
        for path in paths:
            proof=next(s['text']for p in source_packets(mark_excerpt(path.read_text(),path=str(path)))for s in p['passages']if s['text'].startswith('Branche — APSA déjà notée :'))
            for text in ["Si un protocole doit changer alors qu'une APSA est déjà notée, il faut conserver cette APSA dans le nouveau protocole Cyclades et lui donner un nom distinct de l'ancien.","Si un élève doit changer de protocole adapté en cours d'année, il est nécessaire de conserver les APSA déjà notées dans le nouveau protocole."]:
                with self.subTest(path=str(path),text=text):self.assertFalse(evidence_logic_errors([claim(text,proof)]))
            self.assertTrue(evidence_logic_errors([claim('Il faut conserver les activités dans le protocole.',proof)]))
    def test_non_prescription_is_not_specific_to_eps(self):
        for predicate in ['ne prouve pas','ne démontre pas',"n'établit pas"]:
            proof='Branche — contrat temporaire : un avis est requis dans ce cas.'
            text=f'Le document {predicate} que cet avis est obligatoire.'
            self.assertFalse(evidence_logic_errors([claim(text,proof)]))
    def test_explicit_permission_and_unqualified_obligation_remain_controlled(self):
        proof='Branche — contrat temporaire : une revue peut être organisée.'
        self.assertTrue(evidence_logic_errors([claim('Une revue peut être organisée.',proof)]))
        self.assertFalse(evidence_logic_errors([claim('Pour un contrat temporaire, une revue peut être organisée.',proof)]))
