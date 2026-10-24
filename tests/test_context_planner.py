import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from context_planner import plan_context


def packet(i, text, origin='document'):
    return dict(id=i, origin=origin, title=text, text=text,
                passages=[dict(id=i+'P1', text=text, scope={'level':'logiciel'})])


class ContextPlannerTests(unittest.TestCase):
    def plan(self, packets, rows, question='Comment réaliser A puis B ?'):
        audit = {}
        llm = Mock()
        llm.complete.return_value = SimpleNamespace(text=json.dumps({'documents': rows}))
        result = plan_context(llm, question=question, public='Collège', mode='ipack',
                              academy='Non précisée', packets=packets, audit=audit)
        return result, audit, llm

    def row(self, p, role):
        return dict(id=p['id'], role=role, passage_id=p['passages'][0]['id'],
                    quote=p['passages'][0]['text'])

    def test_preserves_whole_prerequisites_limits_uncertain_and_multiple_actions(self):
        packets = [packet('D1', 'Avant A, accomplir C dans un autre outil.'),
                   packet('D2', 'A seulement si la validation a été reçue ; sinon attendre.'),
                   packet('D3', 'Pour B, effectuer les étapes documentées.'),
                   packet('D4', 'Limite applicable à A dans cette académie.'),
                   packet('D5', 'Une autre branche pourrait être utile.'),
                   packet('D6', 'Opération distincte sans lien nécessaire.'),
                   packet('D7', 'Fait calculé du programme', 'program')]
        before = copy.deepcopy(packets)
        roles = ['prealable', 'principal', 'complement', 'limite', 'incertain', 'voisin']
        result, audit, llm = self.plan(packets, [self.row(p, role) for p, role in zip(packets, roles)])
        self.assertEqual([p['id'] for p in result], ['D2','D1','D3','D4','D5','D7'])
        self.assertEqual(packets, before)
        for p in result:
            self.assertIs(p, next(x for x in packets if x['id']==p['id']))
        self.assertEqual(audit['excluded_neighbor_ids'], ['D6'])
        self.assertFalse(audit['semantic_roles_proven'])
        llm.complete.assert_called_once()

    def test_invalid_duplicate_or_fabricated_citation_keeps_everything(self):
        packets=[packet('D1','Action A'),packet('D2','Autre action')]
        valid=[self.row(p, 'principal') for p in packets]
        variants=[[valid[0],valid[0]],
                  [dict(valid[0],quote='inventé'), valid[1]],
                  [dict(valid[0],passage_id='D2P1'),valid[1]],
                  [dict(valid[0],role='incompatible'),valid[1]]]
        for rows in variants:
            with self.subTest(rows=rows):
                result, audit, _=self.plan(packets, rows)
                self.assertIs(result, packets)
                self.assertEqual(audit['status'],'fallback_invalid_full_context')

    def test_partial_plan_keeps_unclassified_and_only_excludes_explicit_neighbor(self):
        packets=[packet('D1','Préalable encore non classé'),packet('D2','Action principale'),
                 packet('D3','Opération distincte')]
        rows=[self.row(packets[1],'principal'), self.row(packets[2],'voisin')]
        result,audit,_=self.plan(packets,rows)
        self.assertEqual([p['id'] for p in result],['D2','D1'])
        self.assertEqual(audit['status'],'planned_partial')
        self.assertEqual(audit['unclassified_ids'],['D1'])
        self.assertIs(result[1],packets[0])

    def test_compact_schema_copies_witness_from_source(self):
        packets=[packet('D1','Condition indispensable'),packet('D2','Opération distincte')]
        rows=[dict(id='D1',role='principal',passage_id='D1P1'),
              dict(id='D2',role='voisin',passage_id='D2P1')]
        result,audit,_=self.plan(packets,rows)
        self.assertEqual(result,[packets[0]])
        self.assertEqual(audit['decisions'][0]['source_passage'],'Condition indispensable')

    def test_no_main_document_does_not_turn_uncertainty_into_empty_answer(self):
        packets=[packet('D1','Limite A'),packet('D2','Autre A')]
        result, audit, _=self.plan(packets,[self.row(p,'voisin') for p in packets])
        self.assertIs(result,packets)
        self.assertEqual(audit['status'],'fallback_no_principal_full_context')

    def test_long_context_is_not_truncated_and_makes_no_call(self):
        packets=[packet('D1','Texte long '+('a'*41000)),packet('D2','Autre action')]
        result,audit,llm=self.plan(packets,[])
        self.assertIs(result,packets)
        self.assertEqual(audit['status'],'fallback_budget_full_context')
        llm.complete.assert_not_called()

    def test_one_document_needs_no_model(self):
        packets=[packet('D1','Action A')]
        result,audit,llm=self.plan(packets,[])
        self.assertIs(result,packets)
        llm.complete.assert_not_called()

    def test_general_question_keeps_all_responsibilities_without_four_document_cap(self):
        packets=[packet('D'+str(i), 'Responsabilité '+str(i)) for i in range(1,9)]
        result,audit,_=self.plan(packets,[self.row(p,'principal') for p in packets],
                                 question='Quel est le rôle du coordonnateur ?')
        self.assertEqual(result,packets)
        self.assertEqual(len(result),8)


