import csv,io,json,tempfile
from pathlib import Path
import unittest
from admin_retest_113_live import render
from admin_replay_loader import load_replay
from documentary_review import circuit_document_mismatch

class Surface:
    def __init__(self, rows, fallback=False):
        self.downloads=[];self.warnings=[]
        self.session_state={'is_admin':True,'audit113_batch':{'rows':rows,'index':0,'results':[],'waiting':True},
            'messages_hub':[{'role':'assistant','type':'text','content':'answer','version':'v',
                            'usage_ia':{'calls':2 if fallback else 1,'models':['test'],'fallback_used':fallback},
                            'diagnostic_ia':{'calls':[{'prompt':'exact proof'}]}}]}
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def container(self,*a,**k):return self
    def markdown(self,*a,**k):pass
    info=markdown;write=markdown
    def warning(self,text):self.warnings.append(text)
    def file_uploader(self,*a,**k):return None
    def button(self,*a,**k):return False
    def download_button(self,label,data,**kwargs):self.downloads.append(data)

class ReplayUsageTests(unittest.TestCase):
    def row(self,n=1):return {'n':str(n),'question':'Où est le menu ?','mode':'ipack','public':'Collège (DNB)','academie':''}
    def test_export_retains_question_usage_trace_and_version(self):
        ui=Surface([self.row()]);render(ui)
        results=list(csv.DictReader(io.StringIO(ui.downloads[0].decode('utf-8-sig')),delimiter=';'))
        self.assertEqual(results[0]['question'],'Où est le menu ?')
        self.assertEqual(results[0]['version'],'v')
        self.assertEqual(results[0]['academie_effective'],'Non précisée')
        self.assertEqual(results[0]['academie_origine'],'non_precisee')
        self.assertEqual(json.loads(results[0]['usage_ia'])['calls'],1)
        self.assertEqual(json.loads(results[0]['diagnostic_ia'])['calls'][0]['prompt'],'exact proof')
    def test_csv_exports_effective_scope_from_question_not_previous_academy(self):
        row = self.row(); row['question'] = 'Quelle note à Aix-Marseille ?'
        ui=Surface([row]); ui.session_state['academie_memorisee']='Créteil'
        render(ui)
        results=list(csv.DictReader(io.StringIO(ui.downloads[0].decode('utf-8-sig')),delimiter=';'))
        self.assertEqual(results[0]['academie'], '')
        self.assertEqual(results[0]['academie_effective'], 'Aix-Marseille')
        self.assertEqual(results[0]['academie_origine'], 'question')

    def test_provider_fallback_is_retained_but_batch_stops_before_next_question(self):
        ui=Surface([self.row(),self.row(2)],True);render(ui)
        self.assertEqual(len(ui.session_state['audit113_batch']['results']),1)
        self.assertTrue(ui.session_state['audit113_batch']['stopped'])
        self.assertNotIn('current_prompt',ui.session_state)
    def test_replay_loader_observes_new_source_without_mutating_previous(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'admin_retest_113_live.py';p.write_text('render="old"')
            old=load_replay(d);p.write_text('render="new"');new=load_replay(d)
            self.assertEqual(old.render,'old');self.assertEqual(new.render,'new')
    def test_ponctuel_does_not_use_school_year_student_entry_procedure(self):
        text=Path('data/ipack/fiches/ipack_031_situation_ipackeps_saisie_inaptitude_et_depot_certificat_medical.txt').read_text()
        self.assertTrue(circuit_document_mismatch('Transmettre le certificat du candidat inapte au ponctuel',text))
        self.assertFalse(circuit_document_mismatch('Saisir le certificat de notre élève en CCF',text))
        self.assertFalse(circuit_document_mismatch('Comparer la procédure CCF et ponctuel',text))


class InterruptedReplayTests(unittest.TestCase):
    def row(self,n):return {'n':str(n),'question':'Q%d ?'%n,'mode':'ipack','public':'Collège (DNB)','academie':''}
    def stuck(self):
        ui=Surface([self.row(1),self.row(2)]);ui.session_state['messages_hub']=[]
        return ui
    def test_interrupted_question_is_relaunched_once(self):
        ui=self.stuck();render(ui)
        b=ui.session_state['audit113_batch']
        self.assertEqual((b['index'],b['results'],b['waiting']),(0,[],True))
        self.assertEqual(ui.session_state['current_prompt'],'Q1 ?')
    def test_second_interruption_marks_blocked_and_moves_on(self):
        ui=self.stuck();render(ui)
        ui.session_state.pop('current_prompt');ui.session_state['messages_hub']=[];render(ui)
        b=ui.session_state['audit113_batch']
        self.assertEqual(b['index'],1);self.assertIn('BLOQUÉE',b['results'][0]['nouvelle_reponse'])
        self.assertEqual(ui.session_state['current_prompt'],'Q2 ?')
    def test_pending_prompt_is_left_alone(self):
        ui=self.stuck();ui.session_state['current_prompt']='Q1 ?';render(ui)
        b=ui.session_state['audit113_batch']
        self.assertEqual((b['index'],b.get('retries')),(0,None))
