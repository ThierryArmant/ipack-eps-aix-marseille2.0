"""Raccordement de la vidéo des tableaux de bord au contexte final, sans appel payant."""
import unittest
from pathlib import Path
import knowledge_catalog as kc
import test_documentation as routing
from documentary_review import review_exam_answer
from test_documentary_review import FakeLLM
from tutorial_links import supporting_tutorials

DASHBOARD='data/ipack/situations_2026_10_19/tableaux_bord_verification_modules.txt'
PROFILE='data/ipack/visite_college_2026_10_18/fiche_professeur_fonctions_enregistrer.txt'
TZR='data/ipack/fiches/ipack_222_situation_enseignants_tzr_ou_partages_multi_etablissements.txt'

class DashboardSelectionTests(unittest.TestCase):
    def selected(self, question, mode='ipack'):
        route=routing.DocumentationTests();route.setUp()
        docs,_,_,_=route.route(question,'Lycée Général & Techno',mode)
        audit={}
        review_exam_answer(FakeLLM([{'claims':[]}]),question=question,public='Lycée Général & Techno',mode=mode,documents=docs,audit=audit)
        return {p['path']:p for p in audit['documents'] if p['id'] in audit.get('model_document_ids',[])},audit

    def test_progression_and_generic_grey_module_reach_final_context(self):
        for q in ['Où consulter le pourcentage de progression de nos dossiers ?',
                  'Comment afficher la jauge des saisies sur le tableau de bord ?',
                  'Dans iPackEPS, un module reste inactif : comment comprendre cela ?',
                  'Le module de l’enquête natation est grisé, pourquoi ?']:
            with self.subTest(q=q):
                selected,_=self.selected(q)
                self.assertIn(DASHBOARD,selected)
                self.assertNotIn(PROFILE,selected)
                self.assertIn('rapport détaillé',selected[DASHBOARD]['text'])
                self.assertIn('campagne de saisie',selected[DASHBOARD]['text'])

    def test_unrelated_grey_buttons_and_grading_do_not_select_dashboard(self):
        for q,mode in [('Le bouton de verrouillage de lot est grisé dans Santorin','ipack'),
                       ('Le bouton pour envoyer mon dossier pour validation est grisé','ipack'),
                       ('Quel pourcentage de la moyenne vient de cette note EPS ?','ipack'),
                       ('Je viens de devenir coordonnateur, quels modules sont grisés selon mes droits ?','ipack'),
                       ('Un module est grisé','examens')]:
            with self.subTest(q=q):
                selected,_=self.selected(q,mode)
                self.assertNotIn(DASHBOARD,selected)

    def test_role_specific_question_keeps_professor_functions(self):
        selected,_=self.selected('Je deviens coordonnateur EPS : quels droits et fonctions dois-je déclarer dans ma fiche professeur ?')
        self.assertIn(PROFILE,selected)

    def test_navigation_payload_keeps_full_observed_path_and_video(self):
        selected,_=self.selected('Dans iPackEPS je travaille sur deux établissements : comment basculer de l’un à l’autre ?')
        self.assertIn(TZR,selected)
        packet=selected[TZR]
        for word in ["fil d'Ariane",'Informations',"Changer d'Établissement",'[Entrer]']:
            self.assertIn(word,packet['text'])
        audit={'documents':[packet],'accepted_claims':[{'section':'etape','text':"Changer d’établissement par le tableau de bord.",'evidence':[{'document_id':packet['id']}]}]}
        self.assertEqual(['https://youtu.be/HtFmE-6rCl4'],supporting_tutorials(audit,kc.catalog()))

    def test_single_mark_case_is_focused_without_literal_plus_signs(self):
        key='data/examens/situations_2026_10_13/gt_une_seule_note_sur_trois.txt'
        for q in ['Bac général : une note et DI sur deux APSA, comment traiter le résultat ?',
                  'Bac GT : inapte sur 2 activités avec 1 note, quelles possibilités ?']:
            with self.subTest(q=q):
                selected,_=self.selected(q,'examens')
                self.assertIn(key,selected)
                self.assertEqual(selected[key]['priority'],300)
                self.assertFalse(any('ipack_194' in p or 'aix_inscriptions_2027' in p for p in selected))
                self.assertIn('ne pas formuler de proposition de note',selected[key]['text'])

    def test_single_mark_trigger_does_not_capture_two_marks_or_other_diplomas(self):
        key='data/examens/situations_2026_10_13/gt_une_seule_note_sur_trois.txt'
        for q in ['Bac GT : deux notes et DI sur une épreuve, quelle moyenne ?',
                  'CAP : inapte sur deux activités avec une seule note',
                  'DNB : une note et DI à deux activités']:
            with self.subTest(q=q):
                selected,_=self.selected(q,'examens')
                self.assertNotIn(key,selected)

    def test_di_di_numeric_mark_does_not_depend_on_value_or_spacing(self):
        key='data/examens/situations_2026_10_13/gt_une_seule_note_sur_trois.txt'
        for value in [str(n) for n in range(21)]+['8,5','12.5','16,75']:
            for expression in [f'DI+DI+{value}',f'DI + DI + {value}',f'di+di + {value}']:
                with self.subTest(expression=expression):
                    selected,_=self.selected(expression,'examens')
                    self.assertIn(key,selected)
                    self.assertEqual(selected[key]['priority'],300)
        for q in ['CAP DI+DI+10','Bac pro DI+DI+16','DNB DI+DI+8']:
            selected,_=self.selected(q,'examens')
            self.assertNotIn(key,selected)

    def test_extracted_passage_is_exact_and_bounded(self):
        excerpt=Path(DASHBOARD).read_text().split('\n\nNature de la source :')[0]
        self.assertIn(excerpt,Path('data/ipack/transcriptions_videos_tutoriels.txt').read_text())
        self.assertLess(len(Path(DASHBOARD).read_text()),2400)

if __name__=='__main__':unittest.main()
