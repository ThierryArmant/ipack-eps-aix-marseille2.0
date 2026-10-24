"""Déformations explicites et contre-exemples, sans décision métier codée."""
import unittest
from claim_guards import evidence_relation_errors, unsupported_certainty

def claim(text, proof):
    return {'section':'decision','text':text,'evidence':[{'quote':proof}]}

class ExplicitPolarityTests(unittest.TestCase):
    def test_normal_conclusion_cannot_invert_anomaly_on_same_subject(self):
        proof="Des référentiels ou protocoles réclamés à un collège ne sont pas une exigence normale du collège."
        bad="Il est normal que le logiciel réclame des référentiels et des protocoles, car ils ne sont pas requis au collège."
        self.assertTrue(evidence_relation_errors([claim(bad,proof)], 'Cette demande est-elle normale ?'))
        self.assertFalse(evidence_relation_errors([claim("Cette demande de référentiels et protocoles n'est pas normale au collège.",proof)],''))
        self.assertFalse(evidence_relation_errors([claim("Il est normal que le logiciel ne réclame pas de référentiels au collège.",proof)],''))

    def test_other_domain_and_unrelated_anomaly(self):
        proof="Des justificatifs réclamés pour cette consultation ne sont pas une exigence normale de la consultation."
        self.assertTrue(evidence_relation_errors([claim('Il est normal de réclamer ces justificatifs pour cette consultation.',proof)],''))
        self.assertFalse(evidence_relation_errors([claim('Il est normal de vérifier les lots avant transmission.',proof)],''))

    def test_unmentioned_case_is_not_excluded_by_a_list_of_examples(self):
        proof="Les documents modèles peuvent être distincts pour une ouverture, un projet ou un bilan."
        self.assertTrue(evidence_relation_errors([claim("Cette possibilité ne s'applique pas à la reconduction.",proof)],''))
        self.assertFalse(evidence_relation_errors([claim("Cette possibilité ne s'applique pas à la reconduction.",proof+' La reconduction est exclue de ce dispositif.')],''))
        self.assertFalse(evidence_relation_errors([claim("Cette possibilité ne s'applique pas à la reconduction.","Cette fonction s'applique uniquement au bilan.")],''))
        self.assertFalse(evidence_relation_errors([claim("Le dépôt pour la reconduction reste à vérifier.",proof)],''))

    def test_passive_verification_is_not_authorization_but_neighbor_obligation_is(self):
        proof="Ce passage ne suffit pas à confirmer la possibilité de déposer les pièces complémentaires dans ce module. Le mode de transmission reste à vérifier auprès de l'inspection."
        self.assertFalse(unsupported_certainty("Les pièces complémentaires doivent être vérifiées auprès de l'inspection qui les demande.",[proof]))
        self.assertTrue(unsupported_certainty("Les pièces complémentaires doivent être vérifiées auprès de l'inspection. Les pièces complémentaires doivent être déposées dans ce module.",[proof]))
