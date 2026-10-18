import unittest
from unittest.mock import patch
import guided_navigation as guide

class FakeUI:
    def __init__(self, answers, state=None, click=''):
        self.answers=iter(answers); self.session_state=state if state is not None else {}; self.click=click
    def radio(self,*args,**kwargs): return next(self.answers)
    def button(self,label,**kwargs): return label == self.click
    def text_input(self,*args,**kwargs): return 'bouton absent'
    def rerun(self): pass
    def columns(self, *a, **k): return (self, self)
    def expander(self,*args,**kwargs): return self
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def __getattr__(self,name): return lambda *args,**kwargs: None

class GuidedTests(unittest.TestCase):
    def test_all_steps_have_existing_sources(self):
        routes=guide.routes()
        self.assertGreaterEqual(len(routes),7)
        for route in routes.values():
            for text,path in route:
                self.assertTrue(path.is_file())
                self.assertTrue(text)
                self.assertNotIn('certificative',text)
    def test_next_back_and_blocked_branches(self):
        goal='Me repérer depuis le début'
        state={}
        ui=FakeUI([goal],state,'C’est fait · Suivant →')
        guide.render_guide(ui,'test','Lycée voie générale')
        self.assertEqual(state['test_position_0'],1)
        ui=FakeUI([goal],state,'← Retour')
        guide.render_guide(ui,'test','Lycée voie générale')
        self.assertEqual(state['test_position_0'],0)
    def test_completion_and_no_source(self):
        goal='Configurer les périodes'
        for answer in ['Oui','Non, j’ai encore besoin d’aide']:
            guide.render_guide(FakeUI([goal,'C’est fait',answer]),'x','Lycée voie professionnelle')
        with patch.object(guide,'documented_steps',return_value=([],'')):
            self.assertEqual(guide.routes(),{})
