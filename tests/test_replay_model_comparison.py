import csv,io,json,unittest
from unittest.mock import Mock
from admin_retest_113_live import comparison_step,render
class ComparisonBatchTests(unittest.TestCase):
    def setUp(self):
        self.row=dict(n='9',question='Où consulter ?',mode='examens',public='Lycée Général & Techno',academie='')
        self.state=dict(is_admin=True,audit113_batch=dict(rows=[self.row],index=0,results=[],waiting=False,stopped=False,comparison='mini_albert'))
        self.runner=Mock(return_value=dict(branches={n:dict(answer=n+' réponse',model=m,usage=dict(calls=2),audit=dict(proof='conservée')) for n,m in [('Mini','gpt-4o-mini'),('Albert','gpt-oss-120b')]}))
    def test_two_branches_and_one_row_only(self):
        self.assertTrue(comparison_step(self.state,self.runner,'v1'))
        self.runner.assert_called_once_with(self.row,'Non précisée')
        r=self.state['audit113_batch']['results'][0]
        self.assertEqual(r['reponse_mini'],'Mini réponse');self.assertEqual(r['reponse_albert'],'Albert réponse')
        self.assertEqual(json.loads(r['diagnostic_ia'])['branches']['Albert']['audit']['proof'],'conservée')
        self.assertNotIn('current_prompt',self.state)
        self.assertFalse(comparison_step(self.state,self.runner,'v1'))
        self.assertEqual(self.runner.call_count,1)
    def test_interruption_not_retried(self):
        self.state['audit113_batch']['comparison_inflight']=0
        comparison_step(self.state,self.runner,'v1');self.runner.assert_not_called()
        self.assertIn('aucune relance',self.state['audit113_batch']['results'][0]['erreur_albert'])
    def test_stop_and_nonadmin(self):
        self.state['audit113_batch']['stopped']=True
        self.assertFalse(comparison_step(self.state,self.runner,'v1'))
        self.state['audit113_batch']['stopped']=False;self.state['is_admin']=False
        self.assertFalse(comparison_step(self.state,self.runner,'v1'));self.runner.assert_not_called()
    def test_version_change_stops(self):
        self.state['audit113_batch']['version']='v0'
        self.assertFalse(comparison_step(self.state,self.runner,'v1'))
        self.assertTrue(self.state['audit113_batch']['stopped']);self.runner.assert_not_called()
    def test_error_recorded_once(self):
        self.runner.side_effect=RuntimeError('secret');comparison_step(self.state,self.runner,'v1')
        self.runner.assert_called_once()
        self.assertNotIn('secret',self.state['audit113_batch']['results'][0]['erreur_mini'])
        self.assertEqual(self.state['audit113_batch']['index'],1)
    def test_csv_has_both_responses(self):
        comparison_step(self.state,self.runner,'v1')
        class UI:
            def __init__(ui):ui.session_state=self.state;ui.downloads=[]
            def __enter__(ui):return ui
            def __exit__(ui,*a):pass
            def markdown(ui,*a,**kw):pass
            info=warning=write=caption=markdown
            def container(ui,*a,**kw):return ui
            def file_uploader(ui,*a,**kw):return None
            def button(ui,*a,**kw):return False
            def download_button(ui,label,data,**kw):ui.downloads.append(data)
        ui=UI();render(ui)
        rows=list(csv.DictReader(io.StringIO(ui.downloads[0].decode('utf-8-sig')),delimiter=';'))
        self.assertEqual(rows[0]['reponse_albert'],'Albert réponse')
        self.assertIn('branches',json.loads(rows[0]['diagnostic_ia']))
