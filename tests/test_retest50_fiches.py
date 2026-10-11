"""Régressions des six questions signalées dans les passes comparées."""
import unittest
import knowledge_catalog as kc

class Retest50FichesTests(unittest.TestCase):
    def answer(self,q,mode='examens',level='Lycée Général & Techno'):
        level,mode=kc.effective_context(q,level,mode)
        return kc.documented_response(q,level,mode)[0]

    def test_individual_option_has_practice_and_oral(self):
        a=self.answer("Quelles sont les épreuves de l'option EPS pour un candidat individuel au bac GT ?")
        for part in ['sauvetage aquatique','badminton','20 minutes','12 points','8']:
            self.assertIn(part,a)
        self.assertIn('distincte',a)

    def test_shn_date_is_not_an_unconditional_twenty(self):
        a=self.answer('À quelle date un élève doit-il avoir le statut de sportif de haut niveau pour bénéficier du régime SHN à Aix-Marseille ?')
        self.assertIn('janvier ou juillet',a)
        self.assertIn('validé par le recteur',a)
        self.assertIn("unique note",a)

    def test_absent_candidate_is_not_fixed_by_export(self):
        a=self.answer("Il manque trois élèves dans la liste des candidats du bac sur Cyclades, est-ce que je dois refaire l'export depuis iPackEPS ?")
        self.assertIn('ne crée pas',a)
        self.assertIn('chef',a)
        self.assertIn('DIEC',a)

    def test_activity_deadline_is_explicitly_historical(self):
        a=self.answer("Nous voulons proposer une activité qui n'est pas sur la liste nationale au bac GT. Avant quand faut-il la demander ?")
        self.assertIn('30 mai 2026',a)
        self.assertIn('passée',a)
        self.assertIn('liste académique',a)

    def test_fraud_commission_is_not_cahpn(self):
        a=self.answer("Un élève a triché en course d'orientation. que faire")
        self.assertIn('commission de discipline',a)
        self.assertIn('pas la CAHPN',a)
        self.assertIn('évaluation ordinaire',a)

    def test_video_cannot_make_ipack_a_gradebook(self):
        a=self.answer("Comment filmer ou photographier un élève et associer la vidéo à son évaluation ?",'ipack','Collège (DNB)')
        self.assertIn('Pronote',a)
        self.assertIn("n'est pas",a)
        self.assertIn('Santorin',a)
