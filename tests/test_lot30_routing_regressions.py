"""Confusions de circuits : vrais documents, aucun appel distant."""
import ast
import unittest
from pathlib import Path
import test_documentation as routing
from documentary_review import mark_excerpt, source_packets, situation_mismatch, review_exam_answer, render_claims
from source_scope import select_academy
from test_documentary_review import FakeLLM

class CircuitRegressionTests(unittest.TestCase):
    def setUp(self):
        self.h = routing.DocumentationTests(); self.h.setUp()

    def test_note_export_keeps_perimeter_and_no_exam_rule(self):
        docs,_,_,_=self.h.route('Exporter mes notes vers Pronote : comment faire ?', 'Collège (DNB)', 'ipack')
        self.assertIn('Il n’existe pas dans le périmètre documenté d’export de notes',docs)
        # Exécuter le vrai bloc des repères de l'application, sans Streamlit.
        tree=ast.parse(Path('app.py').read_text())
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.Try) and any(isinstance(x,ast.Constant) and x.value=='config/faits_par_examen.txt' for x in ast.walk(n)))
        env={'prompt':'Exporter mes notes vers Pronote : comment faire ?', 'niveau_actuel_form':'Collège (DNB)', 'mode':'ipack','faits_champs':'','re':__import__('re')}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'app.py','exec'),env)
        self.assertEqual(env['faits_champs'],'')
        env.update(prompt='DNB : comment remonter les moyennes dans LSU ?',faits_champs='')
        exec(compile(ast.Module(body=[node],type_ignores=[]),'app.py','exec'),env)
        self.assertIn('LSU',env['faits_champs'])

    def test_ccf_recovery_not_ponctuel(self):
        docs,_,_,_=self.h.route('Comment organiser un rattrapage CCF pour un absent justifié ?', 'Lycée Général & Techno','examens')
        self.assertIn('CCF : positionnement des évaluations différées',docs)
        self.assertIn('après consultation de l’équipe pédagogique',docs)
        self.assertIn('MENE2531948N, 2.d',docs)
        self.assertNotIn('Bac GT ponctuel : publics et conditions de neutralisation',docs)
        self.assertTrue(situation_mismatch('Organiser le différé CCF ?', 'Bac GT ponctuel : publics et conditions de neutralisation'))
        self.assertFalse(situation_mismatch('CCF et ponctuel : quelles différences ?', 'Bac GT ponctuel : publics'))
        self.assertFalse(situation_mismatch('Absence au ponctuel : que faire ?', 'Bac GT ponctuel : publics'))

    def test_actual_ponctuel_absence_keeps_its_source(self):
        docs,_,_,_=self.h.route('Bac GT : absence justifiée aux deux épreuves ponctuelles ?', 'Lycée Général & Techno','examens')
        self.assertIn('Bac GT ponctuel : publics et conditions de neutralisation',docs)

    def test_medical_deposit_is_explicitly_local(self):
        path='data/examens/complement_reponses_validees.txt'
        ps=source_packets(mark_excerpt(Path(path).read_text(),path=path))
        for academy in ('Lille','Aix-Marseille'):
            packets,_=select_academy(ps,academy)
            span=next(s for p in packets for s in p['passages'] if s['text'].startswith('Certificat médical :'))
            self.assertEqual(span['scope']['nature'],['consigne_academique'])
            self.assertEqual(bool(span['scope'].get('not_confirmed_for')),academy=='Lille')

    def test_local_certificate_deposit_is_not_rendered_as_lille_rule(self):
        path='data/examens/complement_reponses_validees.txt'
        packets,_=select_academy(source_packets(mark_excerpt(Path(path).read_text(),path=path)),'Lille')
        packet=packets[0]
        span=next(s for s in packet['passages'] if s['text'].startswith('Certificat médical :'))
        claim={'section':'etape','text':'Le certificat médical se déclare et se dépose dans iPackEPS.',
               'evidence':[{'document_id':packet['id'],'quote':span['text'],'level':span['scope']['level'],'scope':span['scope']}]}
        answer=render_claims([claim],packets)
        self.assertIn('À Aix-Marseille',answer)
        self.assertIn('de l’académie de Lille',answer)

    def test_sourced_export_answer_needs_no_repair(self):
        docs,_,_,_=self.h.route('Exporter mes notes vers Pronote : comment faire ?', 'Collège (DNB)','ipack')
        packet=next(p for p in source_packets(docs) if p['path'].endswith('ipack_perimetre.txt'))
        span=next(s for s in packet['passages'] if s['text'].startswith('Il n’existe pas'))
        claim={'section':'decision','text':'Il n’existe pas dans le périmètre documenté d’export de notes iPackEPS vers Pronote.','evidence':[{'document_id':packet['id'],'passage_ids':[span['id']]}]}
        llm=FakeLLM([{'claims':[claim]}]);audit={}
        answer=review_exam_answer(llm,question='Exporter mes notes vers Pronote : comment faire ?',public='Collège (DNB)',mode='ipack',documents=docs,audit=audit)
        self.assertEqual(len(llm.prompts),1)
        self.assertIn('Pronote',answer)
        self.assertFalse(audit['final_rejections'])
