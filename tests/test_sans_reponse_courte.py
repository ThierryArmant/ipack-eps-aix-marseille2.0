import unittest

from exact_source_answer import without_short_answer, media_text

EXTRAITS = '<h3>Réponse</h3><p>1. Passage voisin sur le portail. <sup>[1]</sup></p>'


class SansReponseCourteTest(unittest.TestCase):
    def test_aucune_phrase_retenue_dit_qu_il_ne_sait_pas(self):
        audit = {'short_answer': {'status': 'nothing_kept'}, 'exact_extracts': {}}
        out = without_short_answer(EXTRAITS, audit, 'ipack')
        self.assertIn('Je n’ai pas trouvé', out)
        self.assertIn('correspondant académique iPackEPS', out)
        self.assertIn('<details><summary>Passages proches', out)  # replié
        self.assertEqual(out.count('<h3>Réponse</h3>'), 1)
        self.assertIn('Passage voisin', out)

    def test_panne_du_redacteur_garde_les_extraits_ouverts(self):
        audit = {'short_answer': {'status': 'invalid_no_retry'}, 'exact_extracts': {}}
        out = without_short_answer(EXTRAITS, audit, 'examens')
        self.assertIn('n’a pas pu être rédigée', out)
        self.assertIn('<details open>', out)
        self.assertNotIn('Je n’ai pas trouvé', out)

    def test_contact_selon_onglet(self):
        audit = {'short_answer': {'status': 'nothing_kept'}, 'exact_extracts': {}}
        self.assertIn('service des examens', without_short_answer(EXTRAITS, audit, 'examens'))
        self.assertIn('inspection EPS', without_short_answer(EXTRAITS, audit, 'textes'))

    def test_pas_de_video_sans_reponse(self):
        audit = {'exact_extracts': {'display_version': 'exact-focus-v1', 'no_short_answer_display': 'nothing_kept',
                                    'focused_passage_ids': ['D1P1'],
                                    'selected_sources': [{'passages': [{'id': 'D1P1', 'text': 'vidéo'}]}]}}
        self.assertEqual(media_text(audit, 'repli'), '')


if __name__ == '__main__':
    unittest.main()
