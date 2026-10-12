import unittest
import knowledge_catalog as kc
class DistributionMail(unittest.TestCase):
 def test_mail_error_gets_address_correction_not_restart(self):
  for public in ['Lycée Général & Techno','Lycée Pro / CAP']:
   for mode in ['examens','ipack']:
    q='La distribution des lots affiche une erreur avec des adresses mail'
    a=kc.delivered_text(q,public,mode); t=kc.priority_titles(q,public,mode)
    self.assertTrue(any('mail déclaré' in x for x in t));self.assertIn('Contrôler / réaffecter',a);self.assertNotIn('FAQ EPS — Distribution',t)
 def test_restart_still_preserves_existing_grades(self):
  q='Erreur de distribution : supprimer et recommencer ?'
  a=kc.delivered_text(q,'Lycée Général & Techno','examens')
  self.assertIn('FAQ EPS — Distribution',kc.priority_titles(q,'Lycée Général & Techno','examens'));self.assertIn('Si des notes existent, ne pas supprimer',a)
