import unittest
from documentary_review import source_packets, mark_excerpt, bind_faq_context
from knowledge_catalog import priority_titles

class FAQContextTests(unittest.TestCase):
    def test_answer_keeps_exact_question_without_inventing_conditions(self):
        body='Q7 : Le bouton affiche X ; comment continuer ?\n\nR7 : Le responsable ouvre le dossier.'
        spans=source_packets(mark_excerpt(body))[0]['passages']
        self.assertEqual(len(spans),1)
        self.assertEqual(spans[0]['text'],body)
    def test_different_numbers_or_scopes_are_never_merged(self):
        body='Q1 : Question\nR2 : Réponse'
        a={'text':'Q1 : Question','start':0,'end':13,'scope':{}}
        b={'text':'R2 : Réponse','start':14,'end':len(body),'scope':{}}
        self.assertEqual(len(bind_faq_context([a,b],body)),2)
        b['text']='R1 : Réponse';b['scope']={'academy':'autre'}
        self.assertEqual(len(bind_faq_context([a,b],body)),2)
    def test_deposit_and_individual_combination_select_different_documents(self):
        q='Deux FCA de demi-fond pour des groupes différents : réunir dans un PDF ?'
        titles=priority_titles(q,'Lycée Général & Techno','examens')
        self.assertTrue(any('Déposer deux FCA' in t for t in titles))
        self.assertFalse(any('limites du menu individuel' in t for t in titles))
        both=priority_titles(q+' Et pour le même candidat, dans son ensemble certificatif ?','Lycée Général & Techno','examens')
        self.assertTrue(any('limites du menu individuel' in t for t in both))
        self.assertFalse(any('Déposer deux FCA' in t for t in both))
