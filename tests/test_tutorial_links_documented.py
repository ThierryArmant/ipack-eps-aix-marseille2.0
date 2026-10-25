import unittest
from tutorial_links import supporting_tutorials


def audit(text, path='data/ipack/fiches/x.txt'):
    return {'documents': [{'id': 'D1', 'path': path, 'text': text}],
            'exact_extracts': {'focused_passage_ids': ['D1P1'],
                               'selected_sources': [{'passages': [{'id': 'D1P1', 'text': text}]}]}}


class DocumentedModeVideos(unittest.TestCase):
    def test_passage_affiche_declenche_la_video_du_parcours(self):
        self.assertEqual(supporting_tutorials(audit('Ouvrir [Dossier EPS] > [Classes] puis [Actualiser].'), {}),
                         ['https://youtu.be/tu8J1RBUTwk'])

    def test_mot_etablissement_en_minuscule_ne_suffit_pas(self):
        self.assertEqual(supporting_tutorials(audit("Écrire à l'assistance [ici] en précisant l'établissement et son UAI."), {}), [])

    def test_video_unique_de_la_fiche(self):
        text = 'Cliquer sur [Saisir].\n- Vidéo : https://youtu.be/abcdef12'
        self.assertEqual(supporting_tutorials(audit(text, 'data/examens/y.txt'), {}), ['https://youtu.be/abcdef12'])
