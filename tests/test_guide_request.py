import unittest
from guide_request import requests_guide
class RequestTests(unittest.TestCase):
    def test_generic_help(self):
        for q in ['aide moi je suis perdu', 'Je suis perdue dans iPackEPS', 'Je ne sais pas par où commencer', 'aidez-moi svp', 'aide-moi']:
            for p in ['Collège','Lycée Général & Techno','Lycée Pro / CAP']:
                self.assertTrue(requests_guide(q,'ipack',p),q)
    def test_concrete_or_other_context(self):
        for q in ['J’ai perdu mes classes', 'je suis perdu comment importer mes élèves', 'Qui modifie la liste des enseignants ?', 'ma vidéo est perdue']:
            self.assertFalse(requests_guide(q,'ipack','Collège'),q)
        for mode in ['textes','examens']:
            self.assertFalse(requests_guide('aide moi je suis perdu',mode,'Collège'))
        self.assertFalse(requests_guide('je suis perdu','ipack','1er degré'))
