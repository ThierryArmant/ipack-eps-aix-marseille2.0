import unittest
from pathlib import Path
from documentary_review import mark_excerpt, source_packets, validate_claims, render_claims, conditional_extraction_errors, review_exam_answer
from test_documentary_review import FakeLLM

FAQ='data/examens/audit_faq_2026_10_12/d3_procedure_verifiee.txt'
RULE='data/examens/situations_2026_10_13/gt_une_seule_note_sur_trois.txt'


class DiSourceAndConditionTests(unittest.TestCase):
    def test_teacher_appreciation_reference_is_national_and_linked(self):
        ps=source_packets(mark_excerpt(Path(FAQ).read_text(),path=FAQ,url='https://www.education.gouv.fr/bo/2026/Hebdo9/MENE2531948N'))
        span=next(p for p in ps[0]['passages'] if p['text'].startswith('La valeur de la note'))
        self.assertEqual(span['scope']['nature'],['texte_national'])
        claim={'section':'decision','text':"L'enseignant apprécie si les éléments d'évaluation sont suffisants.",
               'evidence':[{'document_id':'D1','passage_ids':[span['id']]}]}
        accepted,rejected=validate_claims({'claims':[claim]},ps)
        self.assertFalse(rejected)
        answer=render_claims(accepted,ps)
        self.assertIn('Résumé d’un texte officiel',answer)
        self.assertIn('MENE2531948N du 20 février 2026, 2.e',answer)
        self.assertIn('https://www.education.gouv.fr/bo/2026/Hebdo9/MENE2531948N',answer)

    def test_santorin_entry_stays_software(self):
        ps=source_packets(mark_excerpt(Path(FAQ).read_text(),path=FAQ))
        span=next(p for p in ps[0]['passages'] if p['text'].startswith('Saisie dans Santorin'))
        self.assertEqual(span['scope']['nature'],['logiciel'])
        self.assertIn('Guide de saisie Santorin',span['scope']['reference'])

    def test_teacher_validation_of_note_is_an_explicit_decision(self):
        proof=Path(RULE).read_text()
        def errors(text):
            return conditional_extraction_errors([{'section':'etape','text':text,'evidence':[{'quote':proof}]}], 'Une seule épreuve évaluée : quelle saisie ?')
        self.assertFalse(errors("La note obtenue est conservée à condition que l'enseignant du groupe classe valide cette note unique."))
        self.assertTrue(errors('La note obtenue est conservée automatiquement.'))
        self.assertTrue(errors('La note obtenue est conservée à condition que le certificat médical soit déposé.'))
        self.assertTrue(errors("La note obtenue est conservée à condition que l'enseignant valide le certificat médical."))

    def test_valid_teacher_condition_passes_without_repair(self):
        # Les deux branches restent présentes ; seul le faux rejet est visé.
        source="La note est conservée à condition que l'enseignant valide cette note unique ; sinon il ne propose aucune note si les éléments d'appréciation sont trop réduits."
        claim={'section':'etape','text':source,'evidence':[{'document_id':'D1','quote':source}]}
        llm=FakeLLM([{'claims':[claim]}]);a={}
        review_exam_answer(llm,question='Une seule épreuve évaluée : quelle saisie ?',public='Lycée Général & Techno',documents=mark_excerpt(source),audit=a)
        self.assertEqual(len(llm.prompts),1)
        self.assertFalse(a['initial_rejections'])
