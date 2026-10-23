import unittest
from document_selector import profile,question_excerpt

class SelectorLongLineTests(unittest.TestCase):
    def test_late_relevant_sentence_is_visible_without_increasing_budget(self):
        text=('Présentation générale du dossier. '*20)+'Pour modifier les archives, une autorisation spécifique est nécessaire.'
        result=question_excerpt(text,'Comment modifier les archives ?',150)
        self.assertIn('autorisation spécifique',result)
        self.assertLessEqual(len(result),150)
        self.assertTrue(result.startswith('…'))
    def test_card_exposes_late_condition_and_keeps_full_source(self):
        text=('Description générale du dossier. '*25)+'Si le lot est fermé, demander son ouverture à la direction.'
        packet={'id':'D1','title':'Accès','text':text}
        card=profile(packet,'Mon lot est fermé : comment demander son ouverture ?')
        self.assertIn('direction',card['demande_proche_extrait'])
        self.assertTrue(any('direction' in c for c in card['conditions_extraits']))
        self.assertEqual(packet['text'],text)
        self.assertTrue(card['description_partielle'])
    def test_short_description_unchanged(self):
        self.assertEqual(question_excerpt('Si le dossier est ouvert, enregistrer.','Dossier',150),'Si le dossier est ouvert, enregistrer.')
    def test_no_matching_late_text_does_not_create_facts(self):
        result=question_excerpt('Introduction générale. '*30,'Motintrouvable',150)
        self.assertLessEqual(len(result),150)
        self.assertNotIn('Motintrouvable',result)
        self.assertTrue(result.endswith('…'))

    def test_decimal_is_not_treated_as_sentence_boundary(self):
        text=('Présentation générale du dossier. '*20)+'Pour modifier la note, saisir 6.5 points dans le champ.'
        result=question_excerpt(text,'Comment modifier la note dans le champ ?',150)
        self.assertIn('6.5 points',result)
