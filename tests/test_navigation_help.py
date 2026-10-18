import unittest
from unittest.mock import patch
from pathlib import Path
from navigation_help import offer_navigation_help, documented_navigation_help, CLARIFICATION


class NavigationHelpTests(unittest.TestCase):
    def test_only_specific_college_technical_clarification_offers_help(self):
        self.assertTrue(offer_navigation_help('ipack', 'Collège (DNB)', 'clarification', CLARIFICATION))
        for args in (('textes','Collège (DNB)','clarification',CLARIFICATION),
                     ('examens','Collège (DNB)','clarification',CLARIFICATION),
                     ('ipack','Lycée Général & Techno','clarification',CLARIFICATION),
                     ('ipack','Collège (DNB)','ia',CLARIFICATION),
                     ('ipack','Collège (DNB)','clarification','Précisez le diplôme.'),
                     ('ipack','Collège (DNB)','documentee','Chemin connu')):
            self.assertFalse(offer_navigation_help(*args))

    def test_content_comes_from_documented_order_without_exam_procedure(self):
        body = documented_navigation_help()
        self.assertIn('Établissement', body)
        self.assertIn('Ma Fiche Professeur', body)
        self.assertIn('Dossier EPS', body)
        self.assertEqual(body.count('<li>'), 3)
        self.assertIn('Source du parcours', body)
        self.assertNotIn('certificative', body)
        self.assertNotIn('rattrapage', body)

    def test_missing_source_has_no_invented_fallback(self):
        with patch('navigation_help.SOURCE', Path('/nonexistent/guide.txt')):
            self.assertEqual(documented_navigation_help(), '')
