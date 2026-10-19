"""Complétude guidée par les sources ; pas de validation distante."""
import unittest
from pathlib import Path
import test_documentation as routing
from documentary_review import response_focus_notes, source_packets, mark_excerpt, review_exam_answer, catalogue_focus_match
from test_documentary_review import FakeLLM

class ResponseFocusTests(unittest.TestCase):
    def test_no_guidance_without_its_document(self):
        for q in ('Comment déclarer une inaptitude ?', 'SHN : quels aménagements ?', 'EPPCS : pratique et oral ?'):
            self.assertEqual(response_focus_notes(q,[]),[])
        self.assertEqual(response_focus_notes('Comment changer de lycée ?', [{'path':'data/commun/gt_shn_eligibilite.txt'}]),[])

    def test_individual_medical_action_keeps_real_path(self):
        h=routing.DocumentationTests();h.setUp()
        docs,_,_,_=h.route('Déclarer dans iPackEPS une inaptitude temporaire : quelles étapes ?', 'Collège (DNB)','ipack')
        packets=source_packets(docs)
        p=next(p for p in packets if p['path'].endswith('ipack_inaptitude.txt'))
        self.assertTrue(catalogue_focus_match('Déclarer une inaptitude temporaire',p))
        self.assertIn('[Mes Élèves] > [Visualisation]',p['text'])
        self.assertIn('chemin',response_focus_notes('Déclarer une inaptitude temporaire',packets)[0])
        self.assertFalse(catalogue_focus_match('Un certificat permet-il une dispense du DNB ?',p))

    def test_ordinary_gt_count_keeps_at_least_two_national(self):
        path='data/commun/audit60/gt_regles_decisives.txt'
        packets=source_packets(mark_excerpt(Path(path).read_text(),path=path))
        notes=response_focus_notes('Combien d’épreuves et de champs au CCF bac GT ?',packets)
        self.assertIn('au moins',notes[0])
        self.assertIn('au moins deux activités',packets[0]['text'])
        self.assertEqual(response_focus_notes('Mon menu a déjà été envoyé, où suivre sa validation ?',packets),[])

    def test_eppcs_practice_is_a_part_of_the_oral(self):
        path='data/examens/fiches/examens_100_situation_eppcs_epreuve_terminale_ecrit_oral.txt'
        packets=source_packets(mark_excerpt(Path(path).read_text(),path=path))
        notes=response_focus_notes('EPPCS : comment fonctionne la pratique ?',packets)
        self.assertIn('durées et points',notes[0])
        self.assertIn('prestation pratique notée sur 12',packets[0]['text'])
        self.assertIn('commentaire analytique',packets[0]['text'])
        self.assertIn('session 2027',packets[0]['text'])

    def test_shn_fiche_contains_real_amendments_and_conditions(self):
        path='data/commun/gt_shn_eligibilite.txt'
        text=Path(path).read_text();packets=source_packets(mark_excerpt(text,path=path))
        self.assertIn('validation du recteur',text)
        self.assertIn('20 ne peut pas être l’unique note',text)
        self.assertIn('deux activités de deux champs différents',text)
        span=next(s for s in packets[0]['passages'] if s['text'].startswith('Aménagements de l’EPS obligatoire'))
        self.assertEqual(span['scope']['nature'],['texte_national'])
        self.assertNotIn('academy',span['scope'])
        self.assertTrue(response_focus_notes('SHN au bac GT : quels aménagements ?',packets))
        self.assertEqual(response_focus_notes('Statut SHN obtenu après les inscriptions : quel aménagement ?',packets),[])

    def test_source_guidance_is_passed_to_single_generation(self):
        path='data/examens/fiches/examens_100_situation_eppcs_epreuve_terminale_ecrit_oral.txt'
        docs=mark_excerpt(Path(path).read_text(),path=path,selection='catalogue',priority=200)
        packet=source_packets(docs)[0];span=next(s for s in packet['passages'] if s['text'].startswith('L’épreuve dite orale'))
        claim={'section':'decision','text':'L’épreuve dite orale comprend une prestation pratique notée sur 12 et un commentaire analytique noté sur 8, en deux parties de 15 minutes.','evidence':[{'document_id':packet['id'],'passage_ids':[span['id']]}]}
        llm=FakeLLM([{'claims':[claim]}]);a={}
        answer=review_exam_answer(llm,question='EPPCS : comment fonctionne la pratique ?',public='Lycée Général & Techno',mode='examens',documents=docs,audit=a)
        self.assertEqual(len(llm.prompts),1)
        self.assertIn('response_focus',llm.prompts[0])
        self.assertNotIn('response_focus',answer)
        self.assertFalse(a['final_rejections'])
