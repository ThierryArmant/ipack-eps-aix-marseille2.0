import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from document_selector import profile, select_documents, candidate_pool, MAX_PROMPT_CHARS
from documentary_review import review_exam_answer, mark_excerpt, source_packets, TracedLLM, usage_summary
from test_documentary_review import FakeLLM as RawFakeLLM, DOC, claim


def choice(status, ids, objet='', checks=None):
    return {'status':status, 'ids':ids, 'objet':objet,
            'compatibilites':checks if checks is not None else [
                {'id':i,'operation':'directe','conditions':'etablies'} for i in ids]}


class FakeLLM(RawFakeLLM):
    def __init__(self, outputs):
        # Anciens scénarios : déclarer explicitement leur hypothèse de compatibilité.
        outputs = [choice(x['status'], x['ids'], x.get('objet',''))
                   if isinstance(x,dict) and set(x)=={'status','ids','objet'} else x for x in outputs]
        super().__init__(outputs)


class SelectorTests(unittest.TestCase):
    def choose(self, output, documents=DOC, question='Ouvrir le dossier', **kwargs):
        audit={};llm=FakeLLM([output])
        with patch('document_selector.catalogue_candidates', return_value=[]):
            result=select_documents(llm,source_packets(documents),question=question,public='Lycée Général & Techno',
                                    mode='ipack',academy='Non précisée',audit=audit,**kwargs)
        return result,audit,llm

    def test_mixed_real_profile_exposes_gt_branch_without_pro_condition(self):
        text = Path('data/examens/complement_saisie_bloquee_diagnostic.txt').read_text()
        packet = {'id':'D1', 'title':'Diagnostic de saisie', 'text':text, 'scopes':['gt','pro','cap']}
        gt = profile(packet, 'La saisie des évaluations est bloquée', 'Lycée Général & Techno')
        self.assertIn('Au bac GT', gt['branche_public_extrait'])
        self.assertIn('AFL1', gt['branche_public_extrait'])
        self.assertNotIn('Au bac professionnel', gt['demande_proche_extrait'])
        self.assertFalse(any(line.startswith('Au bac professionnel') for line in gt['conditions_extraits']))
        pro = profile(packet, 'La saisie des évaluations est bloquée', 'Lycée Pro / CAP')
        self.assertIn('Au bac professionnel', pro['branche_public_extrait'])
        self.assertIn('AFLP', pro['branche_public_extrait'])
        self.assertEqual(packet['text'], text)

    def test_public_description_keeps_exact_symptom_and_comparisons(self):
        text = ('Au bac GT, vérifier la première valeur.\n'
                'Au bac professionnel uniquement, vérifier le choix.\n'
                'Si un cadenas apparaît sur le lot verrouillé, contacter la direction.')
        packet = {'id':'D1', 'title':'Diagnostic', 'text':text}
        card = profile(packet, 'Mon lot est verrouillé avec un cadenas', 'Lycée Général & Techno')
        self.assertIn('cadenas', card['demande_proche_extrait'])
        card = profile(packet, 'Comparer le bac GT au bac professionnel', 'Lycée Général & Techno')
        self.assertEqual(card['branche_public_extrait'], '')
        self.assertTrue(any('professionnel' in x for x in card['limites_extraits']))

    def test_gt_card_and_condition_contract_reach_selector_at_one_call(self):
        text = Path('data/examens/complement_saisie_bloquee_diagnostic.txt').read_text()
        docs = mark_excerpt(text, path='data/examens/complement_saisie_bloquee_diagnostic.txt',
                            title='Santorin — Diagnostic de saisie')
        result, audit, llm = self.choose(choice('ambiguous', ['D1'], checks=[
            {'id':'D1','operation':'directe','conditions':'inconnues'}]), documents=docs,
            question='La saisie des évaluations est bloquée')
        self.assertIn('Au bac GT', audit['cards'][0]['branche_public_extrait'])
        self.assertIn('Le seul diplôme compatible ne prouve pas', llm.prompts[0])
        self.assertIn("n'impose pas une clarification", llm.prompts[0])
        self.assertIn('Choisis assez de fiches', llm.prompts[0])
        self.assertEqual(audit['status'], 'ambiguous')
        self.assertEqual(result[0]['text'].strip(), text.strip())
        self.assertEqual(len(llm.prompts), 1)
        self.assertLessEqual(len(llm.prompts[0]), MAX_PROMPT_CHARS)

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

    def test_no_match_on_partial_descriptions_preserves_full_review(self):
        selector=FakeLLM([{'status':'no_match','ids':[],'objet':'objet non couvert'}]);writer=FakeLLM([{'claims':[]}]);audit={}
        with patch('document_selector.catalogue_candidates', return_value=[]):
            answer=review_exam_answer(writer,question='Information non couverte par ces fiches',public='Lycée Général & Techno',
                documents=DOC,audit=audit,selector_llm=selector,selection_policy='gpt_shortlist',mode='ipack')
        self.assertIn('Aucune consigne',answer);self.assertEqual(len(writer.prompts),1)
        self.assertEqual(audit['document_orientation']['status'],'no_match_full_review')
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

