import hashlib
import json
import unittest
from pathlib import Path
import test_documentation as routing
import knowledge_catalog as kc
from documentary_review import mark_excerpt, source_packets, response_focus_notes, review_exam_answer, render_claims
from source_scope import select_academy
from test_documentary_review import FakeLLM

MENU='data/examens/validation_menu_cadre_national_gt.txt'
ADAPTE='data/examens/mesure3_corrections/gt_controle_adapte_inaptitude_permanente.txt'
LOCAL='data/commun/audit60/aix_protocoles_2026.txt'
CONTEST='data/commun/audit60/contestation_note.txt'

class FourPrioritiesTests(unittest.TestCase):
    def test_generic_menu_uses_national_validation_not_aix_software(self):
        h=routing.DocumentationTests();h.setUp()
        docs,_,_,_=h.route('Faire valider le menu APSA de mon établissement : comment procéder ?', 'Lycée Général & Techno','examens')
        ps=source_packets(docs)
        self.assertIn(MENU,[p['path'] for p in ps])
        self.assertNotIn(LOCAL,[p['path'] for p in ps])
        self.assertIn('Le chef d’établissement transmet le protocole',docs)
        self.assertIn('canal de dépôt',docs)

    def test_explicit_aix_keeps_local_reference(self):
        paths=[p for p,_ in kc.reference_notice(['gt'],'À Aix-Marseille, faire valider notre menu d’établissement ?')]
        self.assertIn(LOCAL,paths)
        docs=kc.priority_context('À Aix-Marseille, faire valider notre menu d’établissement ?', 'Lycée Général & Techno','examens')
        self.assertIn('BA spécial 549',docs)

    def test_local_deposit_is_attributed_in_its_own_sentence(self):
        ps=source_packets(mark_excerpt(Path(LOCAL).read_text(),path=LOCAL))
        chosen,_=select_academy(ps,'Lille')
        span=next(s for s in chosen[0]['passages'] if s['text'].startswith('Réponse courte :'))
        self.assertEqual(span['scope']['nature'],['consigne_academique'])
        claim={'section':'etape','text':'La déclaration des protocoles et le dépôt des FCA se font dans iPackEPS.', 'evidence':[{'document_id':'D1','quote':span['text'],'level':span['scope']['level'],'scope':span['scope']}]}
        answer=render_claims([claim],chosen)
        self.assertIn('À Aix-Marseille',answer)
        self.assertIn('Lille',answer)
        national=next(s for s in chosen[0]['passages'] if s['text'].startswith('Bac GT, cadre national'))
        self.assertNotIn('not_confirmed_for',national['scope'])

    def test_pro_cap_keeps_transmission_and_harmonisation_separate(self):
        path='data/commun/audit60/pro_cap_absences.txt'
        ps=source_packets(mark_excerpt(Path(path).read_text(),path=path))
        self.assertIn('point entier supérieur',ps[0]['text'])
        self.assertIn('point entier le plus proche',ps[0]['text'])
        self.assertIn('seule habilitée',ps[0]['text'])
        self.assertIn('harmonisation à la commission',response_focus_notes('Comment fonctionne l’évaluation bac pro et CAP ?',ps)[0])

    def test_handicap_keeps_three_two_one_cases_and_ccf(self):
        ps=source_packets(mark_excerpt(Path(ADAPTE).read_text(),path=ADAPTE))
        text=ps[0]['text']
        for fragment in ['Trois épreuves de trois champs', 'Deux épreuves adaptées', 'autant que possible', 'cas très particuliers', 'une seule épreuve adaptée', 'contrôle en cours de formation']:
            self.assertIn(fragment,text)
        self.assertTrue(response_focus_notes('Comment adapter l’évaluation pour un handicap au bac GT ?',ps))
        focused=' '.join(response_focus_notes('Deux épreuves adaptées : quels champs ?',ps))
        self.assertIn('autant que possible',focused)
        self.assertIn('pas une obligation absolue',focused)
        self.assertIn('handicap découvert en cours d’année',focused)
        self.assertEqual(response_focus_notes('Deux épreuves adaptées : quels champs ?', []), [])

    def test_grade_appeal_no_software_label_and_no_blanket_ban(self):
        path='data/ipack/fiches/ipack_179_situation_menace_de_recours_juridique_d_un_parent_sur_une_note_de_ccf.txt'
        for source in (path,CONTEST):
            text=Path(source).read_text();ps=source_packets(mark_excerpt(text,path=source))
            self.assertNotIn("Avant les résultats, il n'y a pas de procédure de contestation",text)
            self.assertNotIn('L. 911-4',text)
            self.assertTrue(all(s['scope']['nature']==['texte_national'] for s in ps[0]['passages']))
            self.assertIn('service-public.gouv.fr/particuliers/vosdroits/F22331',text)

    def test_new_official_copies_and_consolidated_index_are_traceable(self):
        manifest=json.loads(Path('sources/officiels/2026-10-19/registre.json').read_text())
        self.assertEqual(len(manifest),5)
        for record in manifest:
            for kind in ('copie','lecture'):
                self.assertEqual(hashlib.sha256(Path(record[kind]).read_bytes()).hexdigest(),record['sha256_'+kind])
        indexed={metadata['path'] for _,metadata in kc.document_records('data/examens')}
        # document_records expose des fiches du chargeur avec leur chemin source.
        for record in manifest:
            self.assertEqual(record['lecture'] in indexed,record['indexe'])
        for nor in ('MENE2505383C','MENE2517122C'):
            original=Path('sources/officiels/2026-10-19/'+nor+'.md').read_text()
            consolidated=Path('data/commun/textes_sources/'+nor+'.txt').read_text()
            self.assertIn('Version de lecture consolidée',consolidated)
            self.assertIn('soit adapter l’épreuve si l’inaptitude est partielle',consolidated)
            self.assertNotIn('soit adapter l’épreuve si l’inaptitude est partielle',original)

    def test_national_menu_reply_requires_no_repair(self):
        docs=mark_excerpt(Path(MENU).read_text(),path=MENU,selection='catalogue',priority=60)
        ps=source_packets(docs);span=next(s for s in ps[0]['passages'] if s['text'].startswith('Le chef d’établissement'))
        claim={'section':'etape','text':span['text'],'evidence':[{'document_id':'D1','passage_ids':[span['id']]}]}
        llm=FakeLLM([{'claims':[claim]}]);a={}
        answer=review_exam_answer(llm,question='Faire valider notre menu APSA d’établissement : quelle démarche ?',public='Lycée Général & Techno',academy='Lille',mode='examens',documents=docs,audit=a)
        self.assertEqual(len(llm.prompts),1)
        self.assertFalse(a['final_rejections'])
        self.assertNotIn('non confirmées pour Lille',answer)
