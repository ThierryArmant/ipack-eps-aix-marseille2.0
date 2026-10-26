import json
import re
import unittest

import tutorial_links as tl

FICHES = ['data/ipack/transcriptions_videos_tutoriels.txt', 'data/examens/videos_tutoriels_cyclades_santorin.txt']


class VideosParSectionTest(unittest.TestCase):
    """Chaque passage d'une section de transcription propose la vidéo de SA section."""

    def test_chaque_section_donne_sa_video(self):
        catalogue = json.load(open('config/catalogue_documents.json', encoding='utf-8'))
        checked = 0
        for path in FICHES:
            text = open(path, encoding='utf-8').read()
            for block in re.split(r'(?m)^(?=###\s)', text):
                urls = re.findall(r'Vid[ée]os?\s*:\s*(https://\S+)', block, re.I)
                if not urls:
                    continue
                head = block.split('\n', 1)[0].lstrip('#').strip()
                lines = [l for l in block.splitlines()[1:]
                         if len(l) > 40 and not re.search(r'Vid[ée]os?\s*:', l)
                         and not l.startswith(('- Mots-cl', '- Formulations'))]
                for line in lines[:2]:
                    audit = {'documents': [{'id': 'D1', 'path': path}],
                             'exact_extracts': {'selected_sources': [{'passages': [{'id': 'D1P1', 'text': line, 'section': head}]}],
                                                'focused_passage_ids': ['D1P1']}}
                    self.assertEqual(tl.supporting_tutorials(audit, catalogue), [urls[0].rstrip('.,;)')], (path, head))
                    checked += 1
        self.assertGreater(checked, 100)

    def test_passage_inconnu_pas_de_video_de_section(self):
        self.assertIsNone(tl._section_video(FICHES[0], 'Phrase qui ne figure dans aucune section de la fiche.'))


if __name__ == '__main__':
    unittest.main()
