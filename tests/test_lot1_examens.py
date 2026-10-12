import unittest
import knowledge_catalog as kc
class Lot1(unittest.TestCase):
 def answer(self,q,public='Lycée Général & Techno'):
  return kc.documented_response(q,public,'examens')[0]
 def test_pro_does_not_import_gt_obligations_or_accept_unlimited_authority(self):
  a=self.answer('En bac pro, faut-il deux professeurs pour évaluer un CCF EPS ? Un collègue dit que tout se décide seul.','Lycée Pro / CAP')
  self.assertIn('ne sont pas obligatoires',a);self.assertIn('ne signifie pas',a)
 def test_third_activity_overrides_general_absence_reply(self):
  a=self.answer('Le professeur de la classe est absent sans remplaçant : troisième activité impossible pour toute la classe, DI ?')
  self.assertIn('Déclarer CE',a);self.assertIn('avant l’accord',a)
 def test_medical_does_not_trigger_collective_ce(self):
  a=self.answer('Élève inapte à la troisième activité : que saisir ?')
  self.assertNotIn('Déclarer CE',a)
 def test_distribution_keeps_pdf_and_preserves_notes(self):
  a=self.answer('Santorin ne trouve pas d’examinateur correspondant au mail déclaré lors de la distribution.')
  self.assertIn('PDF',a);self.assertIn('ne supprimez pas',a)
 def test_missing_candidates_does_not_require_automatic_100_percent(self):
  a=self.answer('Des élèves inscrits manquent dans Santorin après la distribution.')
  self.assertIn('rejouer l’import',a);self.assertIn('Il n’est pas nécessaire',a)
 def test_non_eps_grading_does_not_trigger_software_reply(self):
  a=self.answer('Il manque deux élèves en cours EPS, comment préparer le prochain cours ?')
  self.assertNotIn('rejouer l’import',a)
