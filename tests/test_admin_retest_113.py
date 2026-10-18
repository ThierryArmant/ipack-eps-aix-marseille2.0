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
    def test_valid_file(self):
        self.assertEqual(len(parse_csv(sample())), 113)

    def test_wrong_count(self):
        with self.assertRaisesRegex(ValueError, "113 questions"):
            parse_csv(sample(112))

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
