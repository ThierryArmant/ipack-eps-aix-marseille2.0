import unittest
from pathlib import Path
from documentary_review import (situation_mismatch, dnb_document_mismatch, mark_excerpt,
    source_packets, validate_claims, review_exam_answer)
from claim_guards import unsupported_certainty, workflow_fidelity_errors
from test_documentary_review import FakeLLM
import test_documentation as routing


class RemainingBlockerTests(unittest.TestCase):
    def test_no_note_is_not_one_note(self):
        q='Élève inapte toute l’année, sans aucune note : coefficient EPS ?'
        proof=Path('data/commun/audit60/inaptitude_totale_annee_terminale.txt').read_text().splitlines()[2]
        self.assertFalse(situation_mismatch(q,proof))
        self.assertTrue(situation_mismatch(q,'Certification sur une seule note.'))
        self.assertTrue(situation_mismatch('Une seule note obtenue : que faire ?', 'Certification sur deux notes.'))

    def test_annual_fiche_proof_is_accepted_without_repair(self):
        path='data/commun/audit60/inaptitude_totale_annee_terminale.txt'
        docs=mark_excerpt(Path(path).read_text(),path=path,title='Bac GT : inaptitude totale annuelle sans évaluation',selection='catalogue',priority=300)
        ps=source_packets(docs)
        span=next(s for s in ps[0]['passages'] if 'moyenne fictive' in s['text'])
        claim={'section':'decision','text':"Si l'inaptitude totale attestée couvre toute l'année sans aucune évaluation possible, la dispense d'EPS conduit à neutraliser son coefficient après traitement du dossier académique.",'evidence':[{'document_id':'D1','passage_ids':[span['id']]}]}
        llm=FakeLLM([{'claims':[claim]}]);a={}
        review_exam_answer(llm,question='Élève inapte toute l’année, aucune note : coefficient EPS ?',public='Lycée Général & Techno',documents=docs,audit=a)
        self.assertEqual(len(llm.prompts),1)
        self.assertFalse(a['final_rejections'])

    def test_generic_video_fiche_not_filtered_for_its_lycee_comparison(self):
        path='data/ipack/fiches/ipack_301_situation_videos_photos_eleves_droit_image_rgpd.txt'
        packet=source_packets(mark_excerpt(Path(path).read_text(),path=path,title='Filmer un élève pour l’évaluer : outil et cadre institutionnel'))[0]
        self.assertFalse(dnb_document_mismatch('Vidéo EPS et RGPD : autorisation parentale ?', 'Collège (DNB)',packet))
        exam=source_packets(mark_excerpt('Saisir les notes du CCF dans Santorin.',path='data/examens/notation.txt',title='Notation CCF Santorin'))[0]
        self.assertTrue(dnb_document_mismatch('Vidéo EPS et RGPD', 'Collège (DNB)',exam))

    def test_video_real_routing_reaches_generation_and_keeps_a_sourced_answer(self):
        q='Vidéo EPS dans iPackEPS : conformité RGPD et autorisation parentale ?'
        harness=routing.DocumentationTests();harness.setUp()
        docs,_,_,_=harness.route(q,'Collège (DNB)','ipack')
        ps=source_packets(docs)
        packet=next(p for p in ps if p['path'].endswith('video_perimetre.txt') or 'ipack_301' in p['path'])
        span=next(s for s in packet['passages'] if 'Informer les élèves' in s['text'])
        claim={'section':'etape','text':"Informer les élèves et utiliser le circuit d’autorisation d’image validé par l’établissement pour les mineurs, en distinguant captation et diffusion.",'evidence':[{'document_id':packet['id'],'passage_ids':[span['id']]}]}
        llm=FakeLLM([{'claims':[claim]}]);a={}
        answer=review_exam_answer(llm,question=q,public='Collège (DNB)',mode='ipack',documents=docs,audit=a)
        self.assertEqual(len(llm.prompts),1)
        self.assertIn('autorisation',answer)
        self.assertNotIn('Aucune consigne applicable',answer)

    def test_report_rule_survives_reservation_on_sending_procedure(self):
        body=Path('data/textes/fiches/accident_eleve_rapport_parents_2009.txt').read_text()
        proof=next(line for line in body.splitlines() if line.startswith("Le chef d'établissement établit"))
        claim="Le chef d'établissement doit établir le rapport d'accident dans les 48 heures."
        self.assertFalse(unsupported_certainty(claim,[proof]))
        self.assertTrue(workflow_fidelity_errors([{'text':'Le délai exact de transmission est de 48 heures.','evidence':[{'quote':proof}]}],'Rapport accident : délai ?'))
        self.assertTrue(unsupported_certainty('La signature des familles est interdite.',["Les sources ne prévoient pas de signature des familles. Faire confirmer par le service."]))

    def test_singular_passage_id_must_still_resolve_to_an_existing_passage(self):
        ps=source_packets(mark_excerpt('Le responsable vérifie le certificat médical avant la décision.'))
        claim={'section':'condition','text':'Le responsable vérifie le certificat médical avant la décision.','evidence':[{'document_id':'D1','passage_id':'D1P1'}]}
        good,bad=validate_claims({'claims':[claim]},ps)
        self.assertTrue(good);self.assertFalse(bad)
        for value in ['', 'D1P999']:
            claim['evidence'][0]['passage_id']=value
            good,bad=validate_claims({'claims':[claim]},ps)
            self.assertFalse(good);self.assertTrue(bad)

    def test_missing_citation_repairs_with_available_ids_without_inventing_one(self):
        proof='Le responsable vérifie le certificat médical avant la décision.'
        bad={'section':'condition','text':proof,'evidence':[{'document_id':'D1','passage_id':''}]}
        good={**bad,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}
        llm=FakeLLM([{'claims':[bad]},{'claims':[good]}]);a={}
        review_exam_answer(llm,question='Qui vérifie le certificat médical ?',public='Lycée Général & Techno',documents=mark_excerpt(proof),audit=a)
        self.assertEqual(len(llm.prompts),2)
        self.assertEqual(a['repair_feedback'][0]['rejected_evidence'][0]['available_passage_ids'],['D1P1'])
        self.assertFalse(a['final_rejections'])

    def test_empty_citation_is_not_automatically_filled_from_claim(self):
        proof='Le responsable vérifie le certificat médical avant la décision.'
        bad={'section':'condition','text':proof,'evidence':[{'document_id':'D1','passage_id':''}]}
        llm=FakeLLM([{'claims':[bad]},{'claims':[bad]}]);a={}
        with self.assertRaises(ValueError):
            review_exam_answer(llm,question='Qui vérifie le certificat médical ?',public='Lycée Général & Techno',documents=mark_excerpt(proof),audit=a)
        self.assertEqual(len(llm.prompts),2)
        self.assertTrue(a['final_rejections'])
