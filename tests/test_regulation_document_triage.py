"""Régressions documentaires : séparation des régimes et des publics, sans génération."""
import json
from pathlib import Path
import unittest
import knowledge_catalog as kc
import test_documentation as documentation

class RegulationDocumentTriageTests(unittest.TestCase):
    def test_adult_workplace_does_not_change_primary_pupil_context(self):
        q='En CM1, un parent professeur EPS dans un autre collège intervient bénévolement : agrément ?'
        self.assertEqual(kc.effective_context(q,'1er degré','textes'),('1er degré','textes'))
        body=kc.priority_context(q,'1er degré','textes')
        self.assertIn('1.b',body)
        self.assertIn('autoriser préalablement',body)

    def test_mixed_grades_preserve_selected_public(self):
        q='CM2 et élèves de sixième, sortie commune cycle 3'
        self.assertEqual(kc.effective_context(q,'1er degré','textes'),('1er degré','textes'))
        self.assertIn('tranche de quinze',kc.priority_context(q,'1er degré','textes'))
        self.assertEqual(kc.documented_response(q,'1er degré','textes')[0],'')

    def test_secondary_group_does_not_receive_primary_numerical_table(self):
        body=kc.priority_context('Voyage de 52 collégiens trois nuits : taux encadrement ?', 'Collège (DNB)','textes')
        self.assertIn('pas de ratio national',body)
        self.assertNotIn('tranche de quinze',body)
        self.assertNotIn('quatre adultes',body)

    def test_alert_and_equality_are_separate_sources(self):
        cat=kc.catalog()
        equality=next(p for p in cat if 'base_textes_officiels_038_' in p)
        self.assertNotIn('satellite',Path(equality).read_text())
        body=kc.priority_context('VTT en milieu isolé : téléphone satellite et alerte ?', 'Collège (DNB)','textes')
        self.assertIn('100683',body)
        self.assertNotIn('ANCRAGE CONSTITUTIONNEL',body)

    def test_related_safety_documents_all_reach_generation_priority(self):
        route=documentation.DocumentationTests();route.setUp()
        text,_,_,error=route.route('Escalade en grande voie avec relais et accident : contrôles et déclaration ?', 'Collège (DNB)','textes')
        self.assertFalse(error)
        for title in ('environnement spécifique','contrôles du professeur','rapport et communication'):
            self.assertIn(title,text)

    def test_new_fiches_are_sourced_and_have_no_direct_responses(self):
        c=kc.catalog()
        for stem in ('appn_moyens_alerte','escalade_relais','intervenants_eps_ecole','sorties_mixte_cycle3'):
            p=next(p for p in c if stem in p)
            self.assertIn('https://',Path(p).read_text())
            self.assertNotIn('reponse_directe',c[p])

    def test_borrowed_bicycle_damage_reaches_responsibility_without_outing_keyword(self):
        body = kc.priority_context(
            'Un vélo emprunté se casse en cours : responsabilité et vérifications ?',
            'Collège (DNB)', 'textes')
        self.assertIn('défauts décelables', body)
        self.assertIn('lien causal', body)
        self.assertIn('MENE0401637C', body)
        unrelated = kc.priority_context('Un élève casse une vitre : responsabilité ?',
                                        'Collège (DNB)', 'textes')
        self.assertNotIn('Sortie au musée à vélo', unrelated)

    def test_specific_climbing_packet_contains_checks_not_only_project_authorisation(self):
        from documentary_review import mark_excerpt, source_packets
        path = 'data/textes/fiches/escalade_relais_environnement_specifique.txt'
        packet = source_packets(mark_excerpt(Path(path).read_text(), path=path))[0]
        controls = [s['text'] for s in packet['passages'] if s['text'].startswith('Contrôles')]
        self.assertEqual(len(controls), 2)
        self.assertIn('supervise', controls[0])
        self.assertIn('visuelle et tactile', controls[1])
        self.assertIn('ne décrivent pas', controls[1])
