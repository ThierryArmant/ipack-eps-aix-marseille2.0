import unittest
from pathlib import Path
from documentary_review import course_duration_mismatch, dnb_document_mismatch, source_packets, mark_excerpt

class CourseDureeTests(unittest.TestCase):
    def test_reported_question_excludes_wrong_course_deposit_document(self):
        path='data/ipack/complement_reponses_validees.txt'
        packets=source_packets(mark_excerpt(Path(path).read_text(),path=path))
        for q in ('peut on deposer une activite course de durée et demi fond', 'Déposer une FCA de course en durée CA5'):
            self.assertTrue(course_duration_mismatch(q,packets[0]))
        self.assertFalse(course_duration_mismatch('Ma fiche de demi-fond est non certificative',packets[0]))
        self.assertFalse(course_duration_mismatch('course en durée',{'path':'data/commun/texte_officiel_bac_gt_note_de_service_2026.txt'}))

    def test_structural_fields_do_not_prove_deposit_procedure(self):
        code=Path('app.py').read_text()
        self.assertIn('il ne prouve ni la validité du protocole complet ni une procédure de dépôt',code)
        self.assertNotIn("Ces activités sont toutes dans des champs DIFFÉRENTS : elles peuvent figurer ensemble",code)


class DnbCrossContextTests(unittest.TestCase):
    def test_dnb_one_mark_excludes_santorin_lycee(self):
        path='data/examens/tutoriels_creteil_cyclades_santorin.txt'
        packet=source_packets(mark_excerpt(Path(path).read_text(),path=path))[0]
        self.assertTrue(dnb_document_mismatch("je n'ai qu'une note et de nombreuses dispenses pour le dnb que dois je faire",'Collège (DNB)',packet))
        self.assertFalse(dnb_document_mismatch('DI + DI + une note au bac GT', 'Lycée Général & Techno',packet))
        path='data/commun/dnb/03_absences_representativite.txt'
        packet=source_packets(mark_excerpt(Path(path).read_text(),path=path))[0]
        self.assertFalse(dnb_document_mismatch('Une seule note au DNB', 'Collège (DNB)',packet))


class PrimarySecondaryRoutingTests(unittest.TestCase):
    def test_primary_source_not_given_to_college_trip(self):
        import knowledge_catalog as kc
        self.assertTrue(kc.incompatible(Path('data/textes/premier_degré.txt').read_text(), {'dnb'}))
        self.assertFalse(kc.incompatible(Path('data/commun/sorties_premier_degre.txt').read_text(), {'primaire'}))

    def test_bike_trip_gets_precise_source(self):
        import knowledge_catalog as kc
        text=kc.delivered_text('Je fais une sortie VTT avec mes élèves pour me rendre au musée : quelles obligations ?', 'Collège (DNB)','textes')
        self.assertIn('Au moins un enseignant accompagne',text)
        self.assertIn('hors agglomération',text)
        self.assertIn('avant 12 ans',text)
        self.assertIn('mode de déplacement',text)
