import unittest
from pathlib import Path
from documentary_review import mark_excerpt, source_packets, handicap_overview_packets, review_exam_answer
from test_documentary_review import FakeLLM

ADAPTE='data/examens/mesure3_corrections/gt_controle_adapte_inaptitude_permanente.txt'
TEMP='data/ipack/fiches/ipack_212_situation_interdiction_d_improviser_un_controle_adapte_fca_a_la_volee.txt'

class HandicapOverviewTests(unittest.TestCase):
    def setUp(self):
        self.docs='\n\n'.join(mark_excerpt(Path(p).read_text(),path=p,priority=320 if p==ADAPTE else 300,selection='catalogue') for p in (ADAPTE,TEMP))
        self.packets=source_packets(self.docs)

    def test_overview_prompt_keeps_entire_national_fiche_only(self):
        llm=FakeLLM([{'claims':[]}]);audit={}
        review_exam_answer(llm,question='Quelles modalités d’évaluation adaptées pour un lycéen en situation de handicap ?',public='Lycée Général & Techno',documents=self.docs,academy='Nantes',audit=audit)
        self.assertEqual(audit['model_document_ids'],['D1'])
        self.assertIn('D2',audit['excluded_handicap_overview_documents'])
        self.assertEqual(len(llm.prompts),1)
        for text in ['Trois épreuves de trois champs', 'Deux épreuves adaptées', 'autant que possible', 'Pour des cas très particuliers']:
            self.assertIn(text,llm.prompts[0])
        self.assertNotIn('Pas de nouvelle validation',llm.prompts[0])

    def test_specific_requests_keep_complementary_procedures(self):
        for q in ['Handicap : comment saisir les épreuves dans Cyclades ?', 'Handicap découvert en cours d’année : adapter l’évaluation ?', 'Inaptitude temporaire : organiser une épreuve adaptée ?', 'Handicap : quel certificat pour l’évaluation ?', 'Handicap : quel recours sur les épreuves ?']:
            with self.subTest(q=q):
                self.assertEqual(handicap_overview_packets(q,self.packets),self.packets)
        self.assertEqual(handicap_overview_packets('Handicap : quelles épreuves ?',self.packets[1:]),self.packets[1:])

    def test_temporary_rule_is_national_but_software_is_not(self):
        p=next(p for p in self.packets if p['path']==TEMP)
        reg=next(s for s in p['passages'] if s['text'].startswith("Pour une inaptitude temporaire en cours d'année"))
        self.assertEqual(reg['scope']['nature'],['texte_national'])
        self.assertNotIn('Cyclades',reg['text'])
        soft=next(s for s in p['passages'] if s['text'].strip().startswith('Pas de nouvelle validation'))
        self.assertNotEqual(soft['scope']['nature'],['texte_national'])

    def test_realistic_omission_and_absolute_preference_restore_source_without_retry(self):
        p=self.packets[0]
        general=next(s for s in p['passages'] if s['text'].startswith('Réponse directe'))
        lists=next(s for s in p['passages'] if s['text'].startswith('Les épreuves adaptées sont de préférence'))
        llm=FakeLLM([{'claims':[
            {'section':'decision','text':"Le contrôle adapté est construit par l'équipe EPS et les services de santé scolaire et soumis à la commission académique.", 'evidence':[{'document_id':p['id'],'passage_ids':[general['id']]}]},
            {'section':'etape','text':"Les épreuves adaptées doivent être choisies dans les listes nationale, académique ou d'établissement.",'evidence':[{'document_id':p['id'],'passage_ids':[lists['id']]}]}
        ]}]);audit={}
        answer=review_exam_answer(llm,question='Quelles possibilités pour évaluer au bac un lycéen en situation de handicap ?',public='Lycée Général & Techno',documents=self.docs,academy='Nantes',audit=audit)
        for expected in ['autant que possible','de préférence','Trois épreuves','Deux épreuves','cas très particuliers']:
            self.assertIn(expected,answer)
        self.assertNotIn('doivent être choisies',answer)
        self.assertEqual(len(llm.prompts),1)
        self.assertFalse(audit['repair_performed'])
        self.assertEqual(len(audit['verbatim_handicap_passages']),2)

    def test_verbatim_does_not_invent_when_source_or_answer_missing(self):
        from documentary_review import preserve_handicap_overview_excerpts
        self.assertEqual(preserve_handicap_overview_excerpts({'claims':[]},'Handicap : quelles épreuves ?',self.packets),({'claims':[]},[]))
        proposal={'claims':[{'section':'decision','text':'Exemple','evidence':[]}]}
        for q,packets in [('Handicap : créer un protocole dans Cyclades ?',self.packets),('Handicap : quelles épreuves ?',self.packets[1:])]:
            self.assertEqual(preserve_handicap_overview_excerpts(proposal,q,packets),(proposal,[]))
