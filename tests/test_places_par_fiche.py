"""Une même fiche ne prend pas plus de deux des dix places tant que d'autres fiches attendent."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from document_retrieval import retrieve_documents


def _node(path, label):
    text = '[DOCUMENT: ' + path + '; statut: s]\n' + label
    return SimpleNamespace(node=SimpleNamespace(text=text, metadata={'path': path, 'title': 'T'}), score=0.5)


def _run(ipack_nodes, santorin_nodes):
    r_ipack, r_sant = Mock(), Mock()
    r_ipack.retrieve.return_value = ipack_nodes
    r_sant.retrieve.return_value = santorin_nodes
    q = 'comment modifier un groupe dans ipackeps'
    extraits, *_ = retrieve_documents(prompt=q, p_norm=q, p_low=q,
        niveau_actuel_form='Lycée Général & Techno', mode='ipack', est_college=False,
        est_clairement_lycee=True, mots_cles_intention_peda=[], recherche_mots={},
        chercher_par_mots=Mock(return_value=[]), retriever_textes=None, retriever_peda=None,
        retriever_santorin=r_sant, retriever_ipack=r_ipack,
        libelle_source=lambda *a: '', _url_source=lambda *a: '', reference_notice=Mock(return_value=[]))
    return extraits


class PlacesParFiche(unittest.TestCase):
    def test_troisieme_fragment_cede_sa_place_a_une_autre_base(self):
        ipack = [_node('data/ipack/a.txt', f'A{i}') for i in range(6)] + \
                [_node(f'data/ipack/b{i}.txt', f'B{i}') for i in range(4)]
        sant = [_node('data/examens/s.txt', 'S0')]
        texte = _run(ipack, sant)
        self.assertIn('A0', texte)
        self.assertIn('A1', texte)
        self.assertIn('S0', texte)          # la bonne fiche d'une autre base entre
        for i in range(4):
            self.assertIn(f'B{i}', texte)
        self.assertLessEqual(texte.count('[DOCUMENT: '), 10)

    def test_places_libres_rendues_aux_fragments_en_attente(self):
        texte = _run([_node('data/ipack/a.txt', f'A{i}') for i in range(5)], [])
        for i in range(5):
            self.assertIn(f'A{i}', texte)   # rien n'est perdu quand il reste de la place

    def test_ordre_des_deux_premiers_fragments_conserve(self):
        texte = _run([_node('data/ipack/a.txt', 'A0'), _node('data/ipack/c.txt', 'C0'),
                      _node('data/ipack/a.txt', 'A1')], [])
        self.assertLess(texte.index('A0'), texte.index('C0'))
        self.assertLess(texte.index('C0'), texte.index('A1'))


if __name__ == '__main__':
    unittest.main()
