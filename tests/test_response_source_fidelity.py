import unittest
from pathlib import Path
from documentary_review import conditional_extraction_errors, render_claims, source_packets, mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

class SourceFidelityTests(unittest.TestCase):
    def proof(self,text,source,section='decision'):
        return {'text':text,'section':section,'evidence':[{'document_id':'D1','quote':source}]}
    def test_symptom_condition_is_not_teacher_decision(self):
        source=Path('data/examens/situations_2026_10_13/gt_une_seule_note_sur_trois.txt').read_text()
        bad=self.proof('Si le candidat a une note de 14 et deux dispenses, sa note pour le baccalauréat sera uniquement celle de 14.',source)
        self.assertTrue(conditional_extraction_errors([bad],'DI + DI + 14 : quel résultat ?'))
        good=self.proof('Si l’enseignant apprécie les éléments suffisants pour une certification, la note peut être retenue ; sinon il peut ne pas formuler de proposition de note.',source)
        self.assertFalse(conditional_extraction_errors([good],'DI + DI + 14 : quel résultat ?'))
    def test_approximation_does_not_replace_non_guaranteed_delay(self):
        source='Les comptes remontent en 72 h environ : délai indicatif cité par l’assistance, sans garantie.'
        for text in ['Les comptes remontent en 72 h.','Cela peut prendre environ 72 heures.']:
            self.assertTrue(conditional_extraction_errors([self.proof(text,source)],'Mon établissement manque'))
        self.assertFalse(conditional_extraction_errors([self.proof('Les 72 h sont un délai indicatif sans garantie.',source)],'Mon établissement manque'))
    def test_fixed_documented_delay_stays_valid(self):
        self.assertFalse(conditional_extraction_errors([self.proof('Le délai est de 3 jours.','Le délai est de 3 jours.')],'Quel délai ?'))
    def test_requested_distinction_uses_registry_and_marks_missing_national(self):
        docs=mark_excerpt('### Essai\nDans Santorin, ouvrir le menu Distribution.',path='data/examens/santorin_cas_pratiques/17_santorin_dans_quel_menu_se_fait_chaque_operation.txt')
        packets=source_packets(docs)
        span=packets[0]['passages'][0]
        c={'section':'etape','text':'Ouvrir le menu Distribution.','evidence':[{'document_id':'D1','quote':span['text'],'scope':span.get('scope',{})}]}
        result=render_claims([c],packets,question='Distingue texte national, consigne académique et logiciel.')
        self.assertIn('Cadre national',result)
        self.assertIn('aucun passage de portée nationale',result)
        self.assertIn('Documentation du logiciel :</strong>',result)
        self.assertNotIn('Cadre national',render_claims([c],packets,question='Où cliquer ?'))
    def test_national_source_is_not_announced_missing(self):
        docs=mark_excerpt('### Essai\n=== TEXTE OFFICIEL : règle\nUne règle nationale.')
        result=render_claims([],source_packets(docs),question='Distingue national et logiciel.')
        self.assertNotIn('aucun passage',result)
    def test_first_prompt_preserves_return_path_and_delay(self):
        llm=FakeLLM([{'claims':[]}])
        review_exam_answer(llm,question='Comment changer de contexte ?',public='Lycée Général & Techno',documents=mark_excerpt('### Navigation\nRemonter par le fil d’Ariane au tableau de bord.'),mode='ipack')
        self.assertEqual(1,len(llm.prompts))
        self.assertIn('chemin de retour documenté',llm.prompts[0])
        self.assertIn('même si tu écris « environ »',llm.prompts[0])
