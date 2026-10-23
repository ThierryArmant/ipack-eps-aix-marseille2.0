"""Tests isolés du panneau admin : aucun secret, aucun appel IA."""
import csv
import io
import unittest

from admin_retest_113 import parse_csv

def sample(count=113):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["n", "question", "mode", "public", "verdict"], delimiter=";")
    writer.writeheader()
    for i in range(count):
        writer.writerow({"n": str(i + 1), "question": f"Question {i + 1} ?",
                         "mode": ["ipack", "examens", "textes"][i % 3],
                         "public": "Collège", "verdict": "partiel"})
    return output.getvalue().encode("utf-8-sig")

class AdminRetest113Tests(unittest.TestCase):
    def test_large_trace_columns_are_accepted_and_not_replayed(self):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['question','mode','public','diagnostic_ia'], delimiter=';')
        writer.writeheader()
        for i in range(5):
            writer.writerow({'question':f'Question {i} ?', 'mode':'examens', 'public':'Collège',
                             'diagnostic_ia':'preuve;\n' * 70000})
        data = output.getvalue().encode('utf-8')
        self.assertGreater(len(data), 2_000_000)
        previous = csv.field_size_limit()
        try:
            csv.field_size_limit(131072)
            rows = parse_csv(data)
        finally:
            csv.field_size_limit(previous)
        self.assertEqual(len(rows), 5)
        self.assertNotIn('diagnostic_ia', rows[0])
        self.assertEqual(rows[0]['question'], 'Question 0 ?')

    def test_malformed_quoted_csv_becomes_friendly_value_error(self):
        with self.assertRaisesRegex(ValueError, 'CSV illisible'):
            parse_csv(b'question;mode;public\n"Unclosed;examens;College\n')

    def test_csv_loader_observes_parser_update_without_reload(self):
        import tempfile
        from pathlib import Path
        from admin_csv_loader import load_csv_import
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'admin_retest_113.py'
            path.write_text('parse_csv = "old"')
            old = load_csv_import(directory)
            path.write_text('parse_csv = "new"')
            new = load_csv_import(directory)
            self.assertEqual(old.parse_csv, 'old')
            self.assertEqual(new.parse_csv, 'new')

    def test_valid_file(self):
        self.assertEqual(len(parse_csv(sample())), 113)

    def test_variable_count(self):
        for count in [1, 5, 79, 112, 114]:
            self.assertEqual(len(parse_csv(sample(count))), count)

    def test_friendly_headers_and_comma(self):
        rows = parse_csv('Question,Niveau,Onglet,Academy\nComment faire ?,Lycée voie générale,Examens,Aix-Marseille\n'.encode())
        self.assertEqual(rows[0]['n'], '1')
        self.assertEqual(rows[0]['public'], 'Lycée Général & Techno')
        self.assertEqual(rows[0]['academie'], 'Aix-Marseille')
        self.assertEqual(rows[0]['verdict'], '')

    def test_tabular_export_and_blank_lines(self):
        rows = parse_csv('Questions\tPublic\tContexte\nQuel menu ?\tCollège\tiPackEPS\n\n'.encode())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['mode'], 'ipack')

    def test_explicit_defaults_only_fill_missing(self):
        rows = parse_csv('question;mode;public\nQuestion A ?;;\nQuestion B ?;ipack;Collège\n'.encode(), 'examens', 'Lycée voie générale')
        self.assertEqual([r['mode'] for r in rows], ['examens', 'ipack'])
        self.assertEqual(rows[1]['public'], 'Collège (DNB)')

    def test_unknown_public_not_guessed(self):
        with self.assertRaisesRegex(ValueError, 'public absent ou non reconnu'):
            parse_csv('question;mode;public\nQuestion ?;examens;lycée\n'.encode())

    def test_empty_table(self):
        with self.assertRaisesRegex(ValueError, 'aucune question'):
            parse_csv(sample(0))

    def test_duplicate_aliases_not_silently_overwritten(self):
        with self.assertRaisesRegex(ValueError, 'Deux colonnes'):
            parse_csv('question;mode;contexte;public\nQ;ipack;examens;Collège\n'.encode())

    def test_quoted_multiline_question_kept(self):
        rows = parse_csv('question;mode;public\n"Première ligne; précision\nSuite ?";textes;Collège\n'.encode())
        self.assertEqual(rows[0]['question'], 'Première ligne; précision\nSuite ?')

    def test_duplicate_id(self):
        content = sample().decode("utf-8-sig").replace("2;Question 2 ?", "1;Question 2 ?")
        with self.assertRaisesRegex(ValueError, "doublon"):
            parse_csv(content.encode("utf-8"))

    def test_missing_question(self):
        content = sample().decode("utf-8-sig").replace("1;Question 1 ?", "1;")
        with self.assertRaisesRegex(ValueError, "vide"):
            parse_csv(content.encode("utf-8"))

    def test_invalid_mode(self):
        content = sample().decode("utf-8-sig").replace(";ipack;", ";autre;", 1)
        with self.assertRaisesRegex(ValueError, "Mode inconnu"):
            parse_csv(content.encode("utf-8"))

    def test_invalid_encoding(self):
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            parse_csv(b"\xff\xfe")

if __name__ == "__main__":
    unittest.main()
