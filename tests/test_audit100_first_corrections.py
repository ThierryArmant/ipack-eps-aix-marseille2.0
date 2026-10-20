import unittest
from pathlib import Path
import knowledge_catalog as kc
import test_documentation as routing
from documentary_review import mark_excerpt,source_packets

BASE='data/examens/audit100_2026_10_20/'
class Audit100FirstCorrections(unittest.TestCase):
    def test_business_update_does_not_trigger_software_shortcut(self):
        for q in ['Valider le projet EPS actualisé dans iPackEPS ?', 'Comment mettre à jour la fiche professeur dans iPackEPS ?', 'Mise à jour des protocoles dans iPackEPS : comment valider ?']:
            with self.subTest(q=q):
                result=kc.documented_response(q,'Collège (DNB)','ipack')
                self.assertFalse(result[0])
        result=kc.documented_response('Comment mettre à jour iPackEPS vers la nouvelle version sans perdre mes données ?', 'Lycée Général & Techno','ipack')
        self.assertTrue(result[0])

    def test_sums_and_averages_are_not_same_selected_fiche(self):
        h=routing.DocumentationTests();h.setUp()
        docs,_,_,_=h.route('Dans Santorin, comment calculer le total APSA avec les AFL1 et AFL2 ?', 'Lycée Général & Techno','examens')
        self.assertIn(BASE+'calcul_points_afl_gt.txt',docs)
        self.assertIn('somme des points',docs)
        self.assertIn('AFL3',docs)
        self.assertIn('après harmonisation',docs)
        self.assertNotIn(BASE+'calcul_points_afl_gt.txt',kc.priority_context('Calcul AFLP au CAP ?', 'Lycée Pro / CAP','examens'))

    def test_signatures_have_specific_document_without_invented_obligation(self):
        h=routing.DocumentationTests();h.setUp()
        for q in ['Faut-il signer les bordereaux Santorin ?', 'La fiche individuelle doit-elle porter la signature des deux évaluateurs ?']:
            docs,_,_,_=h.route(q,'Lycée Général & Techno','examens')
            self.assertIn(BASE+'formalites_signatures_ccf.txt',docs)
            self.assertIn('ne suffit pas',docs)
            self.assertIn('consigne locale',docs)

    def test_paper_retention_is_not_ipack_database_retention(self):
        h=routing.DocumentationTests();h.setUp()
        docs,_,_,_=h.route('Quelle durée de conservation pour les grilles papier de CCF ?', 'Lycée Général & Techno','textes')
        self.assertIn('ipack_207',docs)
        self.assertNotIn('ipack_archivage_prudence.txt',docs)
        self.assertIn('ne fixe pas de durée',docs)

    def test_reassignment_is_not_appn(self):
        h=routing.DocumentationTests();h.setUp()
        docs,_,_,_=h.route('Comment faire réaffecter les protocoles par le chef dans Cyclades ?', 'Lycée Général & Techno','examens')
        self.assertIn(BASE+'reaffecter_evaluateur_cyclades.txt',docs)
        self.assertNotIn('dossier_appn_demande_validation.txt',docs)
        self.assertIn('Contrôler / Réaffecter',docs)
        appn=kc.priority_context('Dans iPackEPS comment déposer mon dossier APPN en kayak ?', 'Lycée Général & Techno','ipack')
        self.assertIn('Dossier APPN',appn)

    def test_no_medical_certificate_does_not_imply_dispense(self):
        h=routing.DocumentationTests();h.setUp()
        docs,_,_,_=h.route('Rattrapage CCF sans certificat médical valide : que faire ?', 'Lycée Général & Techno','textes')
        self.assertIn('absence_injustifiee_gt.txt',docs)
        self.assertIn('force majeure',docs)
        self.assertIn('ni zéro ni dispense',docs)

    def test_appeal_deadline_has_institutional_source(self):
        text=Path('data/commun/audit60/contestation_note.txt').read_text()
        self.assertIn('deux mois suivant la notification',text)
        self.assertIn('service-public.gouv.fr',text)
        for path in (BASE+'calcul_points_afl_gt.txt',BASE+'formalites_signatures_ccf.txt',BASE+'reaffecter_evaluateur_cyclades.txt'):
            packets=source_packets(mark_excerpt(Path(path).read_text(),path=path))
            self.assertTrue(packets)
            self.assertNotIn('a_verifier',packets[0]['passages'][0]['scope']['nature'])
