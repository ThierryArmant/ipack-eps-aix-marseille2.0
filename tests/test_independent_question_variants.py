"""Questions inédites et contre-exemples : vrai raccordement, sans recherche vectorielle ni IA."""
import unittest
import knowledge_catalog as kc

class IndependentQuestionVariantsTests(unittest.TestCase):
    def selected(self,q,public='Collège (DNB)',mode='ipack'):
        return kc.priority_titles(q,public,mode)
    def test_two_colleges_and_two_lycees_can_select_existing_multi_site_fiche(self):
        expected='[SITUATION: ENSEIGNANTS TZR OU PARTAGÉS (MULTI-ÉTABLISSEMENTS)]'
        for q in ["Je travaille dans deux collèges : comment choisir le second établissement ?",
                  "J'enseigne dans deux lycées, comment basculer vers l'autre ?"]:
            self.assertIn(expected,self.selected(q))
        for q in ["Comment créer deux groupes dans mon collège ?","Je change d'établissement après ma mutation."]:
            self.assertNotIn(expected,self.selected(q))
    def test_one_student_asns_gets_individual_source(self):
        expected='[ARTICLE 50] [Mes Élèves]/[Visualisation]/[ASNS] Validation et Impression de l’ASNS'
        self.assertIn(expected,self.selected("Comment imprimer une attestation ASNS pour un seul élève ?"))
        self.assertNotIn(expected,self.selected("Comment imprimer les attestations ASNS en série dans le dossier natation ?"))
    def test_manual_association_does_not_reuse_it_for_apsa_or_cfa(self):
        expected="Réponses du correspondant examens EPS : association des candidats, Cyclades, IMAG'IN, Santorin"
        q='Comment associer manuellement les élèves à leur protocole Cyclades ?'
        self.assertIn(expected,self.selected(q,'Lycée Général & Techno','examens'))
        for q in ['Comment associer les APSA aux groupes dans iPackEPS ?',
                  'CFA hors SIECLE : comment associer les candidats dans Cyclades au protocole ?']:
            self.assertNotIn(expected,self.selected(q,'Lycée Général & Techno','examens'))
    def test_establishment_branch_is_not_lost_in_other_active_fca_copy(self):
        from documentary_review import source_packets,mark_excerpt
        from pathlib import Path
        path='data/ipack/fiches/ipack_023_situation_non_certification_d_une_apsa_ex_cross_training.txt'
        proofs='\n'.join(s['text']for p in source_packets(mark_excerpt(Path(path).read_text(),path=path))for s in p['passages'])
        self.assertIn("n'est pas, pour ce seul motif, interdite de dépôt",proofs)
        self.assertIn("ne vaut ni accord de l'inspection",proofs)
