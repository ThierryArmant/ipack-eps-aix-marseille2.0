import unittest
import knowledge_catalog as kc
class Lot2(unittest.TestCase):
 def answer(self,q,public='Lycée Général & Techno'):
  return kc.documented_response(q,public,'examens')
 def test_inscription_inapte_is_apte_and_not_annual_condition(self):
  a,_=self.answer('À l’inscription au bac je coche Inapte EPS avec un certificat total ?')
  self.assertIn('cochez « APTE »',a);self.assertIn('Ne pas imposer',a)
 def test_inscription_does_not_capture_ponctuel(self):
  a,m=self.answer('Candidat individuel au bac : inscription inapte EPS au ponctuel ?')
  self.assertNotIn('inscription APTE',m.get('title',''))
 def test_software_precaution_is_not_law_or_impossibility(self):
  a,_=self.answer('Cyclades : deux onglets pour le bac pro et le CAP ?','Lycée Pro / CAP')
  self.assertIn('précaution technique',a);self.assertIn('impossibilité technique',a)
 def test_access_does_not_include_unrequested_calculation(self):
  a,_=self.answer('À Aix-Marseille, par où je passe pour saisir mes notes EPS ?')
  self.assertIn('Portail d’accès aux missions',a);self.assertIn('une ligne par examen',a)
 def test_calendar_is_protocol_not_general_evaluation_project(self):
  a,_=self.answer('Le rattrapage doit-il être juste après chaque CCF ou en fin d’année ?')
  self.assertIn('protocole certificatif',a);self.assertIn('calendrier de la session',a)
 def test_no_justification_does_not_trigger_medical_reply(self):
  a,_=self.answer('Absent sans aucun justificatif au CCF : droit au rattrapage ?')
  self.assertIn('ne donne pas droit',a);self.assertIn('chef d’établissement',a)