class CompatibilityTests(unittest.TestCase):
    choose = SelectorTests.choose
    def test_unknown_condition_retains_evidence_as_ambiguous(self):
        output=choice('selected',['D1'],checks=[{'id':'D1','operation':'directe','conditions':'inconnues'}])
        result,audit,_=self.choose(output)
        self.assertEqual(audit['status'],'ambiguous')
        self.assertEqual([p['id'] for p in result],['D1'])

    def test_neighbor_operation_cannot_become_selected_evidence(self):
        output=choice('selected',['D1'],checks=[{'id':'D1','operation':'voisine','conditions':'etablies'}])
        result,audit,_=self.choose(output)
        self.assertIsNone(result)
        self.assertEqual(audit['excluded_incompatible_ids'],['D1'])
        self.assertEqual(audit['status'],'no_match_full_review')

    def test_incompatible_branch_removed_but_direct_branch_preserved(self):
        docs=DOC+'\n'+mark_excerpt('Autre procédure.',title='Autre opération')
        checks=[{'id':'D1','operation':'directe','conditions':'etablies'},
                {'id':'D2','operation':'directe','conditions':'incompatibles'}]
        result,audit,_=self.choose(choice('selected',['D1','D2'],checks=checks),docs)
        self.assertEqual([p['id'] for p in result],['D1'])
        self.assertEqual(audit['excluded_incompatible_ids'],['D2'])

    def test_missing_compatibility_is_invalid_without_retry(self):
        audit={};llm=RawFakeLLM([{'status':'selected','ids':['D1'],'objet':''}])
        with patch('document_selector.catalogue_candidates',return_value=[]):
            result=select_documents(llm,source_packets(DOC),question='Ouvrir dossier',
                public='Lycée Général & Techno',mode='ipack',academy='Non précisée',audit=audit)
        self.assertIsNone(result);self.assertEqual(audit['status'],'fallback_error')
        self.assertEqual(len(llm.prompts),1)

    def test_ambiguous_writer_receives_no_assumed_branch(self):
        selector=FakeLLM([choice('selected',['D1'],checks=[
            {'id':'D1','operation':'incertaine','conditions':'inconnues'}])])
        writer=RawFakeLLM([{'claims':[]}]);audit={}
        with patch('document_selector.catalogue_candidates',return_value=[]):
            review_exam_answer(writer,question='Ouvrir dossier',public='Lycée Général & Techno',
                documents=DOC,selector_llm=selector,selection_policy='gpt_shortlist',audit=audit,mode='ipack')
        self.assertIn('Ne transforme pas cette incertitude en fait acquis',writer.prompts[0])
        self.assertEqual(len(writer.prompts),1)

