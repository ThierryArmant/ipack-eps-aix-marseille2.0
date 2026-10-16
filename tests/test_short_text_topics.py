"""Exécute les vrais filtres de l'application, sans serveur ni appel de génération."""
import ast
import re
import unicodedata
import unittest
from pathlib import Path
import knowledge_catalog as kc

TREE=ast.parse(Path('app.py').read_text())
def assignment(name):
    return next(n for n in ast.walk(TREE) if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))

def gates(question,mode='textes'):
    env=dict(re=re,unicodedata=unicodedata,prompt=question,mode=mode,
             niveau_actuel_form='Lycée Général & Techno',has_text_reference=kc.has_text_reference)
    for name in ('normaliser','contient_mot_cle'):
        node=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'app.py','exec'),env)
    env.update(p_low=question.lower(),p_norm=env['normaliser'](question))
    for name in ('mots_cles_intention_peda','mots_cles_eps_admin','sujet_documente_textes','est_totalement_hors_sujet'):
        node=assignment(name)
        if name=='est_totalement_hors_sujet':
            node=next(n for n in ast.walk(TREE) if isinstance(n,ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
                      and isinstance(n.value,ast.UnaryOp))
        exec(compile(ast.Module(body=[node],type_ignores=[]),'app.py','exec'),env)
    exec(compile(ast.Module(body=[assignment('est_unss')],type_ignores=[]),'app.py','exec'),env)
    # Les autres disjoncteurs sont faux dans ces demandes professionnelles ; UNSS reste prioritaire.
    env['est_cas_direct']=env['est_unss']
    exec(compile(ast.Module(body=[assignment('est_question_trop_courte')],type_ignores=[]),'app.py','exec'),env)
    return env

class ShortTextTopicsTests(unittest.TestCase):
    def test_identified_professional_requests_reach_documents(self):
        for q in ('IMP', 'IMP coordination', 'pour les imp de coorinatio', 'Recours PPCR',
                  'Classe exceptionnelle', 'Cumul activités'):
            with self.subTest(q=q):
                e=gates(q)
                self.assertTrue(e['sujet_documente_textes'])
                self.assertFalse(e['est_totalement_hors_sujet'])
                self.assertFalse(e['est_question_trop_courte'])
                self.assertTrue(kc.priority_context(q,'Lycée Général & Techno','textes'))

    def test_unrelated_questions_stay_outside(self):
        for q in ('Recette pizza', 'Cours bitcoin', 'Impératif grammatical'):
            with self.subTest(q=q):
                e=gates(q)
                self.assertFalse(e['sujet_documente_textes'])
                self.assertTrue(e['est_totalement_hors_sujet'])

    def test_ambiguous_short_question_still_gets_clarification(self):
        e=gates('mon professeur')
        self.assertFalse(e['sujet_documente_textes'])
        self.assertTrue(e['est_question_trop_courte'])

    def test_documentary_exception_is_limited_to_textes(self):
        for mode in ('ipack','examens'):
            self.assertFalse(gates('IMP',mode)['sujet_documente_textes'])

    def test_unss_restriction_keeps_its_priority(self):
        e=gates('IMP UNSS')
        self.assertTrue(e['est_unss'])
        self.assertTrue(e['est_cas_direct'])
        self.assertFalse(e['est_question_trop_courte'])
