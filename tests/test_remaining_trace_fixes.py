import unittest
from pathlib import Path
import knowledge_catalog as kc
from guide_request import vague_request_opens_guide
from documentary_review import absent_terms, situation_mismatch
from claim_guards import workflow_fidelity_errors


def c(text, proof, section='etape'):
    return {'text':text, 'section':section, 'evidence':[{'quote':proof}]}


class RemainingSelectionTests(unittest.TestCase):
    def test_generic_missing_fields_requests_screen_not_agenda(self):
        q = 'Erreur informations manquantes à la sauvegarde'
        self.assertIn('écran', kc.clarification(q, 'Lycée Général & Techno', mode='ipack'))
        self.assertFalse(vague_request_opens_guide(q, 'ipack', 'Lycée Général & Techno'))
        self.assertFalse(kc.clarification(q+' dans la configuration des classes', 'Collège (DNB)', mode='ipack'))

    def test_staff_integration_does_not_open_generic_guide(self):
        q = 'TZR : quel établissement doit intégrer mes services dans iPackEPS en priorité ?'
        self.assertFalse(vague_request_opens_guide(q, 'ipack', 'Lycée Général & Techno'))
        self.assertIn('MULTI-ÉTABLISSEMENTS', kc.priority_context(q, 'Lycée Général & Techno', 'ipack'))
        self.assertIn('ne fixe aucun ordre de priorité', kc.priority_context(q, 'Lycée Général & Techno', 'ipack'))

    def test_equipment_name_and_college_premise_are_both_kept(self):
        q = 'Ancien nom du gymnase et protocole DNB : modifier le libellé ?'
        context = kc.priority_context(q, 'Collège (DNB)', 'ipack')
        self.assertIn("Modifier l'Équipement", context)
        self.assertIn("ce n'est pas un protocole iPackEPS", context)

    def test_equipment_and_timetable_can_coexist(self):
        q = 'Le gymnase a changé de nom ; impossible de lui associer nos créneaux'
        context = kc.priority_context(q, 'Collège (DNB)', 'ipack')
        self.assertIn("Modifier l'Équipement", context)
        self.assertIn('Agenda Équipe', context)

    def test_adult_service_does_not_turn_college_into_student_public(self):
        q = 'TZR au collège et au lycée, calcul des ORS et ISSR'
        self.assertEqual(kc.effective_context(q,'Lycée Général & Techno','examens'),('Lycée Général & Techno','textes'))
        context = kc.priority_context(q,'Lycée Général & Techno','examens')
        self.assertIn('89-825', context)
        self.assertNotIn('DNB : calcul', context)
        self.assertTrue(situation_mismatch(q, 'DNB : moyenne du contrôle continu et LSU'))
        self.assertFalse(situation_mismatch(q, 'TZR : obligations de service et rattachement'))

    def test_software_question_keeps_its_mode_and_teaching_query_is_not_staff_pay(self):
        self.assertEqual(kc.effective_context('TZR affecté : accès à iPackEPS', 'Collège (DNB)', 'ipack')[1], 'ipack')
        self.assertEqual(kc.effective_context('Le TZR remplace le professeur pour saisir dans Santorin', 'Lycée Général & Techno','examens')[1], 'examens')

    def test_usual_staff_acronyms_not_reported_as_invented(self):
        self.assertEqual(absent_terms('RAD et ORS', []), [])
        self.assertIn('XQZ', absent_terms('XQZ', []))


