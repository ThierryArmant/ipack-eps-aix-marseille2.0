import unittest
from documentary_review import source_packets, mark_excerpt, bind_faq_context
from knowledge_catalog import priority_titles

class FAQContextTests(unittest.TestCase):
    def test_answer_keeps_exact_question_without_inventing_conditions(self):
        body='Q7 : Le bouton affiche X ; comment continuer ?\n\nR7 : Le responsable ouvre le dossier.'
        spans=source_packets(mark_excerpt(body))[0]['passages']
        self.assertEqual(len(spans),1)
        self.assertEqual(spans[0]['text'],body)
    def test_answer_keeps_its_sub_bullets(self):
        body='  - Q1 : Question\n  - R1 : Réponse\n    - seulement si le dossier est validé\n    - sinon voir le chef'
        spans=source_packets(mark_excerpt(body))[0]['passages']
        self.assertEqual([p['text'] for p in spans],[body])
    def test_autonomous_paragraph_after_last_answer_stays_separate(self):
        faq='  - Q4 : Le dossier signé doit être modifié.\n  - R4 : Demander au chef de le rouvrir.'
        action="Action : demander l'ouverture d'une section. Attendu final : demande déposée."
        spans=[p['text'] for p in source_packets(mark_excerpt(faq+'\n\n'+action))[0]['passages']]
        self.assertEqual(spans,[faq,action])
    def test_less_indented_reminder_is_not_part_of_answer(self):
        lines=['- Q2 : Le bouton ne réagit pas.','  R2 : Renommer le protocole.',
               "- Rappel : la validation d'un cas exceptionnel relève de l'inspection."]
        body='\n'.join(lines); spans=[]; pos=0
        for line in lines:
            spans.append({'text':line,'start':pos,'end':pos+len(line),'scope':{}}); pos+=len(line)+1
        out=[p['text'] for p in bind_faq_context(spans, body)]
        self.assertEqual(out,[lines[0]+'\n'+lines[1], lines[2]])
    def test_sss_opening_fiche_separates_faq_and_expected_action(self):
        from pathlib import Path
        path='data/ipack/fiches/ipack_080_article_28_dossiers_dossier_sss_ouverture_demande_d_ouverture_de_section_sportive_scolaire.txt'
        spans=[p['text'] for p in source_packets(mark_excerpt(Path(path).read_text(encoding='utf-8'), path=path))[0]['passages']]
        r4=next(t for t in spans if 'R4' in t)
        self.assertNotIn('Action :', r4)
        self.assertTrue(any(t.startswith('Action :') for t in spans))
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
