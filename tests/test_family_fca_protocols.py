"""Famille FCA/protocoles : vraies preuves, vrai catalogue, questions contrastées sans IA."""
import json
import unittest
from pathlib import Path
import knowledge_catalog as kc
from documentary_review import source_packets,mark_excerpt,compact_model_packet

ROOT=Path('data/ipack/fiches')
def fiche(prefix):return next(ROOT.glob(prefix+'*'))
def proofs(path):
 text=Path(path).read_text()
 return [s['text']for p in source_packets(mark_excerpt(text,path=str(path)))for s in compact_model_packet(p)['passages']]

class FCAProtocolFamilyTests(unittest.TestCase):
    def titles(self,q,mode='ipack'):
        return kc.priority_titles(q,'Lycée Général & Techno',mode)
    def test_establishment_activity_limit_does_not_reset_for_each_menu(self):
        for p in [fiche('ipack_023'),fiche('correspondant_03'),fiche('ipack_237'),Path('data/ipack/situations_2026_10_17/fca_liste_academique_pas_de_depot.txt')]:
            sent='\n'.join(proofs(p))
            with self.subTest(path=str(p)):
                self.assertIn('par lycée',sent)
                self.assertNotIn("une seule épreuve d'établissement par ensemble",sent)
    def test_national_limit_is_not_marked_as_an_aix_only_rule(self):
        from source_scope import select_academy
        for path in [fiche('ipack_023'),fiche('correspondant_03'),fiche('ipack_237'),Path('data/ipack/situations_2026_10_17/fca_liste_academique_pas_de_depot.txt')]:
            packets=source_packets(mark_excerpt(path.read_text(),path=str(path)))
            selected,_=select_academy(packets,'Lyon')
            rule=next(s for p in selected for s in p['passages'] if s['text'].startswith('Cadre national — bac GT'))
            self.assertEqual(rule['scope']['nature'],['texte_national'])
            self.assertNotIn('not_confirmed_for',rule['scope'])
    def test_academic_and_speciality_exceptions_survive_same_visibility_source(self):
        sent='\n'.join(proofs(fiche('ipack_070')))
        self.assertIn("ne valent pas obligation de dépôt pour une APSA académique",sent)
        self.assertIn("Pour l'EPPCS, la case Certificative ne s'applique pas",sent)
    def test_submission_is_distinct_from_validation(self):
        spans=proofs(fiche('ipack_075'))
        result=next(s for s in spans if 'Résultat — dossier soumis' in s)
        self.assertIn('pas dossier validé',result)
        self.assertIn('ne corrige pas automatiquement',result)
    def test_adapted_creation_restriction_is_kept_with_extracted_situation(self):
        from test_documentation import app_functions
        split=app_functions()['decouper_en_fiches']
        files=[fiche('ipack_160'),fiche('ipack_212'),Path('data/examens/complement_cyclades_protocoles_cas_enseignant.txt'),Path('data/ipack/complement_cyclades_cas_pratiques.txt'),Path('data/examens/tutoriels_creteil_cyclades_santorin.txt'),Path('data/examens/videos_tutoriels_cyclades_santorin.txt')]
        examined=0
        for path in files:
            chunks=split(path.read_text())
            for chunk in chunks:
                if 'Branche technique Aix-Marseille' in chunk:
                    examined+=1
                    sent='\n'.join(proofs_text(chunk,path))
                    with self.subTest(path=str(path)):
                        self.assertIn('extraction iPack IA-IPR',sent)
                        self.assertIn('ne vaut pas pour le CAP',sent)
                        self.assertIn('ne change pas les possibilités réglementaires',sent)
        self.assertGreaterEqual(examined,6)
    def test_cyclades_wrong_group_is_not_expanded_to_santorin_lot(self):
        question='Supprimer un protocole dans Cyclades avec un mauvais groupe élève ?'
        self.assertNotIn('eleve dans le mauvais lot',kc.enrich(question))
        titles=self.titles(question)
        self.assertIn("FAQ EPS — Protocole Cyclades avec le mauvais groupe d'élèves",titles)
        self.assertFalse(any('SUPPRIMER UN PROTOCOLE DANS iPackEPS' in s for s in titles))
        self.assertFalse(any('mauvais lot' in s for s in titles))
    def test_real_santorin_wrong_group_keeps_lot_help(self):
        self.assertIn('eleve dans le mauvais lot',kc.enrich("Santorin : un élève est dans le mauvais groupe"))
        self.assertTrue(any('mauvais lot' in s for s in self.titles('Santorin : un élève est dans le mauvais lot','examens')))
    def test_refused_reference_selects_repair_not_late_protocol(self):
        for q in ['Comment remplacer un référentiel refusé ?',"Mon référentiel est rejeté : comment corriger le dépôt ?"]:
            titles=self.titles(q)
            self.assertTrue(any("Rejet d'un référentiel" in t for t in titles),titles)
        self.assertFalse(any("Rejet d'un référentiel" in t for t in self.titles('Où consulter le référentiel académique ?')))
    def test_submission_with_alert_is_not_a_cyclades_deletion(self):
        titles=self.titles('Puis-je soumettre mon dossier malgré une alerte de date ?')
        self.assertTrue(any('Proposer le Dossier' in t for t in titles),titles)
        self.assertFalse(any('SUPPRIMER' in t for t in titles))

def proofs_text(text,path):
    return [s['text']for p in source_packets(mark_excerpt(text,path=str(path)))for s in compact_model_packet(p)['passages']]