class RemainingFidelityTests(unittest.TestCase):
    def test_establishing_report_is_not_exact_transmission_deadline(self):
        proof = "Le chef d'établissement établit le rapport d'accident dans les 48 heures pour l'autorité hiérarchique."
        self.assertTrue(workflow_fidelity_errors([c('Le délai légal exact de transmission est de 48 heures.',proof)],'Rapport accident : quel délai ?'))
        self.assertFalse(workflow_fidelity_errors([c('Le rapport doit être établi dans les 48 heures.',proof)],'Rapport accident : quel délai ?'))
        self.assertFalse(workflow_fidelity_errors([c("Le texte ne précise pas un délai exact de transmission de 48 heures.",proof)],'Rapport accident : quel délai ?'))
        explicit = 'Le rapport doit être transmis dans les 48 heures.'
        self.assertFalse(workflow_fidelity_errors([c(explicit,explicit)],'Rapport accident : quel délai ?'))

    def test_generic_equipment_proof_cannot_confirm_a_dnb_protocol(self):
        proof = 'Sélectionner le gymnase puis cliquer sur Modifier l’Équipement.'
        self.assertTrue(workflow_fidelity_errors([c("Cela ne bloque pas l'édition du protocole DNB.",proof)],'Gymnase : protocole DNB ?'))
        self.assertFalse(workflow_fidelity_errors([c("Au collège, ce n'est pas un protocole iPackEPS.", 'Au collège, ce n’est pas un protocole iPackEPS.')], 'Gymnase : protocole DNB ?'))

    def test_renaming_is_not_force_sync(self):
        proof = 'Sélectionner le gymnase puis cliquer sur Modifier l’Équipement.'
        self.assertTrue(workflow_fidelity_errors([c('Pour forcer la synchronisation, modifier le nom du gymnase.', proof)], 'Gymnase : synchroniser le nom ?'))
        self.assertFalse(workflow_fidelity_errors([c('Pour modifier le nom du gymnase, cliquer sur Modifier l’Équipement.',proof)], 'Gymnase : synchroniser le nom ?'))
        self.assertFalse(workflow_fidelity_errors([c('La commande de synchronisation forcée reste à confirmer.',proof)], 'Gymnase : synchroniser le nom ?'))
        self.assertTrue(workflow_fidelity_errors([c('Pour forcer la synchronisation, modifier le gymnase.', 'Le relevé ne documente pas de commande pour forcer une synchronisation.')], 'Gymnase : synchroniser le nom ?'))
        explicit='Pour forcer la synchronisation, cliquer sur [Synchroniser].'
        self.assertFalse(workflow_fidelity_errors([c(explicit,explicit)], 'Gymnase : synchroniser le nom ?'))

    def test_export_keeps_both_prerequisites_but_can_split_claims(self):
        proof = "L'export se fait seulement après validation des protocoles et après l'import des candidats dans Cyclades par le rectorat."
        bad = c('Exporter le fichier après validation des protocoles.',proof)
        self.assertTrue(workflow_fidelity_errors([bad],'Exporter les groupes vers Cyclades'))
        good = c('Les candidats doivent déjà être importés dans Cyclades.',proof,'condition')
        self.assertFalse(workflow_fidelity_errors([bad,good],'Exporter les groupes vers Cyclades'))
        self.assertFalse(workflow_fidelity_errors([bad,c('Les élèves figurent déjà dans Cyclades.',proof,'condition')],'Exporter les groupes vers Cyclades'))
        self.assertFalse(workflow_fidelity_errors([c('Les documents ne permettent pas de confirmer les préalables de cet export.',proof)],'Exporter les groupes vers Cyclades'))

    def test_class_import_does_not_skip_teacher_assignment_step(self):
        proof = Path('data/ipack/visite_college_2026_10_18/classes_actualiser_configurer_organiser_importer.txt').read_text()
        bad = c('Configuration des classes, puis importation des élèves.', proof)
        self.assertTrue(workflow_fidelity_errors([bad],'Accès restreint pour organiser et importer'))
        good = c('Ouvrir Organisation des Classes et attribuer le professeur.',proof)
        self.assertFalse(workflow_fidelity_errors([bad,good],'Accès restreint pour organiser et importer'))
        self.assertFalse(workflow_fidelity_errors([bad],'Importer un nouvel élève'))


class RemainingOneCallTests(unittest.TestCase):
    def test_valid_report_response_passes_once_and_bad_transmission_is_repaired(self):
        from documentary_review import mark_excerpt, review_exam_answer
        from test_documentary_review import FakeLLM
        proof = "Le chef d'établissement établit le rapport d'accident dans les 48 heures pour l'autorité hiérarchique."
        good = {'section':'etape','text':proof,'evidence':[{'document_id':'D1','quote':proof}]}
        bad = {**good,'text':'Le délai exact de transmission du rapport est de 48 heures.'}
        for outputs, count in [([{'claims':[good]}],1),([{'claims':[bad]},{'claims':[good]}],2)]:
            llm=FakeLLM(outputs); audit={}
            review_exam_answer(llm, question='Accident scolaire : rapport et délai ?', public='Collège (DNB)',documents=mark_excerpt(proof), audit=audit, mode='textes')
            self.assertEqual(len(llm.prompts),count)
            self.assertFalse(audit['final_rejections'])

    def test_complete_export_response_is_accepted_once(self):
        from documentary_review import mark_excerpt, review_exam_answer
        from test_documentary_review import FakeLLM
        proof = "L'export se fait seulement après validation des protocoles et après l'import des candidats dans Cyclades par le rectorat."
        good = {'section':'condition','text':proof,'evidence':[{'document_id':'D1','quote':proof}]}
        llm=FakeLLM([{'claims':[good]}]); audit={}
        review_exam_answer(llm,question='Exporter les groupes vers Cyclades',public='Lycée Général & Techno',documents=mark_excerpt(proof),audit=audit)
        self.assertEqual(len(llm.prompts),1)
        self.assertFalse(audit['final_rejections'])