class PlannedComparisonTests(unittest.TestCase):
    def test_no_reduction_does_not_pay_for_another_writer(self):
        import architecture_comparison as ac
        dr=ac._runtime.documentary_review
        docs='\n\n'.join(dr.mark_excerpt(text,path='data/test'+str(i)+'.txt',title=text)
                         for i,text in enumerate(['Procédure utile','Élément non classé']))
        p=dr.source_packets(docs)[0]
        llm=SimpleNamespace(model='gpt-4o-mini',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text=json.dumps({'documents':[
                dict(id=p['id'],role='principal',passage_id=p['passages'][0]['id'])]}))))
        with patch('architecture_comparison.review_exam_answer',return_value='A') as review:
            result=ac.run_comparison(llm=llm,retrieve=lambda *args:(docs,[],[],''),
                question='Question',public='p',mode='examens',academy='Aix-Marseille',
                version='test',experimental='F')
        review.assert_called_once()
        item=result['branches']['F']
        self.assertEqual(item['state'],'context_not_reduced')
        self.assertNotIn('answer',item)
        self.assertEqual(item['usage']['generation_calls'],0)

    def test_f_reuses_search_preserves_passages_and_does_not_change_e(self):
        import architecture_comparison as ac
        dr=ac._runtime.documentary_review
        docs='\n\n'.join(dr.mark_excerpt(text, path='data/test'+str(i)+'.txt', title=text)
                          for i,text in enumerate(['Opération voisine','Procédure principale si condition vraie']))
        parsed=dr.source_packets(docs)
        decisions=[dict(id=p['id'],role=role,passage_id=p['passages'][0]['id'],quote=p['passages'][0]['text'])
                   for p,role in zip(parsed,['voisin','principal'])]
        llm=SimpleNamespace(model='gpt-4o-mini',temperature=0,
            complete=Mock(return_value=SimpleNamespace(text=json.dumps({'documents':decisions}))))
        retrieve=Mock(return_value=(docs,[],[],''))
        with patch('architecture_comparison.review_exam_answer',return_value='réponse') as review:
            result=ac.run_comparison(llm=llm,retrieve=retrieve,question='Question',public='p',
                                    mode='examens',academy='Aix-Marseille',version='test',experimental='F')
        retrieve.assert_called_once()
        self.assertEqual(review.call_count,2)
        a,f=review.call_args_list
        self.assertEqual(a.kwargs['instructions'],f.kwargs['instructions'])
        self.assertEqual(a.kwargs['question'],f.kwargs['question'])
        kept=dr.source_packets(f.kwargs['documents'])
        self.assertEqual(len(kept),1)
        self.assertEqual(kept[0]['text'],parsed[1]['text'])
        self.assertEqual([s['text'] for s in kept[0]['passages']], [s['text'] for s in parsed[1]['passages']])
        self.assertEqual(result['branches']['F']['usage']['selection_calls'],1)
        self.assertEqual(result['branches']['F']['retrieved_documents'],docs)
