import unittest
from pathlib import Path
from claim_guards import activity_field_errors
from documentary_review import mark_excerpt, source_packets, validate_claims, review_exam_answer
from test_documentary_review import FakeLLM

class DepositFieldProofTests(unittest.TestCase):
    def test_classification_only_does_not_prove_deposit_prohibition(self):
        facts = mark_excerpt("FAITS VÉRIFIÉS — champs d'apprentissage : demi fond : champ 1 ; course en durée : champ 5.",
                             origin='program', title='Faits calculés par le programme')
        packets = source_packets(facts)
        item = {'section':'decision', 'text':"Il n'est pas possible de déposer la course en durée et le demi-fond dans un même document car leurs champs sont différents.",
                'evidence':[{'document_id':'D1','quote':packets[0]['text']}]}
        accepted, errors = validate_claims({'claims':[item]}, packets)
        self.assertFalse(accepted)
        self.assertTrue(any('classement de champs' in e for r in errors for e in r['errors']))

    def test_program_fact_can_state_its_own_limit_without_repair(self):
        body = "Ces activités relèvent de champs d'apprentissage différents. Le classement ne permet pas de conclure à une interdiction de dépôt."
        packets = source_packets(mark_excerpt(body, origin='program'))
        item = {'section':'limite', 'text':body,
                'evidence':[{'document_id':'D1','quote':body}]}
        accepted, errors = validate_claims({'claims':[item]}, packets)
        self.assertTrue(accepted)
        self.assertFalse(errors)

    def test_field_calculation_is_not_in_deposit_prompt(self):
        facts = mark_excerpt("FAITS VÉRIFIÉS PAR LE PROGRAMME — champs d'apprentissage au lycée des activités citées : demi fond : champ 1.",
                             origin='program', title='Faits calculés par le programme')
        doc = mark_excerpt('Le dépôt documenté comporte plusieurs FCA.', path='depot.txt', priority=300)
        audit = {}
        review_exam_answer(FakeLLM([{'claims':[]},{'claims':[]}]),
                           question='Peut-on déposer course de durée et demi-fond ?', public='Lycée Général & Techno',
                           documents=doc+'\n\n'+facts, audit=audit)
        self.assertEqual(audit['excluded_field_calculation_documents'], ['D2'])
        self.assertEqual(audit['model_document_ids'], ['D1'])

    def test_explicit_denial_of_two_distinct_activities_is_rejected(self):
        text = "La course en durée et le demi-fond ne peuvent pas être considérés comme deux épreuves distinctes pour l'ensemble certificatif d'un même candidat."
        self.assertTrue(activity_field_errors([{'text':text}]))
        self.assertFalse(activity_field_errors([{'text':text}], public='Collège (DNB)'))
        self.assertTrue(activity_field_errors([{'text':'La course en durée et le demi-fond relèvent du même champ.'}]))

    def test_correct_distinction_and_conditional_reclassification_are_preserved(self):
        for text in ("Le demi-fond et la course en durée ne relèvent pas du même champ.",
                     "Le demi-fond et la course en durée sont deux activités de champs différents ; une troisième activité d'un autre champ complète l'ensemble.",
                     "Si par course de durée on entend une performance chronométrée, course de durée et demi-fond relèvent du même champ.",
                     "Le demi-fond et le relais relèvent du même champ."):
            self.assertFalse(activity_field_errors([{'text':text}]), text)

    def test_fiche_separates_unknown_deposit_procedure_from_prohibition(self):
        body = Path('data/ipack/courriels_aix_2026_10_14/courses_deux_fca_pdf_menu_individuel.txt').read_text()
        self.assertIn('elles peuvent constituer deux des trois épreuves', body)
        self.assertIn("cette limite documentaire ne démontre pas qu'un tel regroupement est interdit", body)
        self.assertNotIn('ni fusionner sa FCA', Path('data/ipack/complement_reponses_validees.txt').read_text())

if __name__ == '__main__': unittest.main()
