import unittest

from short_answer import unsupported

SRC = ("À chaque rentrée, partir du Tableau de bord : fiche Établissement, puis Dossier EPS > Classes. "
       "Dans Santorin, saisie des notes par AFL.")


class MenusLibellesTest(unittest.TestCase):
    def test_libelle_de_la_fiche_mis_entre_crochets_accepte(self):
        self.assertEqual(unsupported('[Tableau de bord] > [Établissement] : vérifier la fiche.', SRC, 'q'), [])
        self.assertEqual(unsupported('[Dossier EPS] > [Classes] : actualiser.', SRC, 'q'), [])

    def test_menu_invente_refuse(self):
        self.assertIn('menu:[saisie]', unsupported('[Santorin] > [Saisie] : saisir les notes.', SRC, 'q'))
        self.assertTrue(any(r.startswith('menu:') for r in unsupported('[Menu inventé] : faire.', SRC, 'q')))

    def test_ne_pas_attribuer_zero_n_est_pas_une_consigne_interne(self):
        t = 'Ne pas attribuer zéro ni calculer de moyenne fictive.'
        self.assertEqual(unsupported(t, t, 'q'), [])
        t2 = 'Ne pas attribuer à iPackEPS cette procédure.'
        self.assertIn('forme:consigne_interne', unsupported(t2, t2, 'q'))


if __name__ == '__main__':
    unittest.main()
