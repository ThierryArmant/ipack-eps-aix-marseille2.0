"""Perte du périmètre d'une branche, cas réel et domaines fictifs sans IA."""
import unittest
from evidence_logic import evidence_logic_errors

def claim(text,quote):return {'text':text,'evidence':[{'quote':quote}]}

class ExplicitBranchTests(unittest.TestCase):
    def test_actual_validation_claims_do_not_drop_permanent_branch(self):
        proof="Branche — handicap ou inaptitude partielle permanente : les propositions d'adaptation sont soumises à la commission académique. Préparer ou saisir le protocole avant son retour ne constitue pas une décision de cette commission."
        for bad in ["Les propositions d'adaptation doivent être soumises à la commission académique pour validation.","Si un élève doit changer de protocole adapté en cours d'année scolaire, les propositions d'adaptation doivent être soumises à la commission académique."]:
            self.assertTrue(evidence_logic_errors([claim(bad,proof)]))
        for good in ["En cas de handicap, les propositions d'adaptation doivent être soumises à la commission académique.","Pour une inaptitude partielle permanente, les propositions d'adaptation doivent être soumises à la commission académique.","La préparation ne constitue pas une décision de la commission."]:
            self.assertFalse(evidence_logic_errors([claim(good,proof)]))
    def test_temporary_medical_branch_is_not_a_general_restriction(self):
        proof="Branche — inaptitude partielle temporaire en cours d'année : l'adaptation de l'épreuve sur indications médicales est transmise pour information."
        self.assertTrue(evidence_logic_errors([claim("Le changement de protocole doit être justifié par des indications médicales et ne peut être décidé unilatéralement par l'enseignant.",proof)]))
        self.assertFalse(evidence_logic_errors([claim("Pour une inaptitude partielle temporaire, l'adaptation doit être transmise pour information.",proof)]))
    def test_control_is_not_specific_to_medical_cases(self):
        for label in ['dépôt tardif','contrat temporaire','équipement défectueux']:
            proof=f'Branche — {label} : le responsable doit vérifier les pièces.'
            self.assertTrue(evidence_logic_errors([claim('Le responsable doit vérifier les pièces.',proof)]))
            self.assertFalse(evidence_logic_errors([claim(f'Pour un {label}, le responsable doit vérifier les pièces.',proof)]))
    def test_later_reservation_does_not_rescue_unqualified_rule(self):
        proof='Branche — contrat temporaire : un avis est obligatoire.'
        self.assertTrue(evidence_logic_errors([claim('Un avis est obligatoire, mais cela concerne le contrat temporaire.',proof)]))
    def test_unmarked_proof_and_non_prescriptive_reserve_are_not_changed(self):
        self.assertFalse(evidence_logic_errors([claim('Un avis est obligatoire.','Un avis est obligatoire.')]))
        self.assertFalse(evidence_logic_errors([claim('La situation reste à vérifier.','Branche — contrat temporaire : un avis est obligatoire.')]))

    def test_preparing_is_not_made_obligatory_by_its_lack_of_decision_value(self):
        proof="Branche — handicap ou inaptitude partielle permanente : les propositions d'adaptation sont soumises à la commission. Préparer ou saisir le protocole avant son retour ne constitue pas une décision de cette commission."
        bad="Il est nécessaire de préparer ou saisir le nouveau protocole avant son retour à la commission, mais cela ne constitue pas une décision de cette commission."
        errors=evidence_logic_errors([claim(bad,proof)])
        self.assertTrue(any('non-équivalence' in str(e) for e in errors))
        bounded="Pour une inaptitude partielle permanente, il est nécessaire de préparer ou saisir le protocole avant son retour à la commission."
        self.assertTrue(any('non-équivalence' in str(e) for e in evidence_logic_errors([claim(bounded,proof)])))
    def test_filing_does_not_become_obligatory_without_its_own_proof(self):
        proof='Déposer le fichier ne constitue pas une validation du dossier.'
        bad=claim('Il est nécessaire de déposer le fichier.',proof)
        self.assertTrue(evidence_logic_errors([bad]))
        bad['evidence'].append({'quote':'Pour soumettre le dossier, déposer le fichier est obligatoire.'})
        self.assertFalse(evidence_logic_errors([bad]))

    def test_existing_repair_receives_condition_error_and_accepts_bounded_version(self):
        from documentary_review import mark_excerpt,review_exam_answer
        from test_documentary_review import FakeLLM,CHECKS
        proof='Branche — contrat temporaire : le responsable doit vérifier les pièces.'
        def output(text):
            return {'claims':[{'section':'etape','text':text,'evidence':[{'document_id':'D1','passage_ids':['D1P1'],'level':'documentaire'}],'checks':CHECKS.copy()}]}
        llm=FakeLLM([output('Le responsable doit vérifier les pièces.'),output('Pour un contrat temporaire, le responsable doit vérifier les pièces.')]);audit={}
        answer=review_exam_answer(llm,question='Quelles vérifications sont prévues ?',public='GT',mode='textes',documents=mark_excerpt(proof),audit=audit)
        self.assertTrue(audit['repair_performed'])
        self.assertTrue(audit['repair_successful'])
        self.assertEqual(len(llm.prompts),2)
        self.assertIn('condition explicite',str(audit['initial_rejections']))
        self.assertIn('contrat temporaire',answer)
        self.assertFalse(audit['final_rejections'])

    def test_persistent_bad_repair_uses_existing_unconfirmed_response(self):
        from documentary_review import mark_excerpt,review_exam_answer,render_exam_fallback
        from test_documentary_review import FakeLLM,CHECKS
        proof='Branche — contrat temporaire : le responsable doit vérifier les pièces.'
        bad={'claims':[{'section':'etape','text':'Le responsable doit vérifier les pièces.','evidence':[{'document_id':'D1','passage_ids':['D1P1'],'level':'documentaire'}],'checks':CHECKS.copy()}]}
        llm=FakeLLM([bad,bad]);audit={};documents=mark_excerpt(proof)
        with self.assertRaises(ValueError):
            review_exam_answer(llm,question='Quelles vérifications sont prévues ?',public='GT',mode='textes',documents=documents,audit=audit)
        self.assertEqual(len(llm.prompts),2)
        self.assertTrue(audit['final_rejections'])
        fallback=render_exam_fallback(audit,question='Quelles vérifications sont prévues ?',documents=documents,mode='textes')
        self.assertIn('Aucune consigne applicable trouvée',fallback)  # fixture sans référence institutionnelle

    def test_two_explicit_branches_can_be_preserved_in_one_claim(self):
        c=claim('Pour un contrat temporaire, un avis est obligatoire. Pour un contrat permanent, une revue est nécessaire.','Branche — contrat temporaire : un avis est obligatoire.')
        c['evidence'].append({'quote':'Branche — contrat permanent : une revue est nécessaire.'})
        self.assertFalse(evidence_logic_errors([c]))
        c['text']='Un avis est obligatoire. Pour un contrat permanent, une revue est nécessaire.'
        self.assertTrue(evidence_logic_errors([c]))
