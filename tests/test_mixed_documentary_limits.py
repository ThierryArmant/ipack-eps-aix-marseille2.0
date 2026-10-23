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
