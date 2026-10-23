import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from navigation_restore import ROOT, CHAIN, restore_navigation
from documentary_review import mark_excerpt, source_packets, compact_model_packet, review_exam_answer

class NavigationRestoreTests(unittest.TestCase):
    def fixture(self):
        path='data/examens/complement_saisie_bloquee_diagnostic.txt'
        packets=source_packets(mark_excerpt((ROOT/path).read_text(),path=path,title='Diagnostic logiciel'))
        model=[compact_model_packet(p) for p in packets]
        span=next(s for s in model[0]['passages'] if '[Correction] > [Liste des lots]' in s['text'])
        claim={'section':'etape','text':"Demander au chef d'établissement d'intervenir si un cadenas rouge ou fermé apparaît sur le lot.",
               'evidence':[{'document_id':packets[0]['id'],'passage_ids':[span['id']]}]}
        return {'claims':[claim]},[copy.deepcopy(claim)],packets,model,span
    def test_exact_passage_and_original_immutable(self):
        final,accepted,packets,model,span=self.fixture();before=copy.deepcopy(final)
        result,report=restore_navigation(final,accepted,packets,model)
        self.assertEqual(result['claims'][0]['text'],span['text'])
        self.assertEqual(final,before)
        self.assertEqual(result['claims'][0]['evidence'],final['claims'][0]['evidence'])
        self.assertEqual(report['extra_ai_calls'],0)
    def test_requires_accepted_single_citation_and_transmission(self):
        for case in ('rejected','multiple','absent','academique','non_etape'):
            final,accepted,packets,model,span=self.fixture()
            if case=='rejected':accepted=[]
            elif case=='multiple':
                final['claims'][0]['evidence'][0]['passage_ids'].append('D1P99');accepted=copy.deepcopy(final['claims'])
            elif case=='absent':model=[]
            elif case=='academique':span['scope']['level']='academique'
            elif case=='non_etape':
                final['claims'][0]['section']='limite';accepted=copy.deepcopy(final['claims'])
            result,report=restore_navigation(final,accepted,packets,model)
            self.assertEqual(report['replacements'],[],case)
            self.assertEqual(result,final)
    def test_no_change_when_path_present_or_file_not_registered(self):
        final,accepted,packets,model,span=self.fixture()
        final['claims'][0]['text']=span['text'];accepted=copy.deepcopy(final['claims'])
        self.assertEqual(restore_navigation(final,accepted,packets,model)[1]['replacements'],[])
        final,accepted,packets,model,span=self.fixture();packets[0]['path']='data/inconnu.txt'
        self.assertEqual(restore_navigation(final,accepted,packets,model)[1]['replacements'],[])
    def test_changed_source_and_missing_registry_abstain(self):
        final,accepted,packets,model,span=self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir()
            self.assertEqual(restore_navigation(final,accepted,packets,model,root)[1]['replacements'],[])
            registry=(ROOT/'config/navigation_restore_pilot.json').read_text();(root/'config/navigation_restore_pilot.json').write_text(registry)
            path=root/packets[0]['path'];path.parent.mkdir(parents=True);path.write_text('modifié')
            self.assertEqual(restore_navigation(final,accepted,packets,model,root)[1]['skipped'][0]['reason'],'source_modifiee')
    def test_ten_real_files_structural_omission_scenarios(self):
        registry=json.loads((ROOT/'config/navigation_restore_pilot.json').read_text())
        self.assertEqual(len(registry['sources']),10)
        for source in registry['sources']:
            with self.subTest(path=source['path']):
                body=(ROOT/source['path']).read_text()
                self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),source['sha256'])
                packets=source_packets(mark_excerpt(body,path=source['path']))
                model=[compact_model_packet(p) for p in packets]
                candidates=[(p,s) for p in model for s in p['passages'] if CHAIN.search(s['text'])]
                for p,span in candidates:
                    claim={'section':'etape','text':'Effectuer la manipulation documentée.',
                           'evidence':[{'document_id':p['id'],'passage_ids':[span['id']]}]}
                    final={'claims':[claim]}
                    result,report=restore_navigation(final,[claim],packets,model)
                    if report['replacements']:
                        self.assertEqual(result['claims'][0]['text'],span['text'])
                    else:self.assertEqual(result,final)
    def test_rendered_answer_restores_without_second_generation(self):
        final,accepted,packets,model,span=self.fixture()
        class Fake:
            model='offline';temperature=0
            def __init__(self):self.calls=0
            def complete(self,prompt):
                self.calls+=1
                return type('Response',(),{'text':json.dumps(final)})()
        llm=Fake();audit={};path=packets[0]['path']
        answer=review_exam_answer(llm,question='Je ne peux plus saisir les notes dans Santorin',public='Lycée Général & Techno',
            documents=mark_excerpt((ROOT/path).read_text(),path=path,title='Diagnostic logiciel'),audit=audit,repair_enabled=False)
        self.assertEqual(llm.calls,1)
        self.assertTrue(audit['navigation_restore']['applied'])
        self.assertIn('[Correction]',answer);self.assertIn('[Liste des lots]',answer)
        self.assertEqual(audit['proposal']['claims'][0]['text'],final['claims'][0]['text'])

    def test_candidate_rejected_by_existing_validation_keeps_original(self):
        from unittest.mock import patch
        import documentary_review
        final,accepted,packets,model,span=self.fixture()
        class Fake:
            model='offline';temperature=0
            def __init__(self):self.calls=0
            def complete(self,prompt):
                self.calls+=1
                return type('Response',(),{'text':json.dumps(final)})()
        original=documentary_review.validate_claims;seen={'n':0}
        def controlled(*args,**kwargs):
            seen['n']+=1
            if seen['n']==2:return [],[{'errors':['refus simulé du candidat']}]
            return original(*args,**kwargs)
        llm=Fake();audit={};path=packets[0]['path']
        with patch('documentary_review.validate_claims',side_effect=controlled):
            answer=review_exam_answer(llm,question='Je ne peux plus saisir les notes dans Santorin',public='Lycée Général & Techno',
                documents=mark_excerpt((ROOT/path).read_text(),path=path,title='Diagnostic logiciel'),audit=audit,repair_enabled=False)
        self.assertFalse(audit['navigation_restore']['applied'])
        self.assertEqual(audit['final_claims'],final['claims'])
        self.assertEqual(llm.calls,1)

if __name__=='__main__':unittest.main()
