"""Pertes de portée : mêmes contrôles sur plusieurs domaines fictifs et le cas réel."""
from pathlib import Path
import unittest
from unittest.mock import patch
from evidence_logic import evidence_logic_errors, evidence_constraints
from documentary_review import mark_excerpt, review_exam_answer, source_packets, validate_claims
from test_documentary_review import FakeLLM


def claim(text, proof='', section='decision'):
    return {'section':section,'text':text,'evidence':[{'document_id':'D1','passage_ids':['D1P1'],'quote':proof}]}


class EvidenceLogicTests(unittest.TestCase):
    def test_universal_absence_is_not_a_case_specific_exemption(self):
        for obj in ('un équipement de communication', 'une formation complémentaire', 'un contrôle externe'):
            proof=f"Les textes ne prescrivent pas universellement {obj} ; les exigences locales restent à vérifier."
            with self.subTest(obj=obj):
                self.assertTrue(evidence_logic_errors([claim(f"Il n'est pas nécessaire de prévoir {obj}.",proof)]))
                self.assertFalse(evidence_logic_errors([claim(f"Les textes ne prescrivent pas universellement {obj} ; les exigences locales restent à vérifier.",proof)]))

    def test_later_reservation_does_not_rescue_a_categorical_head(self):
        proof="Le dispositif n'est pas une obligation universelle ; le choix dépend du site."
        bad="Le dispositif n'est pas nécessaire, mais il faut vérifier les conditions du site."
        self.assertTrue(evidence_logic_errors([claim(bad,proof)]))

    def test_general_absence_of_requirement_does_not_establish_local_exemption(self):
        proof = "Ce passage ne pose pas une exigence générale d'accord écrit ; la procédure locale reste à vérifier."
        bad = claim("L'accord écrit n'est pas nécessaire.", proof)
        self.assertTrue(evidence_logic_errors([bad]))
        self.assertFalse(evidence_logic_errors([claim(proof, proof)]))
        bad['evidence'].append({'quote': "L'accord écrit n'est pas nécessaire pour cette opération."})
        self.assertFalse(evidence_logic_errors([bad]))

    def test_vague_permission_does_not_replace_an_explicit_condition(self):
        proof = 'Le responsable peut autoriser le dispositif après vérification des pièces.'
        self.assertTrue(evidence_logic_errors([
            claim('Vous pouvez utiliser le dispositif sous certaines conditions.', proof)]))
        self.assertFalse(evidence_logic_errors([
            claim('Vous pouvez utiliser le dispositif si le responsable valide les pièces.', proof)]))
        self.assertFalse(evidence_logic_errors([
            claim('Le dispositif est un recours exceptionnel.', proof)]))

    def test_historical_prescription_keeps_current_confirmation_reservation(self):
        proof = ('Le texte prévoit un contrôle annuel. Le référentiel est ancien ; '
                 'les justificatifs actuels doivent être confirmés par le service compétent.')
        self.assertTrue(evidence_logic_errors([
            claim('Vous devez faire réaliser un contrôle annuel.', proof)]))
        self.assertFalse(evidence_logic_errors([
            claim('Selon la note de 1986, un contrôle annuel est prévu ; les justificatifs actuels restent à confirmer.', proof)]))
        self.assertFalse(evidence_logic_errors([
            claim('Vous devez faire réaliser un contrôle annuel.',
                  'Le texte en vigueur prévoit un contrôle annuel. Le service confirme sa réception.')] ))

    def test_obligation_to_confirm_is_not_the_historical_prescription(self):
        proof = ('Le référentiel est ancien ; les modalités actuelles doivent être confirmées.')
        for text in ('Les modalités actuelles doivent être confirmées par le responsable.',
                     'Vous devez faire confirmer les justificatifs actuels.',
                     'Le responsable doit vérifier les modalités applicables.'):
            with self.subTest(text=text):
                self.assertFalse(evidence_logic_errors([claim(text, proof)]))
        self.assertTrue(evidence_logic_errors([claim(
            'Vous devez appliquer le contrôle annuel et devez vérifier les modalités.', proof)]))

    def test_vague_permission_variants_and_later_sentences_are_checked(self):
        proof = 'Le responsable peut autoriser le dispositif après vérification des pièces.'
        for text in ('Le dispositif est possible sous certaines conditions.',
                     'Une demande est nécessaire. Vous pouvez utiliser le dispositif sous conditions.'):
            with self.subTest(text=text):
                self.assertTrue(evidence_logic_errors([claim(text, proof)]))
        self.assertFalse(evidence_logic_errors([claim(
            'Le dispositif est possible si le responsable valide les pièces.', proof)]))

    def test_later_historical_obligation_cannot_hide_behind_verification(self):
        proof = 'Le référentiel est ancien ; les modalités actuelles doivent être confirmées.'
        for text in ('Le responsable doit vérifier les pièces. Une garantie spéciale doit couvrir les occupants.',
                     'Les pièces sont contrôlées ; une garantie spéciale est obligatoire.'):
            with self.subTest(text=text):
                self.assertTrue(evidence_logic_errors([claim(text, proof)]))
        self.assertFalse(evidence_logic_errors([claim(
            'Le responsable doit vérifier les pièces. Les modalités actuelles doivent être confirmées.', proof)]))
        self.assertFalse(evidence_logic_errors([claim(
            'Le responsable doit vérifier les pièces. Selon la note de 1986, une garantie spéciale est obligatoire ; ses modalités actuelles restent à confirmer.', proof)]))

    def test_no_standard_is_not_proof_of_sufficiency(self):
        for noun in ('ratio','seuil','minimum'):
            proof=f"Il n'existe pas de {noun} général ; le responsable apprécie la configuration."
            self.assertTrue(evidence_logic_errors([claim('Deux opérateurs peuvent suffire car aucun minimum national ne les exclut.',proof)]))
            self.assertFalse(evidence_logic_errors([claim('Deux opérateurs peuvent suffire si le responsable valide la configuration.',proof)]))
        proof='Le minimum est de deux opérateurs ; cet effectif suffit pour cette configuration.'
        self.assertFalse(evidence_logic_errors([claim('Deux opérateurs suffisent pour cette configuration.',proof)]))

    def test_honest_uncertainty_is_not_rejected_as_a_sufficiency_claim(self):
        proof="Il n'existe pas de ratio général ; le responsable apprécie la configuration."
        for text in (
                "Il n'est pas possible de confirmer que deux opérateurs suffisent.",
                "L'absence de ratio ne permet pas de conclure que deux opérateurs suffisent.",
                "Deux opérateurs ne sont pas automatiquement suffisants.",
                "La suffisance de deux opérateurs reste à apprécier."):
            with self.subTest(text=text):
                self.assertFalse(evidence_logic_errors([claim(text,proof)]))
        self.assertTrue(evidence_logic_errors([claim('Deux opérateurs suffisent.',proof)]))

    def test_modal_possibility_keeps_its_pending_authority_assessment(self):
        proof = "Il n'existe pas de ratio général ; le responsable apprécie la configuration."
        for authority in ('responsable du site', 'directeur', 'chef de service'):
            with self.subTest(authority=authority):
                self.assertFalse(evidence_logic_errors([claim(
                    f"Deux opérateurs peuvent suffire, mais cela dépend de l'appréciation du {authority}.", proof)]))
                self.assertTrue(evidence_logic_errors([claim(
                    f"Deux opérateurs suffisent, mais cela dépend de l'appréciation du {authority}.", proof)]))
        self.assertTrue(evidence_logic_errors([claim(
            "Deux opérateurs peuvent suffire. Cela dépend de l'appréciation du responsable.", proof)]))

    def test_uncertain_source_is_not_a_direct_proof_of_sufficiency(self):
        c=claim('Deux opérateurs suffisent.',"Il n'existe pas de ratio général.")
        c['evidence'].append({'quote':"Il n'est pas possible de confirmer que deux opérateurs suffisent."})
        self.assertTrue(evidence_logic_errors([c]))

    def test_explicit_exemption_is_not_rejected_because_other_rules_are_conditional(self):
        c=claim("Le contrôle externe n'est pas nécessaire.",'Le contrôle externe ne fait pas partie des obligations universelles.')
        c['evidence'].append({'quote':"Le contrôle externe n'est pas nécessaire pour cette configuration."})
        self.assertFalse(evidence_logic_errors([c]))

    def test_non_normative_uncertainty_is_not_labelled_a_legal_exemption(self):
        packets=source_packets(mark_excerpt("Un résultat ne garantit pas automatiquement la réussite."))
        self.assertFalse(evidence_constraints(packets))

    def test_different_objects_are_not_a_contradiction(self):
        self.assertFalse(evidence_logic_errors([
            claim("Une autorisation écrite n'est pas nécessaire."),
            claim('Le choix du matériel dépend du terrain.',section='condition')]))
        self.assertTrue(evidence_logic_errors([
            claim("Le contrôle externe n'est pas nécessaire."),
            claim('La nécessité du contrôle externe dépend de la configuration.',section='condition')]))

    def test_real_bad_answer_was_lexically_valid_but_is_now_rejected(self):
        p='data/textes/fiches/appn_moyens_alerte_milieu_isole.txt'
        packets=source_packets(mark_excerpt(Path(p).read_text(),path=p))
        span=next(s for s in packets[0]['passages'] if 'pas universellement' in s['text'])
        c=claim("Il n'est pas nécessaire d'avoir un téléphone satellite pour sortir en montagne dans un milieu hostile en VTT, mais il est essentiel de préparer des moyens de communication adaptés au terrain et à la couverture disponible.")
        c['evidence'][0]['passage_ids']=[span['id']]
        accepted,rejected=validate_claims({'claims':[c]},packets)
        self.assertEqual(len(accepted),1)
        self.assertFalse(rejected)
        self.assertTrue(evidence_logic_errors(accepted))
        limits=evidence_constraints(packets)
        self.assertTrue(any(item['passage_id']==span['id'] for item in limits))

    def test_repair_uses_shared_workflow_in_all_modes(self):
        proof="Le module n'est pas une obligation universelle ; son utilité dépend de la configuration."
        bad=claim("Le module n'est pas nécessaire.")
        good=claim("Le module n'est pas une obligation universelle ; son utilité dépend de la configuration.")
        for mode in ('textes','examens','ipack'):
            with self.subTest(mode=mode):
                audit={};llm=FakeLLM([{'claims':[bad]},{'claims':[good]}])
                result=review_exam_answer(llm,question='Le module est-il nécessaire ?',public='GT',mode=mode,documents=mark_excerpt(proof),audit=audit)
                self.assertTrue(audit['initial_rejections'])
                self.assertEqual(len(llm.prompts),2)
                self.assertIn('obligation universelle',result)
                self.assertNotIn("Le module n'est pas nécessaire",result)

    def test_shared_check_is_read_from_current_module_after_reload(self):
        text='Le responsable vérifie le module avant la validation.'
        c=claim(text);llm=FakeLLM([{'claims':[c]},{'claims':[c]}])
        with patch('evidence_logic.evidence_logic_errors',side_effect=[
                [{'index':0,'errors':['Contrôle rechargé']}], []]) as current:
            review_exam_answer(llm,question='Comment valider le module ?',public='GT',documents=mark_excerpt(text))
        self.assertEqual(current.call_count,2)
        self.assertEqual(len(llm.prompts),2)

    def test_valid_answer_stays_one_call_and_repeated_error_is_not_rendered(self):
        proof="Le module n'est pas une obligation universelle ; son utilité dépend de la configuration."
        good=claim(proof);llm=FakeLLM([{'claims':[good]}])
        review_exam_answer(llm,question='Le module est-il nécessaire ?',public='GT',documents=mark_excerpt(proof))
        self.assertEqual(len(llm.prompts),1)
        bad=claim("Le module n'est pas nécessaire.");audit={}
        with self.assertRaises(ValueError):
            review_exam_answer(FakeLLM([{'claims':[bad]},{'claims':[bad]}]),question='Module nécessaire ?',public='GT',documents=mark_excerpt(proof),audit=audit)
        self.assertNotIn('rendered_answer',audit)
        self.assertTrue(audit['final_rejections'])
