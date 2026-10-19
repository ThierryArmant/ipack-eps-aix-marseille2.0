import unittest
from termes_definis import mark_exceptionnel


class TermesDefinisTests(unittest.TestCase):
    def test_transport_surligne_et_definit_une_fois(self):
        out = mark_exceptionnel('<p>À titre exceptionnel, le chef peut autoriser. Mesure exceptionnelle.</p>', 'puis-je louer un minibus ?')
        self.assertEqual(out.count('class="terme-defini"'), 2)
        self.assertEqual(out.count('terme-defini-note'), 1)
        self.assertIn('86-101', out)

    def test_hors_transport_inchange(self):
        body = '<p>Circonstances exceptionnelles : épreuve différée.</p>'
        self.assertEqual(mark_exceptionnel(body, 'inaptitude au CCF'), body)

    def test_attributs_html_non_modifies(self):
        out = mark_exceptionnel('<p title="exceptionnel">exceptionnel</p>', 'voiture personnelle')
        self.assertIn('<p title="exceptionnel">', out)
