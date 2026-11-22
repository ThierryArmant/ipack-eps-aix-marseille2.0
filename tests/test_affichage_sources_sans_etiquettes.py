import unittest
import exact_source_answer as e


class AffichageSansEtiquettes(unittest.TestCase):
    def test_retire_etiquette_fiche_prioritaire(self):
        self.assertEqual(e.texte_visible("[FICHE PRIORITAIRE — statut: s_2026-10-16] ### Titre"), "### Titre")

    def test_texte_metier_intact(self):
        self.assertEqual(e.texte_visible("Le vestiaire [1] est séparé."), "Le vestiaire [1] est séparé.")

    def test_ligne_de_provenance(self):
        self.assertTrue(e.ligne_provenance("[Textes Officiels & Juridiques / Partenariats] [DOCUMENT: data/a/b.txt; statut: s]"))
        self.assertTrue(e.ligne_provenance("[DOCUMENT: a; statut: b]"))

    def test_phrase_metier_non_masquee(self):
        self.assertFalse(e.ligne_provenance("L'enseignant organise les tâches [DOCUMENT: x] et le matériel."))
        self.assertFalse(e.ligne_provenance("[DOCUMENT: a]\nSuite du texte métier."))


if __name__ == '__main__':
    unittest.main()
