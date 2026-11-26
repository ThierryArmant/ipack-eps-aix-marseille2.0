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


class AffichageSousLaReponse(unittest.TestCase):
    def test_bloc_affiche_pour_la_fiche_utilisee(self):
        from exact_source_answer import _textes_appui
        chemin = 'data/examens/textes_2026_11_26/bac_gt_redoublant_conservation_note_eps.txt'
        packet = {'path': chemin, 'title': "Baccalauréat général et technologique : élève qui redouble la terminale",
                  'passages': [{'text': 'Réponse directe — candidat scolaire qui redouble…'}]}
        bloc = _textes_appui([packet])
        self.assertIn("Textes à l'appui", bloc)
        self.assertIn('MENE2523745N', bloc)
        self.assertNotIn("à citer sous la réponse", bloc)

    def test_section_seulement_dans_une_fiche_a_plusieurs_situations(self):
        from exact_source_answer import _textes_appui
        chemin = 'data/examens/complement_note_de_service_bac_gt_2026.txt'
        packet = {'path': chemin, 'title': "[SITUATION: ABSENCE NON JUSTIFIÉE À UNE ÉPREUVE DE CCF AU BAC GT (note de service du 20 février 2026)]",
                  'passages': []}
        bloc = _textes_appui([packet])
        self.assertIn('non éliminatoire', bloc)
        self.assertNotIn('20/20', bloc)

    def test_rien_sans_ligne_d_appui(self):
        from exact_source_answer import _textes_appui
        self.assertEqual(_textes_appui([{'path': '', 'title': 'x', 'passages': [{'text': 'Réponse directe — y'}]}]), '')
