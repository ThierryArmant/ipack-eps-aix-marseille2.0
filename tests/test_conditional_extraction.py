import unittest
from documentary_review import conditional_extraction_errors, mark_excerpt, review_exam_answer
from test_documentary_review import FakeLLM

SOURCE=("Si l'inaptitude empêche deux autres épreuves, une certification sur une seule note peut être retenue. "
        "Si les éléments d'appréciation sont trop réduits, la dispense neutralise le coefficient EPS. "
        "Ne pas transformer ces possibilités en décision automatique.")
QUESTION='Deux inaptitudes totales et une note : doit-il être noté ?'

def claim(text,section='decision'):
    return {'section':section,'text':text,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}

class ConditionalExtractionTests(unittest.TestCase):
    def test_late_condition_does_not_hide_categorical_head(self):
        c=claim("Il ne doit pas être noté car une certification sur une seule note peut être retenue et la dispense s'applique si les éléments sont trop réduits.")
        c['evidence'][0]['quote']=SOURCE
        self.assertTrue(conditional_extraction_errors([c],QUESTION))

    def test_branch_conditions_and_actor_are_preserved_after_repair(self):
        bad=claim("Il ne doit pas être noté car une certification sur une seule note peut être retenue et la dispense s'applique si les éléments sont trop réduits.")
        good=claim("Une certification sur une seule note peut être retenue si l'inaptitude empêche deux autres épreuves ; si les éléments d'appréciation sont trop réduits, la dispense neutralise le coefficient EPS.")
        llm=FakeLLM([{'claims':[bad]},{'claims':[good]}]);audit={}
        result=review_exam_answer(llm,question=QUESTION,public='Lycée Général & Techno',documents=mark_excerpt(SOURCE),audit=audit)
        self.assertNotIn('ne doit pas',result)
        self.assertIn('une seule note',result)
        self.assertIn('dispense',result)
        self.assertTrue(audit['initial_rejections'])
        self.assertEqual(len(llm.prompts),2)

    def test_known_type_is_not_requested_but_period_can_be(self):
        c=claim("Demandez le caractère total ou partiel des inaptitudes et leur durée.",'etape')
        self.assertTrue(conditional_extraction_errors([c],QUESTION))
        self.assertFalse(conditional_extraction_errors([claim('Précisez la durée des inaptitudes.','limite')],QUESTION))

    def test_valid_conditional_answer_does_not_add_model_call(self):
        good=claim("Une certification sur une seule note peut être retenue si l'inaptitude empêche deux autres épreuves ; si les éléments d'appréciation sont trop réduits, la dispense neutralise le coefficient EPS.")
        llm=FakeLLM([{'claims':[good]}])
        review_exam_answer(llm,question=QUESTION,public='Lycée Général & Techno',documents=mark_excerpt(SOURCE))
        self.assertEqual(len(llm.prompts),1)

    def test_repeated_categorical_failure_is_never_rendered(self):
        bad=claim("Il ne doit pas être noté car une certification sur une seule note peut être retenue et la dispense s'applique si les éléments sont trop réduits.")
        llm=FakeLLM([{'claims':[bad]},{'claims':[bad]}]);audit={}
        with self.assertRaises(ValueError):
            review_exam_answer(llm,question=QUESTION,public='Lycée Général & Techno',documents=mark_excerpt(SOURCE),audit=audit)
        self.assertTrue(audit['final_rejections'])
        self.assertNotIn('rendered_answer',audit)

    def test_unconditional_obligation_supported_by_source_is_kept(self):
        c=claim('Le candidat doit être noté sur trois épreuves.')
        c['evidence'][0]['quote']='Le candidat est évalué sur trois épreuves.'
        self.assertFalse(conditional_extraction_errors([c], 'Comment noter ?'))

if __name__=='__main__': unittest.main()
