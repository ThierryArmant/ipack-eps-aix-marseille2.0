import unittest
from pathlib import Path
from documentary_review import source_packets, mark_excerpt, bind_sections

LOT = 'data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt'


class SectionUnitsTests(unittest.TestCase):
    def passages(self, path):
        return source_packets(mark_excerpt(Path(path).read_text(encoding='utf-8'), path=path))[0]['passages']

    def test_lines_of_a_titled_situation_carry_its_title(self):
        ps = self.passages(LOT)
        lot = [p for p in ps if 'TOUT UN LOT EST ATTRIBUÉ AU MAUVAIS ENSEIGNANT' in p.get('section', '')]
        self.assertTrue(any('réaffecter un lot à un autre examinateur' in p['text'] for p in lot))
        self.assertTrue(any('Ne pas confondre' in p['text'] for p in lot))
        move = [p for p in ps if 'UN ÉLÈVE EST DANS LE MAUVAIS LOT' in p.get('section', '')]
        self.assertTrue(any('déplacer un candidat' in p['text'] for p in move))
        self.assertFalse(any('déplacer un candidat d\'un lot à un autre' in p['text'] and 'Action' in p['text'] for p in lot))

    def test_exact_text_and_proof_units_are_unchanged(self):
        body = '### A\n- ligne un\n- ligne deux\n### B\n- ligne trois'
        spans = []
        pos = 0
        for line in body.split('\n'):
            spans.append({'text': line, 'start': pos, 'end': pos + len(line)})
            pos += len(line) + 1
        content = [s for s in spans if not s['text'].startswith('###')]
        out = bind_sections(content, body)
        self.assertEqual([s['text'] for s in out], ['- ligne un', '- ligne deux', '- ligne trois'])
        self.assertEqual([s['section'] for s in out], ['A', 'A', 'B'])

    def test_file_without_titles_is_unchanged(self):
        spans = [{'text': 'x', 'start': 0, 'end': 1}]
        self.assertEqual(bind_sections(spans, 'x'), spans)


if __name__ == '__main__':
    unittest.main()
