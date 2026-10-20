"""Le mot recours ne suffit pas à faire d'une demande une contestation de note."""
import unittest
import knowledge_catalog as kc

PATH='data/commun/audit60/contestation_note.txt'
class AppealSubjectSelection(unittest.TestCase):
    def chosen(self,q):
        return [p for p,_ in kc.reference_notice({'gt'},q,'Lycée Général & Techno')]
    def test_other_decisions_do_not_select_grade_appeal(self):
        for q in ['Recours après refus de sortie scolaire : quelles démarches ?', 'Un parent conteste le voyage de classe.', 'Erreur de report de date de sortie : comment corriger ?', 'Contester une note de service sur les sorties ?']:
            self.assertNotIn(PATH,self.chosen(q))
    def test_grades_and_results_keep_their_source(self):
        for q in ['Une famille conteste ma notation EPS.', 'Erreur de note après le jury : qui prévenir ?', 'Quel recours pour le résultat au baccalauréat ?', 'Contester le relevé de notes : quel délai ?']:
            self.assertIn(PATH,self.chosen(q))
    def test_entry_error_is_not_an_appeal(self):
        for q in ['Santorin refuse la note saisie avec une erreur de décimale.', 'Erreur dans mon lot : comment corriger la note ?', 'J’ai saisi toutes les notes mais tout est vide, erreur de manipulation ?', 'Erreur dans mon lot : corriger ma note. Préciser ce qui relève du logiciel.']:
            self.assertNotIn(PATH,self.chosen(q))
    def test_preparing_commission_is_not_after_it(self):
        import test_documentation as routing
        h=routing.DocumentationTests();h.setUp()
        text=h.route('Une fois mes notes saisies, récupérer un tableau pour préparer la commission ?', 'Lycée Général & Techno','examens')[0]
        self.assertNotIn('harmonisation_cloture_remontee.txt',text)
        text=h.route('Après la commission d’harmonisation, qui peut modifier la note ?', 'Lycée Général & Techno','examens')[0]
        self.assertIn('harmonisation_cloture_remontee.txt',text)
    def test_releve_verb_is_not_a_grade_report(self):
        import test_documentation as routing
        from documentary_review import context_document_mismatch
        h=routing.DocumentationTests();h.setUp()
        q='Quand exporter les protocoles vers Cyclades ? Préciser ce qui relève du logiciel.'
        text=h.route(q,'Lycée Général & Techno','examens')[0]
        self.assertIn('calendrier_certificatif_aix_marseille.txt',text)
        self.assertFalse(context_document_mismatch(q,'Lycée Général & Techno','examens',{'path':'data/ipack/visite_lycee_2026_10_18/calendrier_certificatif_aix_marseille.txt'}))
    def test_minimum_in_textes_keeps_exceptions_and_commission_keeps_jury(self):
        import test_documentation as routing
        h=routing.DocumentationTests();h.setUp()
        text=h.route('Quel nombre minimal d’épreuves pour le baccalauréat EPS ?', 'Lycée Général & Techno','textes')[0]
        self.assertIn('gt_regles_decisives.txt',text)
        self.assertIn('gt_inaptitude_possibilites_ccf.txt',text)
        text=h.route('Désaccord lors de la commission d’harmonisation : qui arrête la note finale ?', 'Lycée Général & Techno','examens')[0]
        self.assertIn('harmonisation_cloture_remontee.txt',text)
        self.assertIn('jury',text)
