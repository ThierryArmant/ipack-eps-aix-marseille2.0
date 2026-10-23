import unittest
from pathlib import Path
from documentary_review import source_packets, mark_excerpt

class MouldActionConditionsTests(unittest.TestCase):
    def spans(self,path):
        return [s['text'] for p in source_packets(mark_excerpt(Path(path).read_text(),path=path)) for s in p['passages']]
    def test_reassignment_does_not_carry_closure_condition(self):
        spans=self.spans('data/examens/circuit_aix_ipack_cyclades_santorin.txt')
        assignment=next(s for s in spans if s.startswith('Action — réaffecter'))
        closure=next(s for s in spans if s.startswith('Action distincte — clôturer'))
        self.assertNotIn('doivent avoir une note',assignment)
        self.assertIn('tous les candidats du lot doivent avoir une note',closure)
    def test_specialty_condition_and_academic_list_are_distinct_evidence(self):
        spans=self.spans('data/ipack/visite_lycee_2026_10_18/dossier_certificatif_lycee_gt.txt')
        deposit=next(s for s in spans if s.startswith('Action — déposer'))
        specialty=next(s for s in spans if s.startswith('Condition propre'))
        academic=next(s for s in spans if s.startswith('Branche distincte'))
        self.assertNotIn('Enseignement de Spécialité',deposit)
        self.assertNotIn("n'a pas besoin",specialty)
        self.assertIn("n'a pas besoin de déposer",academic)
    def test_signature_limit_precedes_coevaluation_rule(self):
        text=Path('data/examens/audit100_2026_10_20/formalites_signatures_ccf.txt').read_text()
        self.assertLess(text.index('formalité de signature non déterminée'),text.index('Action distincte'))
        self.assertIn('ni à une obligation ni à une dispense',text)
