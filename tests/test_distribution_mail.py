import unittest
import knowledge_catalog as kc
class DistributionMail(unittest.TestCase):
 def test_mail_error_gets_address_correction_not_restart(self):
  for public in ['Lycée Général & Techno','Lycée Pro / CAP']:
   for mode in ['examens','ipack']:
    a,m=kc.documented_response('La distribution des lots affiche une erreur avec des adresses mail',public,mode)
    self.assertIn('mail déclaré',m['title']);self.assertIn('Contrôler / réaffecter',a);self.assertNotIn('Oui, la distribution peut être recommencée',a)
 def test_restart_still_preserves_existing_grades(self):
  a,m=kc.documented_response('Erreur de distribution : supprimer et recommencer ?','Lycée Général & Techno','examens')
  self.assertIn('FAQ EPS I2',m['title']);self.assertIn('Si des notes existent, ne pas supprimer',a)
