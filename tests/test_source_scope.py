import json
import unittest
from pathlib import Path

from documentary_review import mark_excerpt, source_packets, validate_claims, render_claims, review_exam_answer
from source_scope import annotations, select_academy, model_passage
from test_documentary_review import FakeLLM, CHECKS

FRAUD='data/examens/fraude_ccf_eps.txt'


def packets():
    return source_packets(mark_excerpt(Path(FRAUD).read_text(),path=FRAUD,priority=300))


def supported(span,level='reglementaire'):
    return {'section':'decision','text':'Le passage cité décrit la règle à appliquer.',
            'evidence':[{'document_id':'D1','passage_ids':[span['id']],'level':level}],
            'checks':CHECKS.copy()}


class SourceScopeTests(unittest.TestCase):
    def test_registry_is_the_one_supplied_with_all_fiches(self):
        registry=json.loads(Path('config/nature_sources.json').read_text())['fichiers']
        self.assertEqual(len(registry),444)
        self.assertEqual(annotations(FRAUD),registry[FRAUD])

    def test_mixed_fraud_is_never_relabelled_as_only_national_by_model(self):
        ps=packets()
        c=supported(ps[0]['passages'][0])
        good,errors=validate_claims({'claims':[c]},ps)
        self.assertFalse(errors)
        answer=render_claims(good,ps)
        self.assertIn('Fiche mixte : circuit académique + cadre national',answer)
        self.assertNotIn('Texte réglementaire :',answer)

    def test_creteil_marks_inventory_passages_and_preserves_exact_evidence(self):
        original=packets()
        chosen,marked=select_academy(original,'Créteil')
        self.assertTrue(marked)
        foreign=next(s for s in chosen[0]['passages'] if s['scope'].get('not_confirmed_for'))
        sent=model_passage(foreign)
        self.assertIn('Fiche mixte, passage inventorié pour Aix-Marseille',sent['text'])
        self.assertIn('application locale, à vérifier pour Créteil',sent['text'])
        self.assertEqual(foreign['text'],original[0]['text'][foreign['start']:foreign['end']])
        self.assertFalse(any(s['scope'].get('not_confirmed_for') for s in original[0]['passages']))

    def test_software_is_not_promoted_by_model_or_other_academy(self):
        p='data/examens/audit_faq_2026_10_12/k2_procedure_verifiee.txt'
        ps=source_packets(mark_excerpt(Path(p).read_text(),path=p))
        self.assertEqual(select_academy(ps,'Créteil')[1],[])
        good,_=validate_claims({'claims':[supported(ps[0]['passages'][0],level='reglementaire')]},ps)
        answer=render_claims(good,ps)
        self.assertIn('Documentation du logiciel',answer)
        self.assertIn('exemples cités : Dijon, Normandie',answer)
        self.assertNotIn('Texte réglementaire',answer)

    def test_model_cannot_inject_scope_metadata_in_legacy_quote(self):
        ps=source_packets(mark_excerpt('Un document sans nature ni origine établie doit être vérifié.'))
        c={'section':'decision','text':'Vérifiez les sources disponibles.',
           'evidence':[{'document_id':'D1','quote':ps[0]['text'],'level':'documentaire',
                        'scope':{'level':'reglementaire','academy':'Créteil','reference':'faux BO'}}]}
        good,_=validate_claims({'claims':[c]},ps)
        answer=render_claims(good,ps)
        self.assertNotIn('faux BO',answer)
        self.assertNotIn('Texte réglementaire',answer)

    def test_annotated_evidence_requires_identified_passage(self):
        ps=packets()
        c=supported(ps[0]['passages'][0])
        c['evidence'][0]={'document_id':'D1','quote':ps[0]['passages'][0]['text']}
        self.assertFalse(validate_claims({'claims':[c]},ps)[0])

    def test_actual_review_sends_marked_academic_origin_in_one_call(self):
        ps=packets()
        c=supported(ps[0]['passages'][0])
        llm=FakeLLM([{'claims':[c]}])
        audit={}
        review_exam_answer(llm,question='Fraude CCF ?',public='GT',academy='Créteil',
                           documents=mark_excerpt(Path(FRAUD).read_text(),path=FRAUD,priority=300),audit=audit)
        data=json.loads(llm.prompts[0].split('DONNEES :\n',1)[1])
        self.assertEqual(data['academy'],'Créteil')
        self.assertEqual(len(llm.prompts),1)
        self.assertTrue(audit['marked_academic_passages'])
        self.assertIn('Fiche mixte, passage inventorié pour Aix-Marseille',
                      '\n'.join(s['text'] for p in data['documents'] for s in p['passages']))
        self.assertFalse(audit['semantic_review'])


if __name__=='__main__':
    unittest.main()
