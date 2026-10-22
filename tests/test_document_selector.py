import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from document_selector import profile, select_documents, candidate_pool, MAX_PROMPT_CHARS
from documentary_review import review_exam_answer, mark_excerpt, source_packets, TracedLLM, usage_summary
from test_documentary_review import FakeLLM, DOC, claim

class SelectorTests(unittest.TestCase):
    def choose(self, output, documents=DOC, question='Ouvrir le dossier', **kwargs):
        audit={};llm=FakeLLM([output])
        with patch('document_selector.catalogue_candidates', return_value=[]):
            result=select_documents(llm,source_packets(documents),question=question,public='Lycée Général & Techno',
                                    mode='ipack',academy='Non précisée',audit=audit,**kwargs)
        return result,audit,llm

    def test_compact_descriptions_not_full_proof(self):
        text='Réponse directe : ouvrir le dossier.\nSi le rôle est attribué, agir.\nNe pas confondre avec le lot.\n'+('détail '*3000)
        docs=mark_excerpt(text,title='Dossier',priority=300)
        result,audit,llm=self.choose({'status':'selected','ids':['D1'],'objet':'ouvrir le dossier'},docs)
        self.assertEqual(result[0]['text'],text)
        self.assertNotIn('détail '*100,llm.prompts[0])
        self.assertIn('Ne pas confondre',llm.prompts[0])
        self.assertLessEqual(len(llm.prompts[0]),MAX_PROMPT_CHARS)

    def test_invalid_schema_or_invented_identifier_falls_back_without_retry(self):
        for output in [{'status':'selected','ids':['D999'],'objet':''}, {'status':'selected','ids':['D1','D1'],'objet':''},
                       {'status':'no_match','ids':['D1'],'objet':''},'not json',{'status':'selected','ids':[],'objet':''}]:
            result,audit,llm=self.choose(output)
            self.assertIsNone(result);self.assertEqual(audit['status'],'fallback_error');self.assertEqual(len(llm.prompts),1)

    def test_ambiguous_preserves_multiple_branches(self):
        docs=DOC+'\n'+mark_excerpt('Un autre dossier a un autre chemin.',title='Autre dossier')
        result,audit,_=self.choose({'status':'ambiguous','ids':['D1','D2'],'objet':'type de dossier inconnu'},docs)
        self.assertEqual([p['id'] for p in result],['D1','D2'])
        self.assertEqual(audit['status'],'ambiguous')

    def test_no_match_does_not_generate_on_neighbor(self):
        selector=FakeLLM([{'status':'no_match','ids':[],'objet':'objet non couvert'}]);writer=FakeLLM([]);audit={}
        with patch('document_selector.catalogue_candidates', return_value=[]):
            answer=review_exam_answer(writer,question='Information non couverte par ces fiches',public='Lycée Général & Techno',
                documents=DOC,audit=audit,selector_llm=selector,selection_policy='gpt_shortlist',mode='ipack')
        self.assertIn('Aucune consigne',answer);self.assertEqual(writer.prompts,[])
        self.assertEqual(audit['accepted_claims'],[]);self.assertEqual(audit['calls'][0]['stage'],'selection')

    def test_selector_can_keep_lower_priority_before_focus(self):
        docs=mark_excerpt('Une spécialité de professeur.',title='Fiche professeur',priority=330)+ '\n'+DOC
        selector=FakeLLM([{'status':'selected','ids':['D2'],'objet':'ouvrir dossier'}]);writer=FakeLLM([{'claims':[]}]);audit={}
        with patch('document_selector.catalogue_candidates', return_value=[]):
            review_exam_answer(writer,question='Ouvrir le dossier',public='Lycée Général & Techno',documents=docs,
                selector_llm=selector,selection_policy='gpt_shortlist',audit=audit,mode='ipack')
        self.assertEqual(audit['model_document_ids'],['D2'])
        self.assertEqual(audit['effective_selection_policy'],'gpt_shortlist')
        self.assertNotIn('Une spécialité de professeur.',writer.prompts[0])

    def test_catalogue_recovery_has_real_passages_and_valid_ids(self):
        extra={'id':'','path':'data/ipack/fiches/recovered.txt','title':'Dossier','text':'Pour ouvrir le dossier, contactez le responsable habilité.',
               'origin':'document','priority':0,'scopes':[],'url':'','selection':'orientation_catalogue'}
        selector=FakeLLM([{'status':'selected','ids':['R1'],'objet':'ouvrir dossier'}]);writer=FakeLLM([{'claims':[]}]);audit={}
        with patch('document_selector.catalogue_candidates', return_value=[extra]):
            review_exam_answer(writer,question='Ouvrir le dossier',public='Lycée Général & Techno',documents=DOC,
                selector_llm=selector,selection_policy='gpt_shortlist',audit=audit,mode='ipack')
        recovered=next(p for p in audit['documents'] if p['id']=='R1')
        self.assertEqual(recovered['passages'][0]['id'],'R1P1');self.assertEqual(audit['model_document_ids'],['R1'])
        self.assertIn('responsable habilité',writer.prompts[0])

    def test_selector_error_retains_legacy_and_all_evidence_guards(self):
        selector=FakeLLM([TimeoutError('private')]);writer=FakeLLM([{'claims':[claim()]}]);audit={}
        with patch('document_selector.catalogue_candidates', return_value=[]):
            answer=review_exam_answer(writer,question='Ouvrir le dossier',public='Lycée Général & Techno',documents=DOC,
                selector_llm=selector,selection_policy='gpt_shortlist',audit=audit,mode='ipack')
        self.assertTrue(audit['accepted_claims']);self.assertIn('responsable',answer)
        self.assertEqual(audit['effective_selection_policy'],'legacy')
        self.assertNotIn('private',json.dumps(audit))

    def test_selection_does_not_count_as_paid_generation_fallback(self):
        a={'calls':[{'provider':'openai','model':'gpt-4o-mini','stage':'selection'},
                    {'provider':'albert','model':'gpt-oss-120b','stage':'generation','error':'TimeoutError'}]}
        summary=usage_summary(a);self.assertFalse(summary['fallback_used']);self.assertEqual(summary['selection_calls'],1)
        self.assertEqual(summary['generation_calls'],1)
        a['calls'].append({'provider':'openai','model':'gpt-4o-mini','stage':'generation'})
        self.assertTrue(usage_summary(a)['fallback_used'])

    def test_large_question_skips_selection_without_truncating_it(self):
        result,audit,llm=self.choose({},question='question '*1000)
        self.assertIsNone(result);self.assertEqual(llm.prompts,[])

    def test_recovery_separates_compilation_sections_and_does_not_mutate_cached_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir();(root/'data/ipack').mkdir(parents=True)
            (root/'config/catalogue_documents.json').write_text('{}')
            (root/'data/ipack/bank.txt').write_text('### Calendrier de formation\nDates de formation.\n'
                '[ARTICLE 2] Organisation des ateliers collectifs\nRéponse directe : organiser les ateliers collectifs.\n')
            first=candidate_pool([], 'Organiser les ateliers collectifs', 'Lycée Général & Techno', 'ipack', root=root)
            self.assertTrue(any('Organisation des ateliers' in p['title'] for p in first))
            self.assertEqual(first[0]['id'],'R1')
            first[0]['id']='INVALID'
            second=candidate_pool([], 'Organiser les ateliers collectifs', 'Lycée Général & Techno', 'ipack', root=root)
            self.assertEqual(second[0]['id'],'R1')
            self.assertNotIn('Calendrier',second[0]['text'])

    def test_selection_usage_is_separate_from_generation_usage(self):
        usage={'calls':[{'model':'gpt-4o-mini','provider':'openai','stage':'selection',
                        'usage':{'input_tokens':100,'output_tokens':10}},
                       {'model':'gpt-oss-120b','provider':'albert','stage':'generation',
                        'usage':{'input_tokens':900,'output_tokens':90}}]}
        result=usage_summary(usage)
        self.assertEqual(result['total_tokens'],1100)
        self.assertEqual(result['by_stage']['selection']['input_tokens'],100)
        self.assertEqual(result['by_stage']['generation']['input_tokens'],900)
        self.assertFalse(result['fallback_used'])

    def test_profiles_do_not_decide_medical_branch(self):
        permanent=profile({'id':'P','title':'Handicap permanent','text':'Si handicap permanent, soumettre à la commission.','scopes':['gt']})
        temporary=profile({'id':'T','title':'Inaptitude temporaire','text':'Si inaptitude temporaire, transmettre pour information.','scopes':['gt']})
        self.assertNotEqual(permanent['conditions_extraits'],temporary['conditions_extraits'])

if __name__=='__main__':unittest.main()
