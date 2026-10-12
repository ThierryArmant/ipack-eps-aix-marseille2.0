import unittest
import knowledge_catalog as kc
class Lot3(unittest.TestCase):
 def answer(self,q,public='Lycée Général & Techno'):
  return kc.documented_response(q,public,'examens')[0]
 def test_temporary_adaptation_is_information_not_validation(self):
  a=self.answer('Entorse de cheville : badminton adapté, protocole validé par commission avant évaluation ?')
  self.assertIn('pour information',a);self.assertIn('nouvelle validation',a)
 def test_collective_closure_does_not_force_new_lot(self):
  a=self.answer('Piscine fermée pour toute la classe : natation non évaluée, Santorin ?')
  self.assertIn('Ne pas imposer',a);self.assertIn('référent habilité',a)
 def test_one_candidate_does_not_get_collective_closure(self):
  a=self.answer('Seul un élève arrivé après la fermeture de piscine non évalué : CE sur le lot ?')
  self.assertIn('Non : ne pas déclarer le CE',a)
 def test_addition_is_local_not_national_invalidation_ban(self):
  a=self.answer('Ajouter un protocole standard après validation : demander une invalidation ?')
  self.assertIn('Strasbourg et Créteil',a);self.assertIn('protocole adapté',a)
 def test_normal_programming_does_not_get_temporary_medical_reply(self):
  a=self.answer('Quel protocole de badminton adapté annuel déposer pour validation ?')
  self.assertNotIn('comme l’entorse décrite',a)