class ProfileOperationTests(unittest.TestCase):
    def test_procedure_heading_beats_general_introduction(self):
        packet={'id':'D1','title':'Manuel des supports','text':
            "Présentation : la plateforme permet de préparer, distribuer, ouvrir et vérifier les supports.\n"
            "Support incomplet : ouvrir le volet de signalement puis décrire les pages manquantes.\n"
            "Validation : contrôler le traitement des supports.", 'scopes':[]}
        card=profile(packet,'Mon support est incomplet : comment le signaler sur la plateforme ?')
        self.assertTrue(card['demande_proche_extrait'].startswith('Support incomplet :'))
        self.assertIn('volet de signalement',card['demande_proche_extrait'])

    def test_article_text_is_not_discarded_as_metadata(self):
        packet={'id':'D1','title':'Article','text':
            '- Mots-clés : plateforme, support\n- Texte: Accès au support : [Tableau] > [Gestion] > [Ouvrir].',
            'scopes':[]}
        card=profile(packet,'Où accéder au support ?')
        self.assertIn('[Gestion]',card['demande_proche_extrait'])
        self.assertNotIn('Mots-clés',card['demande_proche_extrait'])

class CompleteSectionTests(unittest.TestCase):
    def test_fragments_share_one_complete_section_and_keep_other_sections_out(self):
        from document_selector import complete_candidate_sections
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir();(root/'data/ipack').mkdir(parents=True)
            (root/'config/catalogue_documents.json').write_text('{}')
            path='data/ipack/manual.txt'
            (root/path).write_text('[SITUATION: GESTION DU SUPPORT]\nProcédure : ouvrir le support.\n'
                'Restriction : opération réservée au responsable.\n'
                '[SITUATION: AUTRE OPERATION]\nAUTRE_SECTION_A_EXCLURE')
            packets=[{'id':'D1','path':path,'title':'[SITUATION: GESTION DU SUPPORT]',
                      'text':'Procédure : ouvrir le support.','origin':'document','passages':[{'id':'D1P1'}]},
                     {'id':'D2','path':path,'title':'[SITUATION: GESTION DU SUPPORT]',
                      'text':'Restriction : opération réservée au responsable.','origin':'document'}]
            result=complete_candidate_sections(packets,root)
            self.assertEqual(len(result),1)
            self.assertIn('Restriction',result[0]['text'])
            self.assertNotIn('AUTRE_SECTION_A_EXCLURE',result[0]['text'])
            self.assertNotIn('passages',result[0])
            self.assertIn('passages',packets[0])

    def test_reconstructed_section_replaces_audit_and_renumbers_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir();(root/'data/ipack').mkdir(parents=True)
            (root/'config/catalogue_documents.json').write_text('{}')
            path='data/ipack/manual.txt'
            (root/path).write_text('[SITUATION: OUVRIR LE SUPPORT]\nOuvrir le support.\nRestriction : rôle attribué.')
            docs=mark_excerpt('Ouvrir le support.',path=path,title='[SITUATION: OUVRIR LE SUPPORT]')
            from document_selector import candidate_pool as real_pool
            def pool(*args,**kwargs):
                kwargs["root"]=root
                return real_pool(*args,**kwargs)
            selector=FakeLLM([choice('selected',['D1'])]);writer=RawFakeLLM([{'claims':[]}]);audit={}
            with patch('document_selector.candidate_pool',side_effect=pool):
                review_exam_answer(writer,question='Ouvrir le support',public='Lycée Général & Techno',
                    documents=docs,selector_llm=selector,selection_policy='gpt_shortlist',audit=audit,mode='ipack')
            document=next(x for x in audit['documents'] if x['id']=='D1')
            self.assertIn('Restriction',document['text'])
            self.assertTrue(all(x['id'].startswith('D1P') for x in document['passages']))
            self.assertIn('Restriction',writer.prompts[0])

if __name__=='__main__':unittest.main()
