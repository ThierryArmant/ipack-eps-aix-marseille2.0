import unittest
from claim_guards import unsupported_certainty

class MixedLimitsTests(unittest.TestCase):
    proof = ("Au bac GT, l'évaluation et la notation sont conjointes par deux enseignants. "
             "Cette règle ne suffit pas à démontrer une obligation nationale de double signature sur chaque fiche individuelle en fin d'épreuve.")
    def test_replayed_false_exemption_is_rejected_even_with_unrelated_rule(self):
        self.assertTrue(unsupported_certainty("Il n'est pas obligatoire que deux enseignants signent conjointement la fiche d'évaluation individuelle en fin d'épreuve.",[self.proof]))
    def test_documentary_reserve_is_preserved(self):
        self.assertFalse(unsupported_certainty("Les passages ne permettent pas de confirmer une obligation de double signature sur chaque fiche individuelle.",[self.proof]))
    def test_explicit_rule_on_same_formality_still_counts(self):
        self.assertFalse(unsupported_certainty("La double signature sur la fiche individuelle est obligatoire.",[self.proof,"La double signature sur la fiche individuelle est obligatoire pour cette session."]))
    def test_rule_on_another_action_not_rejected(self):
        self.assertFalse(unsupported_certainty("La co-évaluation par deux enseignants est obligatoire.",[self.proof]))
    def test_same_flaw_in_another_domain(self):
        proof="La consultation est ouverte. Le filtre ne permet pas de confirmer une autorisation de modifier les données archivées."
        self.assertTrue(unsupported_certainty("La modification des données archivées est autorisée.",[proof]))
    def test_actual_validator_rejects_trace_wording(self):
        from documentary_review import source_packets,mark_excerpt,validate_claims
        packets=source_packets(mark_excerpt(self.proof,title='Formalités'))
        accepted,errors=validate_claims({'claims':[{'section':'decision',
            'text':"Il n'est pas obligatoire que deux enseignants signent conjointement la fiche d'évaluation individuelle en fin d'épreuve.",
            'evidence':[{'document_id':'D1','quote':self.proof}]}]},packets)
        self.assertFalse(accepted)
        self.assertIn('absence de consigne',str(errors))
    def test_exact_retest_reserve_no_longer_requests_repair(self):
        text="La co-évaluation par deux enseignants d'EPS est prévue, mais cela ne signifie pas qu'une double signature est obligatoire sur chaque fiche individuelle en fin d'épreuve."
        self.assertFalse(unsupported_certainty(text,[self.proof]))
        from documentary_review import source_packets,mark_excerpt,validate_claims
        packets=source_packets(mark_excerpt(self.proof,title='Formalités'))
        accepted,errors=validate_claims({'claims':[{'section':'condition','text':text,
            'evidence':[{'document_id':'D1','quote':self.proof}]}]},packets)
        self.assertFalse(errors)
        self.assertEqual(len(accepted),1)
    def test_logical_reserve_does_not_hide_neighbor_categorical_exemption(self):
        for link in ('. ', ', mais ', ', donc ', '; toutefois '):
            text="Cela ne signifie pas qu'une double signature est obligatoire sur chaque fiche individuelle"+link+"la double signature sur chaque fiche individuelle n'est pas obligatoire."
            with self.subTest(link=link):
                self.assertTrue(unsupported_certainty(text,[self.proof]))
    def test_other_non_entailment_paraphrases_are_preserved(self):
        for verb in ('implique','prouve','démontre','veut dire'):
            self.assertFalse(unsupported_certainty("Cela ne "+verb+" pas qu'une double signature est obligatoire sur chaque fiche individuelle.",[self.proof]))
