"""Contrôles de périmètre : erreurs voisines et garanties conservées."""
import unittest
from documentary_review import (situation_mismatch, conditional_extraction_errors,
                                metadata_scope_notice, render_claims)
from claim_guards import unsupported_certainty


class GuardApplicabilityTests(unittest.TestCase):
    def test_student_data_is_not_a_personal_specialty_request(self):
        source = "La reconduction concerne les données d'établissement et la fiche professeur."
        self.assertFalse(situation_mismatch("Où archiver les données de mes élèves ?", source))
        self.assertTrue(situation_mismatch("J'enseigne le tennis avec mes élèves.",
                                          "Déclarer ma spécialité sportive dans ma fiche professeur."))

    def test_storage_and_data_entry_are_not_certification_choices(self):
        for source, text in [
            ("Aucune note ne se saisit ni ne se conserve ici.", "Il n'y a pas de conservation des notes."),
            ("RÈGLE ABSOLUE : ON NE SAISIT AUCUNE NOTE DANS CET OUTIL.", "Aucune note ne peut être saisie ici."),
            ("Si les notes sont archivées, choisir le fichier de sauvegarde.", "Conserver les notes dans le fichier.")]:
            claim = {'section': 'decision', 'text': text, 'evidence': [{'quote': source}]}
            self.assertFalse(conditional_extraction_errors([claim], 'Où enregistrer mes données ?'))

    def test_conditional_certification_remains_guarded(self):
        source = "Si les éléments d'appréciation sont suffisants, une certification sur une seule note peut être retenue."
        claim = {'section': 'decision', 'text': 'Sa note sera conservée pour le baccalauréat.',
                 'evidence': [{'quote': source}]}
        self.assertTrue(conditional_extraction_errors([claim], 'Une seule épreuve passée : quel résultat ?'))

    def test_negative_permissions_are_not_proved_by_documentary_silence(self):
        proof = ["Aucune règle écrite n'a été retrouvée. Faire confirmer par le service compétent."]
        self.assertTrue(unsupported_certainty("Le candidat ne peut pas être accueilli.", proof))
        self.assertTrue(unsupported_certainty("Le candidat ne peut pas être accueilli.", proof + ["Aucune règle écrite trouvée ; faire confirmer par le service."]))
        self.assertFalse(unsupported_certainty("Le corpus ne permet pas de confirmer cette interdiction.", proof))
        self.assertFalse(unsupported_certainty("Le candidat ne peut pas être accueilli.",
                                              ["Le candidat ne peut pas être accueilli sans convocation."]))

    def test_scope_notice_requires_verified_metadata_and_no_business_rule(self):
        evidence = [{'scope': {'academy': 'Aix-Marseille', 'not_confirmed_for': 'Créteil'}}]
        notice = "Les consignes de l'académie d'Aix-Marseille concernant les certificats médicaux ne sont pas confirmées pour l'académie de Créteil."
        self.assertTrue(metadata_scope_notice(notice, evidence))
        self.assertFalse(metadata_scope_notice(notice.replace('Créteil', 'Lyon'), evidence))
        self.assertFalse(metadata_scope_notice(notice, [{'scope': {}}]))
        self.assertFalse(metadata_scope_notice(notice + ' Le formulaire est obligatoire.', evidence))

    def test_foreign_academic_rule_is_attributed_in_its_sentence(self):
        evidence = [{'document_id': 'D1', 'scope': {'nature': ['consigne_academique'],
                    'academy': 'Aix-Marseille', 'not_confirmed_for': 'Créteil'}}]
        claim = {'section': 'condition', 'text': 'Le document doit utiliser le formulaire local.', 'evidence': evidence}
        packets = [{'id': 'D1', 'path': '', 'url': '', 'title': 'Procédure locale', 'display_level': 'academique'}]
        rendered = render_claims([claim], packets)
        self.assertIn('À Aix-Marseille, Le document', rendered)
        self.assertIn('service des examens de l’académie de Créteil', rendered)
        evidence[0]['scope'] = {'nature': ['logiciel']}
        self.assertNotIn('À Aix-Marseille', render_claims([claim], packets))
