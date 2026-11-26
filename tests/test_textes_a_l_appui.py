"""Règle du 26/11/2026 : une réponse douteuse est accompagnée des textes.
Toute citation « … » d'une ligne « Réponse directe — textes à l'appui » doit figurer mot pour mot
dans une copie de texte officiel conservée dans le dépôt."""
import re
import unittest
from pathlib import Path

SOURCES = list(Path('data/commun/textes_sources').glob('*.txt')) + list(Path('sources/officiels').glob('*/*.md'))


def _norm(s):
    s = s.replace('’', "'").replace(' ', ' ').replace(' ', ' ')
    return re.sub(r'\s+', ' ', s).strip()


CORPUS = _norm('\n'.join(p.read_text(encoding='utf-8') for p in SOURCES))


def lignes_appui():
    for p in Path('data').rglob('*.txt'):
        if 'archives' in p.parts:
            continue
        for ligne in p.read_text(encoding='utf-8').splitlines():
            if ligne.startswith("Réponse directe — textes à l'appui"):
                yield p, ligne


class TextesALAppui(unittest.TestCase):
    def test_citations_exactes(self):
        lignes = list(lignes_appui())
        self.assertTrue(lignes)
        for p, ligne in lignes:
            for citation in re.findall(r'«\s*(.+?)\s*»', ligne):
                for morceau in re.split(r'\s*\[…\]\s*', citation):
                    morceau = _norm(morceau).rstrip('.').strip()
                    if len(morceau) < 12:
                        continue
                    with self.subTest(fiche=str(p), citation=morceau[:60]):
                        self.assertIn(morceau, CORPUS)


if __name__ == '__main__':
    unittest.main()
