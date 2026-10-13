import unittest
from pathlib import Path
from documentary_review import course_duration_mismatch, source_packets, mark_excerpt

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
