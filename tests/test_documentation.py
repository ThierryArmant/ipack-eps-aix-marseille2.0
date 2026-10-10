"""Régressions sans OpenAI : vrai chargeur et vrai routage, retrievers simulés."""
import ast
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

import knowledge_catalog as kc


def app_functions():
    tree = ast.parse(Path('app.py').read_text())
    names = {'decouper_en_fiches', 'charger_dossier_txt_securise', '_recherche_documentaire'}
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in names]
    env = dict(re=re, **{name: getattr(kc, name) for name in
                        ('document_records', 'incompatible', 'reference_notice', 'obsolete_reference', 'section_scopes')})
    env['Document'] = lambda **kw: SimpleNamespace(**kw)
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith('_RE_') for t in n.targets):
            exec(compile(ast.Module(body=[n], type_ignores=[]), 'app.py', 'exec'), env)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'app.py', 'exec'), env)
    return env


class Retriever:
    def __init__(self, docs):
        self.docs = docs

    def retrieve(self, question):
        return [SimpleNamespace(node=d, score=0.95) for d in self.docs]


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.env = app_functions()

    def route(self, question, public, mode, docs=()):
        e = self.env
        e.update(prompt=question, p_norm=kc.normalise(question), p_low=question.lower(),
                 niveau_actuel_form=public, mode=mode, est_college=public == 'Collège (DNB)',
                 est_clairement_lycee=bool(re.search('bac|cap', kc.normalise(question))),
                 mots_cles_intention_peda=[], recherche_mots={},
                 chercher_par_mots=lambda *a: [], libelle_source=lambda n: n.node.metadata.get('source'))
        for name in ('textes', 'peda', 'santorin', 'ipack'):
            e['retriever_' + name] = Retriever(docs)
        return e['_recherche_documentaire']()

    def test_archives_and_quarantine_not_indexed(self):
        for folder in ('data/examens', 'data/ipack', 'data/textes'):
            docs = self.env['charger_dossier_txt_securise'](folder)
            self.assertGreater(len(docs), 5)
            for d in docs:
                self.assertNotIn('/archives/', d.metadata['path'])
                self.assertNotIn('/a_verifier/', d.metadata['path'])
                self.assertFalse(kc.obsolete_reference(d.text))

    def test_shared_gt_source_available_in_three_bases(self):
        for folder in ('data/examens', 'data/ipack', 'data/textes'):
            docs = self.env['charger_dossier_txt_securise'](folder)
            self.assertTrue(any('texte_officiel_bac_gt' in d.metadata['source'] for d in docs))

    def test_registry_paths_exist(self):
        for path in kc.catalog():
            self.assertTrue(Path(path).is_file(), path)

    def test_ambiguous_medical_case_asks_before_code(self):
        q = 'Il est dispensé et il manque une note : je mets zéro ou DI ?'
        self.assertIn('CAP ou baccalauréat professionnel', kc.clarification(q, 'Lycée Pro / CAP'))
        self.assertIn('totale ou partielle', kc.clarification(q, 'Lycée Général & Techno'))

    def test_precise_partial_inaptitude_reaches_documentation(self):
        q = 'Bac pro 2026 : inaptitude partielle temporaire en terminale, maintenir le CCF ?'
        self.assertEqual(kc.clarification(q, 'Lycée Pro / CAP'), '')
        text, sources, _, error = self.route(q, 'Lycée Pro / CAP', 'ipack')
        self.assertIn('MENE2526357C', text)
        self.assertNotIn('MENE2517122C', text)
        self.assertTrue(sources)
        self.assertEqual(error, '')

    def test_cap_does_not_receive_bac_pro_notice(self):
        text, _, _, _ = self.route('CAP 2026 inaptitude partielle temporaire CCF', 'Lycée Pro / CAP', 'examens')
        self.assertIn('MENE2526679C', text)
        self.assertNotIn('MENE2505383C', text)

    def test_dnb_lsu_cyclades_and_no_foreign_diploma(self):
        docs = [SimpleNamespace(text='[PORTEE: cap]\nDeux épreuves CAP', metadata={'source': 'cap'})]
        text, _, _, _ = self.route('3e : où saisir mes trois CCF EPS dans Santorin pour le DNB ?', 'Collège (DNB)', 'examens', docs)
        self.assertIn('LSU', text)
        self.assertIn('Cyclades', text)
        self.assertNotIn('Deux épreuves CAP', text)
        self.assertIn('recommandation', text)

    def test_mixed_cycle3_keeps_both_levels(self):
        text, _, _, _ = self.route('24 CM2 et 28 élèves de 6e, course orientation dans un parc public : encadrement ?', '1er degré', 'textes')
        self.assertIn('cycle 3', text)
        self.assertIn('quatre adultes', text)
        self.assertIn('exclut les activités physiques', text)

    def test_climbing_final_teacher_check(self):
        text, _, _, _ = self.route('28 élèves de 4e, moulinette après une leçon, assurage seuls ?', 'Collège (DNB)', 'textes')
        self.assertIn('visuel et tactile', text)
        self.assertIn('retour au sol', text)
        self.assertIn('simultanément actifs', text)

    def test_filter_before_limit_retains_matching_nodes(self):
        docs = [SimpleNamespace(text=f'[PORTEE: cap]\nCAP {i}', metadata={'source': 'cap'}) for i in range(9)]
        docs.append(SimpleNamespace(text='[PORTEE: gt]\nPROCÉDURE GT', metadata={'source': 'gt'}))
        text, _, _, _ = self.route('Bac général : exporter les élèves', 'Lycée Général & Techno', 'examens', docs)
        self.assertIn('PROCÉDURE GT', text)
        self.assertNotIn('CAP 1', text)

    def test_missing_context_and_semantic_rewrite_regressions(self):
        text, _, _, _ = self.route('Quel bouton pour une action inconnue ?', 'Lycée Général & Techno', 'ipack')
        self.assertEqual(text, '')
        code = Path('app.py').read_text()
        self.assertIn('if besoin_ia and (erreur_rag or not extraits_doc)', code)
        self.assertNotIn('re.sub(r"santorin", "LSU / dossier scolaire"', code)


if __name__ == '__main__':
    unittest.main()
