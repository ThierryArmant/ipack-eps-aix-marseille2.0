import unittest
from admin_retest_113 import parse_csv


class CsvModeAliasesTests(unittest.TestCase):
    def test_singular_plural_and_case_keep_question_and_level(self):
        for value, expected in [('texte','textes'),(' Textes ','textes'),('TEXTE','textes'),
                                ('texte officiel','textes'),('examen','examens'),('examens','examens'),('ipack','ipack')]:
            with self.subTest(value=value):
                rows=parse_csv(('mode;public;question\n'+value+';Collège;Question exemple\n').encode())
                self.assertEqual(rows[0]['mode'],expected)
                self.assertEqual(rows[0]['question'],'Question exemple')
                self.assertEqual(rows[0]['public'],'Collège (DNB)')

    def test_unknown_mode_and_unspecified_level_are_not_inferred(self):
        with self.assertRaisesRegex(ValueError,'inconnu'):
            parse_csv(b'mode;public;question\ninconnu;College;Question\n')
        for level in ['', 'Candidats libres']:
            with self.assertRaisesRegex(ValueError,'public absent ou non reconnu'):
                parse_csv(('mode;public;question\ntexte;'+level+';Question\n').encode())


if __name__=='__main__':unittest.main()
