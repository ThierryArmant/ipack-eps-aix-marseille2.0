"""Stratégie commune : sélection complémentaire et réparation avec preuves vérifiées."""
import json
from pathlib import Path
from unittest.mock import patch
import unittest
from documentary_review import mark_excerpt, review_exam_answer, source_packets
from document_selector import select_documents
from test_documentary_review import FakeLLM

class SharedStrategyTests(unittest.TestCase):
    def test_complementary_role_sources_survive_but_unrelated_and_incompatible_do_not(self):
        docs = '\n'.join(mark_excerpt(text, title=title) for title, text in [
            ('Fonction', 'Le responsable déclare sa fonction dans sa fiche.'),
            ('Responsabilités', 'Le responsable vérifie puis transmet le dossier.'),
            ('Autre outil', 'Une autre opération concerne un autre outil.'),
            ('Autre régime', 'Un régime différent suit une procédure distincte.')])
        choice = {'status':'selected', 'ids':['D1','D2','D3','D4'], 'objet':'Responsabilités du responsable',
                  'compatibilites':[
                      {'id':'D1','operation':'directe','conditions':'etablies'},
                      {'id':'D2','operation':'complementaire','conditions':'inconnues'},
                      {'id':'D3','operation':'voisine','conditions':'etablies'},
                      {'id':'D4','operation':'complementaire','conditions':'incompatibles'}]}
        llm, audit = FakeLLM([choice]), {}
        with patch('document_selector.catalogue_candidates', return_value=[]):
            selected = select_documents(llm, source_packets(docs), question='Quelles sont les responsabilités de ce rôle ?',
                                        public='Collège', mode='ipack', academy='Non précisée', audit=audit)
        self.assertEqual([p['id'] for p in selected], ['D1','D2'])
        self.assertEqual(audit['status'], 'ambiguous')
        self.assertEqual(audit['excluded_incompatible_ids'], ['D3','D4'])
        self.assertEqual(len(llm.prompts), 1)

    def test_repair_preserves_good_claim_after_an_earlier_bad_reference(self):
        proof = 'Le responsable vérifie le dossier avant sa transmission.'
        valid = {'section':'etape','text':proof,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}
        bad = {'section':'decision','text':'FAUSSE_CONCLUSION_A_NE_PAS_RECOPIER',
               'evidence':[{'document_id':'D404','passage_ids':['D404P1']}]}
        llm, audit = FakeLLM([{'claims':[bad,valid]}, {'claims':[valid]}]), {}
        review_exam_answer(llm, question='Qui vérifie le dossier ?', public='Collège', mode='ipack',
                           documents=mark_excerpt(proof), audit=audit)
        preserved = json.loads(llm.prompts[1].split('AFFIRMATIONS DEJA VALIDEES :\n')[1].split('\nERREURS MECANIQUES :')[0])
        self.assertEqual(preserved, [valid])
        self.assertNotIn(bad['text'], llm.prompts[1])
        self.assertEqual(audit['repair_preserved_claim_count'], 1)
        self.assertEqual(len(llm.prompts), 2)
        self.assertFalse(audit['final_rejections'])

    def test_logically_rejected_claim_is_never_marked_as_already_valid(self):
        proof = 'Le dispositif peut être utilisé après accord du responsable.'
        vague = {'section':'decision','text':'Le dispositif est possible sous certaines conditions.',
                 'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}
        corrected = {'section':'condition','text':proof,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}
        llm, audit = FakeLLM([{'claims':[vague]}, {'claims':[corrected]}]), {}
        review_exam_answer(llm, question='Comment utiliser le dispositif ?', public='Collège',
                           documents=mark_excerpt(proof), audit=audit)
        self.assertEqual(audit['repair_preserved_claim_count'], 0)
        self.assertNotIn(vague['text'], llm.prompts[1])

    def test_common_instructions_have_one_citation_contract_and_bounded_size(self):
        llm, audit = FakeLLM([{'claims':[]}]), {}
        review_exam_answer(llm, question='Où consulter le dossier ?', public='Collège',
                           documents=mark_excerpt('Le dossier peut être consulté dans le tableau de bord.'), audit=audit)
        prompt = llm.prompts[0]
        self.assertEqual(prompt.count('PRIORITÉ : UNE AIDE CORRECTE ET CONCRÈTE'), 1)
        self.assertLess(audit['writer_instruction_chars'], 11000)
        schema = prompt.split('SCHEMA :\n')[1].split('\nCONSIGNES INSTITUTIONNELLES :')[0]
        self.assertEqual(json.loads(schema)['claims'][0]['section'], 'etape')
        self.assertNotIn('Cite seulement les sources qui justifient la conclusion : titre', prompt)
        self.assertEqual(len(llm.prompts), 1)
