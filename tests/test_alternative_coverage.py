import unittest
from documentary_review import conditional_extraction_errors

PROOF="Sur la seule épreuve évaluée, l'enseignant peut conserver la certification, ou ne pas proposer de note si les éléments d'appréciation sont trop réduits et mentionner dispensé de l'épreuve d'EPS, avec neutralisation du coefficient."
def claims(text):
    return [{'section':'decision','text':text,'evidence':[{'quote':PROOF}]}]
class AlternativeCoverageTests(unittest.TestCase):
    def test_dispensing_two_activities_is_not_dispensing_the_whole_exam(self):
        answer="L'enseignant peut retenir la note. Les deux APSA non évaluées sont dispensées."
        self.assertTrue(conditional_extraction_errors(claims(answer),'Deux inaptitudes et une note : que décider ?'))
    def test_complete_alternative_is_accepted(self):
        answer="L'enseignant peut conserver la note ou ne pas proposer de note si les éléments sont trop réduits ; dans ce cas le coefficient est neutralisé."
        self.assertFalse(conditional_extraction_errors(claims(answer),'Deux inaptitudes et une note : que décider ?'))
    def test_explicit_choice_does_not_force_irrelevant_branch(self):
        self.assertFalse(conditional_extraction_errors(claims('Conserver la note et dispenser les deux APSA.'),'Je conserve la note, que saisir avec deux inaptitudes ?'))
