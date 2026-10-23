import unittest
from pathlib import Path
from documentary_review import mark_excerpt,source_packets

class CorpusReviewBatchTests(unittest.TestCase):
    def spans(self,path):
        return [s['text'] for p in source_packets(mark_excerpt(Path(path).read_text(),path=path)) for s in p['passages']]
    def test_fallback_calculation_source_keeps_both_operations_in_separate_proofs(self):
        spans=self.spans('data/examens/situations_2026_10_13/saisie_par_afl_pas_note_finale.txt')
        apsa=next(s for s in spans if s.startswith('Action de calcul'))
        final=next(s for s in spans if s.startswith('Résultat distinct'))
        self.assertIn('additionner',apsa)
        self.assertIn('AFL3',apsa)
        self.assertIn("trois notes d'APSA",final)
        self.assertNotIn('moyenne des trois notes ;',final)
    def test_second_active_followup_copy_separates_reassignment_and_closure(self):
        spans=self.spans('data/ipack/fiches/ipack_106_8_suivi_de_l_avancement_par_l_etablissement.txt')
        reassign=next(s for s in spans if s.startswith('Action distincte — réaffecter'))
        close=next(s for s in spans if s.startswith('Action distincte — clôturer'))
        self.assertNotIn('tous les candidats',reassign)
        self.assertIn('tous les candidats',close)
    def test_both_actor_copies_name_the_actual_operation(self):
        for name in ['data/examens/complement_reponses_validees.txt','data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt']:
            spans=self.spans(name)
            proof=next(s for s in spans if "Acteur pour déplacer un candidat" in s)
            self.assertIn("ne détermine pas les droits de réaffectation",proof)
    def test_historical_minimum_cannot_be_read_without_its_unverified_version(self):
        spans=self.spans('data/examens/audit_faq_2026_10_12/f6_procedure_verifiee.txt')
        historic=next(s for s in spans if '- Observation historique' in s)
        self.assertIn('ne vérifie pas le fonctionnement actuel',historic)
        self.assertIn('deux APSA',historic)
