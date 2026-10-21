"""Défauts de voisinage constatés, testés avec contre-exemples sans IA distante."""
import unittest
from pathlib import Path
import knowledge_catalog as kc
import test_documentation as routing
from test_documentary_review import FakeLLM
from documentary_review import review_exam_answer, mark_excerpt, context_document_mismatch

class TransversalTerrainNeighbours(unittest.TestCase):
    def setUp(self):
        self.h=routing.DocumentationTests();self.h.setUp()
    def test_medical_typo_has_same_document_selection_as_correct_word(self):
        typo='Inaptitude totale : faut-il mettre Dispensé ?'.replace('Inaptitude','Imaptitude')
        regular=typo.replace('Imaptitude','Inaptitude')
        for public in ['Lycée Général & Techno','Lycée Pro / CAP']:
            a=self.h.route(typo,public,'examens')[0]
            b=self.h.route(regular,public,'examens')[0]
            self.assertEqual(a,b)
        self.assertIn('gt_inaptitude_possibilites_ccf.txt', self.h.route(typo,'Lycée Général & Techno','examens')[0])
        self.assertEqual(kc.normalise('imagination et aptitude'),'imagination et aptitude')
    def test_conditional_general_fiche_contains_both_durations(self):
        text=self.h.route('Inaptitude totale : faut-il mettre Dispensé ?','Lycée Général & Techno','examens')[0]
        for phrase in ['toute l’année','période limitée','deux épreuves','sur une seule','notes antérieures','si elle est partielle']:
            self.assertIn(phrase,text)
    def test_exam_status_does_not_receive_class_attendance_source(self):
        q='Inaptitude totale : faut-il mettre Dispensé ?'
        wrong='data/textes/fiches/dispense_inaptitude_presence_cours.txt'
        right='data/commun/audit60/gt_inaptitude_possibilites_ccf.txt'
        docs=mark_excerpt(Path(wrong).read_text(),path=wrong,title='Élève inapte : présence en cours')+'\n'+mark_excerpt(Path(right).read_text(),path=right,title='Inaptitude au bac GT')
        a={};review_exam_answer(FakeLLM([{'claims':[]}]),question=q,public='Lycée Général & Techno',mode='examens',documents=docs,audit=a)
        self.assertIn('D1',a['excluded_situation_documents'])
        self.assertNotIn('D2',a['excluded_situation_documents'])
        self.assertFalse(context_document_mismatch('Élève inapte : doit-il venir en cours et quel statut saisir ?', 'Lycée Général & Techno','examens',{'path':wrong,'title':'Présence en cours'}))
    def test_missing_teacher_lots_does_not_invent_missing_students(self):
        q='Un remplaçant ne voit aucun lot dans Santorin, que doit faire la direction ?'
        self.assertNotIn('eleves manquants',kc.enrich(q))
        text=self.h.route(q,'Lycée Général & Techno','examens')[0]
        self.assertNotIn('audit_lot1_2026_10_12/eleves_manquants.txt',text)
        self.assertIn('REMPLAÇANT',text)
        students=self.h.route('Les élèves inscrits dans Cyclades sont absents des lots Santorin après distribution', 'Lycée Général & Techno','examens')[0]
        self.assertIn('audit_lot1_2026_10_12/eleves_manquants.txt',students)
        newcomer=self.h.route('Un élève arrivé cette semaine n’apparaît pas dans mon lot Santorin : que vérifier ?', 'Lycée Général & Techno','examens')[0]
        self.assertIn('audit_lot1_2026_10_12/eleves_manquants.txt',newcomer)
    def test_membership_does_not_mean_departure(self):
        q='Bac GT CCF : un élève appartient à une structure du PPF sans être inscrit sur les listes SHN, peut-il bénéficier des aménagements ?'
        text=self.h.route(q,'Lycée Général & Techno','examens')[0]
        self.assertNotIn('eleve_parti_inscrit.txt',text)
        self.assertIn('shn',text.lower())
        real=self.h.route('Un élève est parti mais reste inscrit à l’examen, que faire ?', 'Lycée Général & Techno','examens')[0]
        self.assertIn('eleve_parti_inscrit.txt',real)
