"""Accès multi-établissements et liste élèves : procédures voisines, sans IA distante."""
import unittest
import knowledge_catalog as kc
from documentary_review import context_document_mismatch, mark_excerpt, review_exam_answer
import test_documentation as routing
from test_documentary_review import FakeLLM
from pathlib import Path

MULTI='data/ipack/fiches/ipack_222_situation_enseignants_tzr_ou_partages_multi_etablissements.txt'
ORS='data/textes/complement_obligations_service_eps.txt'
ROSTER='data/ipack/situations_2026_10_17/eleve_absent_liste_ajout.txt'

class AccessRosterNeighbours(unittest.TestCase):
    def setUp(self):
        self.h=routing.DocumentationTests();self.h.setUp()
    def route(self,q,public='Lycée Pro / CAP',mode='ipack'):
        return self.h.route(q,public,mode)[0]
    def test_lost_access_without_software_name_is_not_service_rule(self):
        for q in ['Deux établissements (LP et LGT) : je n’ai plus accès au LGT, seulement au LP. Pourquoi ?',
                  'Je travaille sur plusieurs collèges et mon accès au second est bloqué.',
                  'Mon autre lycée n’est plus accessible : j’ai perdu mon accès à cet établissement.']:
            with self.subTest(q=q):
                text=self.route(q)
                self.assertIn(MULTI,text)
                self.assertNotIn(ORS,text)
                self.assertIn('Changer d’Établissement',text)
        self.assertIn(ORS,self.route('Service partagé dans deux établissements : ai-je une heure de réduction ?', mode='textes'))
    def test_access_filter_removes_vector_service_source_before_llm(self):
        q='Mon accès au second lycée est bloqué : je peux encore entrer dans le premier.'
        wrong=mark_excerpt(Path(ORS).read_text(),path=ORS,title='Obligations de service')
        right=mark_excerpt(Path(MULTI).read_text(),path=MULTI,title='Accès multi-établissements')
        llm=FakeLLM([{'claims':[]}]);audit={}
        review_exam_answer(llm,question=q,public='Lycée Pro / CAP',mode='ipack',documents=wrong+'\n'+right,audit=audit)
        self.assertIn('D1',audit['excluded_situation_documents'])
        self.assertNotIn('D2',audit['excluded_situation_documents'])
        self.assertFalse(context_document_mismatch(q+' Mes ORS changent-elles aussi ?', 'Lycée Pro / CAP','ipack',{'path':ORS,'title':'Obligations de service'}))
    def test_roster_covers_departures_as_well_as_arrivals(self):
        for q in ['Des élèves ont quitté le lycée et de nouveaux sont arrivés : comment mettre à jour la base élèves ?',
                  'Des élèves partis restent dans le listing iPackEPS : comment actualiser ?',
                  'Comment ajouter un élève arrivé dans ma classe ?']:
            with self.subTest(q=q):
                text=self.route(q,'Lycée Général & Techno')
                self.assertIn(ROSTER,text)
                self.assertIn('Pour les départs',text)
                self.assertIn('[Importer]',text)
                self.assertIn('ne décrit pas le mécanisme de suppression',text)
                self.assertNotIn('cyclades_candidats_absents.txt',text)
    def test_exam_departure_keeps_its_own_circuit(self):
        paths=[p for p,_ in kc.reference_notice({'gt'},'Un élève a quitté le lycée : le retirer du lot Santorin ?', 'Lycée Général & Techno')]
        self.assertNotIn(ROSTER,paths)
    def test_article18_does_not_give_two_current_button_names(self):
        text=Path('data/ipack/fiches/ipack_065_article_18_dossiers_dossiereps_eleves_placement_des_eleves_dans_les_groupes.txt').read_text()
        self.assertNotIn('menu [importation élèves] => [Actualiser]',text)
        self.assertIn('menu [Importation des Élèves] => [Importer]',text)
