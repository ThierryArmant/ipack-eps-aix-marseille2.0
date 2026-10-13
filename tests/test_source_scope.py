import json
import unittest
from pathlib import Path

from documentary_review import mark_excerpt, source_packets, validate_claims, render_claims, review_exam_answer
from source_scope import annotations, select_academy, model_passage
from test_documentary_review import FakeLLM, CHECKS

FRAUD='data/examens/fraude_ccf_eps.txt'
AIX_PROTOCOLES='data/commun/audit60/aix_protocoles_2026.txt'
MIXTE_AIX='data/examens/audit_faq_2026_10_12/h1_procedure_verifiee.txt'


def packets(path=FRAUD):
    return source_packets(mark_excerpt(Path(path).read_text(),path=path,priority=300))


def supported(span,level='reglementaire'):
    # Une affirmation reprend le vocabulaire du passage qui l'énonce (contrôle lexical).
    return {'section':'decision','text':span['text'][:300],
            'evidence':[{'document_id':'D1','passage_ids':[span['id']],'level':level}],
            'checks':CHECKS.copy()}


class SourceScopeTests(unittest.TestCase):
    def test_registry_is_the_one_supplied_with_all_fiches(self):
        registry=json.loads(Path('config/nature_sources.json').read_text())['fichiers']
        self.assertEqual(len(registry),482)
        self.assertEqual(annotations(FRAUD),registry[FRAUD])

    def test_mixed_fraud_is_never_relabelled_as_only_national_by_model(self):
        ps=packets()
        c=supported(ps[0]['passages'][0])
        good,errors=validate_claims({'claims':[c]},ps)
        self.assertFalse(errors)
        answer=render_claims(good,ps)
        self.assertIn('Passage non attribué — fiche mixte : circuit académique + cadre national',answer)
        self.assertIn('origine académique : Aix-Marseille',answer)
        self.assertNotIn('Texte réglementaire :',answer)

    def test_creteil_keeps_national_fraud_steps_unmarked(self):
        # EX290 : la compétence de la commission de discipline est nationale, pas une consigne d'Aix.
        chosen,marked=select_academy(packets(),'Créteil')
        self.assertEqual(marked,[])
        step4=next(s for s in chosen[0]['passages'] if s['text'].startswith('4. Ne pas saisir de zéro'))
        self.assertNotIn('Consigne de l’académie',model_passage(step4)['text'])

    def test_creteil_marks_inventory_passages_and_preserves_exact_evidence(self):
        original=packets(AIX_PROTOCOLES)
        chosen,marked=select_academy(original,'Créteil')
        self.assertTrue(marked)
        foreign=next(s for s in chosen[0]['passages'] if s['scope'].get('not_confirmed_for'))
        sent=model_passage(foreign)
        self.assertIn('application locale, à vérifier pour Créteil',sent['text'])
        self.assertIn('Créteil',sent['text'])
        self.assertEqual(foreign['text'],original[0]['text'][foreign['start']:foreign['end']])
        self.assertFalse(any(s['scope'].get('not_confirmed_for') for s in original[0]['passages']))

    def test_mixed_fiche_keeps_national_frame_and_flags_local_application(self):
        chosen,marked=select_academy(packets(MIXTE_AIX),'Créteil')
        self.assertTrue(marked)
        foreign=next(s for s in chosen[0]['passages'] if s['scope'].get('not_confirmed_for'))
        sent=model_passage(foreign)['text']
        self.assertIn('Fiche mixte, passage inventorié pour Aix-Marseille',sent)
        self.assertIn('application locale, à vérifier pour Créteil',sent)

    def test_absence_of_aix_instruction_is_not_an_aix_instruction(self):
        import portee_registre
        self.assertEqual(portee_registre.lignes_aix("Aucune consigne académique d’Aix propre à ce cas n’a été trouvée."),[])

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

    def test_unrelated_passage_is_rejected(self):
        # EX290 : une règle sur la fraude ne peut pas être prouvée par la fiche du modèle de PV.
        pv='data/commun/audit60/pv_ccf_prudence.txt'
        ps=packets(pv)
        c=supported(ps[0]['passages'][0])
        c['text']="L'enseignant ne peut pas saisir zéro dans Santorin pour sanctionner un candidat soupçonné de fraude."
        good,errors=validate_claims({'claims':[c]},ps)
        self.assertFalse(good)
        self.assertIn('sans rapport',str(errors))

    def test_annotated_evidence_requires_identified_passage(self):
        ps=packets()
        c=supported(ps[0]['passages'][0])
        c['evidence'][0]={'document_id':'D1','quote':ps[0]['passages'][0]['text']}
        self.assertFalse(validate_claims({'claims':[c]},ps)[0])

    def test_actual_review_sends_marked_academic_origin_in_one_call(self):
        ps=packets(AIX_PROTOCOLES)
        c=supported(ps[0]['passages'][0])
        llm=FakeLLM([{'claims':[c]}])
        audit={}
        review_exam_answer(llm,question='Validation des protocoles ?',public='GT',academy='Créteil',
                           documents=mark_excerpt(Path(AIX_PROTOCOLES).read_text(),path=AIX_PROTOCOLES,priority=300),audit=audit)
        data=json.loads(llm.prompts[0].split('DONNEES :\n',1)[1])
        self.assertEqual(data['academy'],'Créteil')
        self.assertEqual(len(llm.prompts),1)
        self.assertTrue(audit['marked_academic_passages'])
        self.assertIn('application locale, à vérifier pour Créteil',
                      '\n'.join(s['text'] for p in data['documents'] for s in p['passages']))
        self.assertFalse(audit['semantic_review'])

    def test_registry_is_up_to_date_with_fiches(self):
        # Une fiche modifiée sans régénérer le registre laisserait des marques périmées.
        import portee_registre
        registre=json.loads(Path('config/portee_academique.json').read_text(encoding='utf-8'))['fichiers']
        self.assertEqual(registre,portee_registre.inventaire(),
                         'Relancer : python portee_registre.py --write')


if __name__=='__main__':
    unittest.main()
