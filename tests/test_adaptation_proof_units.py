"""Vraie fiche 212, annotations et perte de modalités ; aucun appel fournisseur."""
import unittest
from pathlib import Path
from documentary_review import source_packets,mark_excerpt,compact_model_packet
from evidence_logic import evidence_logic_errors
PATH='data/ipack/fiches/ipack_212_situation_interdiction_d_improviser_un_controle_adapte_fca_a_la_volee.txt'
def spans():
    return [s for p in source_packets(mark_excerpt(Path(PATH).read_text(),path=PATH))for s in p['passages']]
def c(text,proof):return {'text':text,'evidence':[{'quote':proof}]}
class AdaptationProofUnitsTests(unittest.TestCase):
    def test_creation_proof_keeps_its_condition_after_attribution(self):
        ps=spans();unit=next(s for s in ps if 'crée au besoin' in s['text'])
        self.assertTrue(unit['text'].startswith('Branche — inaptitude partielle temporaire :'))
        self.assertIn('selon la configuration acceptée et le circuit applicable',unit['text'])
        self.assertIn("n'est pas une étape obligatoire",unit['text'])
        self.assertEqual(unit['scope']['nature'],['logiciel'])
        self.assertFalse(any(s['text'].lstrip().startswith('Pas de nouvelle validation :')for s in ps))
    def test_medical_and_software_proofs_are_distinct_and_complete(self):
        ps=spans();medical=next(s for s in ps if 'sans nouvelle validation préalable' in s['text'])
        self.assertTrue(medical['text'].startswith('Branche — inaptitude partielle temporaire :'))
        self.assertEqual(medical['scope']['nature'],['texte_national'])
        self.assertTrue(any(s['text'].startswith('Branche — inaptitude temporaire :') for s in ps))
    def test_exact_unqualified_creation_and_categorical_necessity_are_detected(self):
        proof=next(s['text']for s in spans()if 'crée au besoin' in s['text'])
        for bad in ["L'enseignant doit créer le protocole adapté dans Cyclades, sans modifier les protocoles standards déjà validés.","Pour une inaptitude partielle temporaire, il est nécessaire de créer le protocole adapté dans Cyclades."]:
            self.assertTrue(evidence_logic_errors([c(bad,proof)]))
        good="Pour une inaptitude partielle temporaire, le chef d'établissement ou un enseignant peut créer au besoin le protocole adapté selon le circuit applicable."
        self.assertFalse(evidence_logic_errors([c(good,proof)]))
    def test_actual_date_inversion_is_not_rescued_by_after_at_end(self):
        proof=next(s['text']for s in spans()if s['text'].startswith('Branche — inaptitude partielle temporaire après la date butoir :'))
        bad="La création d'un protocole adapté dans iPackEPS avant la date butoir fixée par la CAHPN ne sera pas transférée vers Cyclades après cette date."
        self.assertTrue(evidence_logic_errors([c(bad,proof)]))
        good="Pour une inaptitude partielle temporaire, après la date butoir, un protocole adapté créé dans iPackEPS ne sera pas transféré par le circuit ordinaire."
        self.assertFalse(evidence_logic_errors([c(good,proof)]))
    def test_other_temporal_conditions_and_optional_actions(self):
        for subject in ['dossier','contrat','fichier']:
            proof=f'Branche — après la date limite : le {subject} ne sera pas accepté.'
            self.assertTrue(evidence_logic_errors([c(f'Avant la date limite, le {subject} ne sera pas accepté après cette date.',proof)]))
            self.assertFalse(evidence_logic_errors([c(f'Après la date limite, le {subject} ne sera pas accepté.',proof)]))
        proof='Le responsable vérifie au besoin les pièces.'
        self.assertTrue(evidence_logic_errors([c('Le responsable doit vérifier les pièces.',proof)]))
        self.assertFalse(evidence_logic_errors([c('Si nécessaire, le responsable doit vérifier les pièces.',proof)]))
    def test_cited_units_are_exact_source_substrings(self):
        text=Path(PATH).read_text()
        for s in spans():self.assertEqual(s['text'],text[s['start']:s['end']])
