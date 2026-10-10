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
                        ('document_records', 'incompatible', 'reference_notice', 'obsolete_reference', 'section_scopes', 'passage_key')})
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
    def test_cap_shn_gets_cap_reference_without_pro_modalities(self):
        text, _, _, _ = self.route('CAP 2026 SHN : combien d’activités sont réellement évaluées ?', 'Lycée Pro / CAP', 'examens')
        self.assertIn('UNE SEULE activité est réellement passée et évaluée', text)
        self.assertNotIn('Deux activités sont réellement évaluées', text)

    def test_sss_replacement_does_not_select_dnb_absence_notice(self):
        paths = [path for path, _ in kc.reference_notice(['dnb'], "Les trois heures de SSS peuvent-elles remplacer les heures d'EPS ?")]
        self.assertIn('data/commun/parcours_sportifs/01_sss_eps_obligatoire.txt', paths)
        self.assertNotIn('data/commun/dnb/03_absences_representativite.txt', paths)

    def test_cap_temporary_inaptitude_does_not_get_three_activity_entry(self):
        text, _, _, _ = self.route('CAP session 2026 inaptitude temporaire seconde activité une note conserver', 'Lycée Pro / CAP', 'ipack')
        self.assertIn('certification sur une seule activité', text)
        self.assertIn('MENE2526679C', text)
        self.assertNotIn('saisir DI + DI + DI', text)

    def test_shn_does_not_inject_swimming_school_rules(self):
        text, _, _, _ = self.route('Bac professionnel 2026 SHN natation : spécialité et CCF', 'Lycée Pro / CAP', 'examens')
        self.assertIn('Deux activités sont réellement évaluées', text)
        self.assertNotIn('Natation scolaire :', text)

    def test_option_eps_gets_its_own_lsl_reference(self):
        text, _, _, _ = self.route('Bac général : enseignement optionnel EPS, LSL ou LSU ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('MENE2523744N', text)
        self.assertIn('livret scolaire du lycée (LSL)', text)

    def test_2027_absence_source_is_available(self):
        text, _, _, _ = self.route('DNB 2027 une seule note En attente', 'Collège (DNB)', 'examens')
        self.assertIn('MENE2623194N', text)
        self.assertIn('absence justifiée : nouvelle convocation', text)

    def test_documentary_context_is_bounded(self):
        docs = [SimpleNamespace(text=f'[PORTEE: gt] PASSAGE_{i}', metadata={'source': f'{i}.txt'}) for i in range(30)]
        text, _, _, _ = self.route('Bac général : informations', 'Lycée Général & Techno', 'examens', docs)
        self.assertLessEqual(len(re.findall('PASSAGE_', text)), 10)

    def test_dnb_new_fiches_are_shared_but_not_selected_for_bac(self):
        for folder in ('data/ipack', 'data/examens', 'data/textes'):
            paths = [md['path'] for _, md in kc.document_records(folder)]
            self.assertEqual(sum('/commun/dnb/' in p for p in paths), 8)
        text, _, _, _ = self.route('Bac pro : créer un protocole et saisir les notes', 'Lycée Pro / CAP', 'examens')
        self.assertNotIn('Incluscol', text)
        self.assertNotIn('DNB :', text)

    def test_dnb_santorin_is_harmonisation_not_ccf(self):
        text, _, _, _ = self.route('DNB 2026 : à quoi sert Santorin et où saisir la moyenne EPS ?', 'Collège (DNB)', 'examens')
        self.assertIn("outil de la commission académique", text)
        self.assertIn('Il est faux de répondre', text)
        self.assertIn('ne pas créer trois CCF', text)

    def test_dnb_no_universal_competence_conversion(self):
        text, _, _, _ = self.route('DNB : convertir les niveaux de compétences en note sur 20', 'Collège (DNB)', 'examens')
        self.assertIn('Aucune table nationale universelle', text)

    def test_dnb_single_note_checks_representativity(self):
        text, _, _, _ = self.route("DNB : un élève n'a qu'une seule note et une moyenne En attente", 'Collège (DNB)', 'examens')
        self.assertIn('Une seule note', text)
        self.assertIn('ne déclenche pas systématiquement', text)

    def test_dnb_sessions_do_not_reuse_2026_deadline(self):
        text, _, _, _ = self.route('DNB 2027 : quelle date et quel texte utiliser ?', 'Collège (DNB)', 'examens')
        self.assertIn('MENE2623228N', text)
        self.assertIn('Les dates de remontée LSU', text)
        self.assertIn('sont historiques', text)

    def test_dnb_incluscol_is_not_note_entry(self):
        text, _, _, _ = self.route('DNB 2027 : Incluscol, procédure simplifiée ou complète ?', 'Collège (DNB)', 'ipack')
        self.assertIn('le candidat crée la demande', text)
        self.assertIn('Incluscol ne sert pas à saisir', text)

    def test_dnb_collective_oral_duration_is_distinct(self):
        text, _, _, _ = self.route('DNB : durée de notre oral en groupe pour un parcours EPS ?', 'Collège (DNB)', 'examens')
        self.assertIn('10 minutes de présentation puis 15', text)

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

    def test_cap_reference_survives_complementary_lookup_failure(self):
        self.route('CAP 2026 inaptitude temporaire CCF', 'Lycée Pro / CAP', 'examens')
        def broken(*args):
            raise RuntimeError('simulated lookup outage')
        self.env['chercher_par_mots'] = broken
        text, sources, diagnostics, error = self.env['_recherche_documentaire']()
        self.assertIn('certification sur une seule activité', text)
        self.assertTrue(sources)
        self.assertTrue(diagnostics)
        self.assertEqual(error, '')

    def test_one_failed_retriever_does_not_block_other_bases(self):
        self.route('Comment exporter mon protocole ?', 'Lycée Général & Techno', 'examens')
        class Broken:
            def retrieve(self, question):
                raise RuntimeError('simulated retriever outage')
        self.env['retriever_santorin'] = Broken()
        self.env['retriever_ipack'] = Retriever([SimpleNamespace(
            text='Procédure documentaire conservée', metadata={'source': 'guide'})])
        text, _, diagnostics, error = self.env['_recherche_documentaire']()
        self.assertIn('Procédure documentaire conservée', text)
        self.assertTrue(diagnostics)
        self.assertEqual(error, '')

    def test_keyword_failure_still_uses_vector_retriever(self):
        self.route('Comment exporter mon protocole ?', 'Lycée Général & Techno', 'examens')
        def broken(*args):
            raise RuntimeError('simulated keyword outage')
        self.env['chercher_par_mots'] = broken
        self.env['retriever_ipack'] = Retriever([SimpleNamespace(
            text='Guide technique retrouvé malgré la panne par mots', metadata={'source': 'guide'})])
        text, _, _, error = self.env['_recherche_documentaire']()
        self.assertIn('Guide technique retrouvé', text)
        self.assertEqual(error, '')

    def test_empty_lookup_failure_remains_blocking(self):
        self.route('Comment exporter mon protocole ?', 'Lycée Général & Techno', 'examens')
        def broken(*args):
            raise RuntimeError('simulated lookup outage')
        self.env['chercher_par_mots'] = broken
        text, _, _, error = self.env['_recherche_documentaire']()
        self.assertEqual(text, '')
        self.assertTrue(error)

    def test_gt_nonlisted_ppf_gets_correct_diploma_notice(self):
        text, _, _, error = self.route('Bac général 2026 : sportif non listé en PPF, aménagement EPS possible ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('absence sur une liste ministérielle ne suffit pas', text)
        self.assertNotIn('[PORTEE: cap]', text)
        self.assertNotIn('[PORTEE: pro]', text)
        self.assertEqual(error, '')

    def test_gt_shn_notice_not_selected_for_cap(self):
        notices = kc.reference_notice({'cap'}, 'CAP SHN non listé en PPF')
        self.assertNotIn('data/commun/gt_shn_eligibilite.txt', [p for p, _ in notices])

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

    def test_node_metadata_filters_diploma_after_chunking(self):
        docs = [SimpleNamespace(text='INFORMATION CAP À ÉCARTER', metadata={'source': 'cap', 'examens': ['cap']})]
        text, _, _, _ = self.route('Bac général : exporter les élèves', 'Lycée Général & Techno', 'examens', docs)
        self.assertNotIn('INFORMATION CAP À ÉCARTER', text)

    def test_two_passages_with_same_long_prefix_are_kept(self):
        prefix = 'Titre et introduction commune ' * 20
        docs = [SimpleNamespace(text=prefix + suffix, metadata={'source': 'gt', 'examens': ['gt']})
                for suffix in ('INFORMATION PREMIÈRE', 'INFORMATION SECONDE')]
        text, _, _, _ = self.route('Bac général : exporter les élèves', 'Lycée Général & Techno', 'examens', docs)
        self.assertIn('INFORMATION PREMIÈRE', text)
        self.assertIn('INFORMATION SECONDE', text)

    def test_explicit_dnb_overrides_selected_pro_cap_public(self):
        self.assertEqual(kc.clarification('DNB : où saisir la note EPS ?', 'Lycée Pro / CAP'), '')

    def test_medical_code_requires_type_and_duration(self):
        for q in ('Bac pro : inaptitude temporaire, je saisis DI ?',
                  'CAP : inaptitude partielle, je saisis DI ?'):
            self.assertTrue(kc.clarification(q, 'Lycée Pro / CAP'))

    def test_missing_context_and_semantic_rewrite_regressions(self):
        text, _, _, _ = self.route('Quel bouton pour une action inconnue ?', 'Lycée Général & Techno', 'ipack')
        self.assertEqual(text, '')
        code = Path('app.py').read_text()
        self.assertIn('if besoin_ia and (erreur_rag or not extraits_doc)', code)
        self.assertNotIn('re.sub(r"santorin", "LSU / dossier scolaire"', code)


if __name__ == '__main__':
    unittest.main()
