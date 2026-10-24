"""Une fiche prioritaire transmise en entier n'est pas répétée par ses propres fragments indexés."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from document_retrieval import retrieve_documents

PRIO = 'data/ipack/qui_contacter_assistance_ipackeps.txt'
AUTRE = 'data/examens/erreurs_cyclades_santorin.txt'


def _node(path, text):
    return SimpleNamespace(node=SimpleNamespace(text=text, metadata={'path': path, 'title': 'T'}), score=0.5)


def _run(prioritaires, nodes, mots=()):
    retriever = Mock()
    retriever.retrieve.return_value = nodes
    notice = Mock(return_value=[(p, {'title': 'Fiche', 'priorite': 285, 'statut': 's'}) for p in prioritaires])
    q = 'qui contacter pour un probleme santorin'
    extraits, *_ = retrieve_documents(prompt=q, p_norm=q, p_low=q,
        niveau_actuel_form='Lycée Général & Techno', mode='examens', est_college=False,
        est_clairement_lycee=True, mots_cles_intention_peda=[], recherche_mots={},
        chercher_par_mots=Mock(return_value=list(mots)), retriever_textes=None, retriever_peda=None,
        retriever_santorin=retriever, retriever_ipack=None,
        libelle_source=lambda *a: '', _url_source=lambda *a: '', reference_notice=notice)
    return extraits


class FragmentsFichePrioritaire(unittest.TestCase):
    def test_fragment_vectoriel_de_la_fiche_entiere_ignore(self):
        texte = _run([PRIO], [_node(PRIO, '[DOCUMENT: ' + PRIO + '; statut: s]\nFRAGMENT-PRIO'),
                              _node(AUTRE, '[DOCUMENT: ' + AUTRE + '; statut: s]\nFRAGMENT-AUTRE')])
        self.assertNotIn('FRAGMENT-PRIO', texte)
        self.assertIn('FRAGMENT-AUTRE', texte)

    def test_fragment_par_mots_de_la_fiche_entiere_ignore(self):
        texte = _run([PRIO], [], mots=['[DOCUMENT: ' + PRIO + '; statut: s]\nMOTS-PRIO',
                                       '[DOCUMENT: ' + AUTRE + '; statut: s]\nMOTS-AUTRE'])
        self.assertNotIn('MOTS-PRIO', texte)
        self.assertIn('MOTS-AUTRE', texte)

    def test_sans_fiche_prioritaire_fragments_conserves(self):
        texte = _run([], [_node(PRIO, '[DOCUMENT: ' + PRIO + '; statut: s]\nFRAGMENT-PRIO')])
        self.assertIn('FRAGMENT-PRIO', texte)


if __name__ == '__main__':
    unittest.main()
