import html
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from generation_runtime import load_runtime
from exact_source_answer import exact_answer


class ExactSelectionUnitTests(unittest.TestCase):
    def run_case(self, texts, choice, packets=None):
        dr=load_runtime().documentary_review
        docs='\n\n'.join(dr.mark_excerpt(text,path=f'data/exemple{i}.txt',title=f'Source {i}')
                         for i,text in enumerate(texts))
        llm=SimpleNamespace(model='fake',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text=json.dumps(choice))))
        audit={}
        if packets is None:
            answer=exact_answer(llm,reviewer=dr,tracer=dr.TracedLLM,documents=docs,
                question='Comment faire ?',public='p',mode='examens',academy='Non précisée',audit=audit)
        else:
            with patch.object(dr,'source_packets',return_value=packets):
                answer=exact_answer(llm,reviewer=dr,tracer=dr.TracedLLM,documents=docs,
                    question='Comment faire ?',public='p',mode='examens',academy='Non précisée',audit=audit)
        return answer,audit,llm

    def test_harmless_repetition_is_traced_and_does_not_discard_proof(self):
        choice={'principal':'D1','complements':['D1','D2','D2'],
                'passages':['D1P1','D1P1','D2P1']}
        out,a,llm=self.run_case(['Action si la condition existe.','Ne pas supprimer les notes.'],choice)
        e=a['exact_extracts']
        self.assertEqual(e['status'],'rendered_exact_sources')
        self.assertEqual(e['raw_selection'],choice)
        self.assertEqual(e['normalized_selection'],
            {'principal':'D1','complements':['D2'],'passages':['D1P1','D2P1']})
        self.assertEqual(len(e['deduplications']),3)
        lead=out.split('<details>')[0]
        self.assertEqual(lead.count('Ne pas supprimer les notes.'),1)
        llm.complete.assert_called_once()

    def test_invented_ids_are_dropped_and_traced_when_valid_ones_remain(self):
        # 25 octobre (Claude, essai à l'aveugle) : un identifiant inventé ne bloque plus toute la sélection.
        for choice in [
            {'principal':'D1','complements':['D1','D99'],'passages':['D1P1']},
            {'principal':'D1','complements':[{}],'passages':['D1P1']}]:
            with self.subTest(choice=choice):
                _,a,llm=self.run_case(['Action.'],choice)
                self.assertEqual(a['exact_extracts']['status'],'rendered_exact_sources')
                self.assertTrue(a['exact_extracts']['identifiants_inconnus_ecartes'])
                llm.complete.assert_called_once()

    def test_unknown_or_wrong_types_are_not_repaired_by_deduplication(self):
        for choice in [
            {'principal':'D1','complements':['D1'],'passages':['D99P1','D99P1']},
            {'principal':None,'complements':['D1'],'passages':[]}]:
            with self.subTest(choice=choice):
                _,a,llm=self.run_case(['Action.'],choice)
                self.assertEqual(a['exact_extracts']['status'],'invalid_selection_no_retry')
                llm.complete.assert_called_once()

    def test_search_lines_removed_from_selector_but_stay_in_audit_and_full_source(self):
        text='- Mots-clés : importer, classe.\n\nAction : importer après validation.\n\n- Formulations courantes des collègues : comment importer ?'
        out,a,llm=self.run_case([text],{'principal':'D1','complements':[], 'passages':['D1P2']})
        payload=json.loads(llm.complete.call_args.args[0].split('DONNEES :\n')[1])
        self.assertEqual([s['id'] for s in payload['documents'][0]['passages']],['D1P2'])
        self.assertEqual(a['exact_extracts']['excluded_search_metadata'],['D1P1','D1P3'])
        self.assertEqual(len(a['documents'][0]['passages']),3)
        self.assertIn('Mots-clés',out.split('<summary>Consulter les passages complets</summary>',1)[1])

    def test_metadata_cannot_be_selected_and_mixed_business_span_is_kept(self):
        _,a,llm=self.run_case(['Mots-clés : importer.\n\nAction : valider.'],
            {'principal':'D1','complements':[],'passages':['D1P1']})
        self.assertEqual(a['exact_extracts']['status'],'invalid_selection_no_retry')
        llm.complete.assert_called_once()
        text='Mots-clés : importer.\nNe pas supprimer les notes.'
        out,a,_=self.run_case([text],{'principal':'D1','complements':[],'passages':['D1P1']})
        self.assertEqual(a['exact_extracts']['excluded_search_metadata'],[])
        self.assertIn(html.escape(text),out)

    def test_section_title_and_distinct_scopes_are_preserved_without_merging(self):
        dr=load_runtime().documentary_review
        packet=dr.source_packets(dr.mark_excerpt('Exemple.',path='data/exemple.txt',title='Fiche'))[0]
        packet['passages']=[dict(id='D1P1',text='Condition nationale.',section='Action <A>',scope={'level':'logiciel'}),
                            dict(id='D1P2',text='À Aix-Marseille seulement : prévenir le service.',section='Action <A>',
                                 scope={'level':'academique','academy':'Aix-Marseille'}),
                            dict(id='D1P3',text='Une autre opération.',section='Autre action',scope={'level':'logiciel'})]
        out,a,llm=self.run_case(['Exemple.'],
            {'principal':'D1','complements':[],'passages':['D1P1','D1P2']},[packet])
        lead=out.split('<details>')[0]
        self.assertEqual(lead.count('<h4>Action &lt;A&gt;</h4>'),1)
        self.assertNotIn('<A>',out)
        self.assertIn('À Aix-Marseille seulement',lead)
        self.assertEqual([s['scope'] for s in a['documents'][0]['passages']],
                         [s['scope'] for s in packet['passages']])
        payload=json.loads(llm.complete.call_args.args[0].split('DONNEES :\n')[1])
        section_id=payload['documents'][0]['passages'][0]['section']
        self.assertEqual(payload['sections'][section_id],{'title':'Action <A>','origin':'source_heading'})
        self.assertNotIn('Une autre opération.',lead)

    def test_excerpt_without_raw_heading_keeps_explicit_document_title_origin(self):
        out,a,llm=self.run_case(['Ne pas effacer les notes.'],
            {'principal':'D1','complements':[],'passages':['D1P1']})
        payload=json.loads(llm.complete.call_args.args[0].split('DONNEES :\n')[1])
        key=payload['documents'][0]['passages'][0]['section']
        self.assertEqual(payload['sections'][key],{'title':'Source 0','origin':'document_title'})
        self.assertIn('<h4>Source 0</h4>',out)
        self.assertEqual(a['exact_extracts']['focused_sections'][0]['section_origin'],'document_title')


if __name__=='__main__':unittest.main()
