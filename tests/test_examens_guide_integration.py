"""Exerce le branchement réel du bouton sans lancer Streamlit ni le modèle."""
import ast
from contextlib import nullcontext
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

class GuideEntryTests(TestCase):
    def run_entry(self, mode, public):
        tree=ast.parse(Path('app.py').read_text())
        block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp) and any(isinstance(x,ast.Name) and x.id=='_guide_mode' for x in ast.walk(n.test)))
        class UI:
            def __init__(self): self.session_state={'active_module':mode,'niveau_actif_form':public};self.buttons=[]
            def button(self,label,**kw): self.buttons.append(kw['key']);return True
            def container(self,**kw): return nullcontext()
            def markdown(self,*a,**kw): pass
        ui=UI()
        with patch('guided_navigation.render_guide') as render:
            exec(compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),'app.py','exec'),{'st':ui,'_guide_mode':mode,'_guide_level':public,'public_label':lambda s:s})
            return ui,render.call_args
    def test_examens_lycees_use_examens_guide(self):
        for public in ['Lycée Général & Techno','Lycée Pro / CAP']:
            ui,call=self.run_entry('examens',public)
            self.assertEqual(call.kwargs['mode'],'examens')
            self.assertIn('examens',call.args[1])
            call.kwargs['on_done']()
            self.assertFalse(next(v for k,v in ui.session_state.items() if k.startswith('guide_direct_')))
    def test_other_publics_and_textes_have_no_examens_button(self):
        for mode,public in [('examens','Collège'),('examens','1er degré'),('textes','Lycée Pro / CAP')]:
            ui,call=self.run_entry(mode,public)
            self.assertIsNone(call)
            self.assertFalse(ui.buttons)
    def test_ipack_state_is_separate(self):
        _,ipack=self.run_entry('ipack','Lycée Général & Techno')
        _,exam=self.run_entry('examens','Lycée Général & Techno')
        self.assertEqual(ipack.kwargs['mode'],'ipack')
        self.assertNotEqual(ipack.args[1],exam.args[1])
    def test_no_output_truncation_markers_in_document_base(self):
        import re
        marker=re.compile(r'\d[\d, ]*\s+tokens?\s+truncated|output\s+truncated',re.I)
        for p in Path('data').rglob('*.txt'):
            self.assertIsNone(marker.search(p.read_text()),str(p))
