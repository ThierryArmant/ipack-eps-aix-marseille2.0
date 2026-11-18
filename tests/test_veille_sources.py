import tempfile
import unittest
from pathlib import Path
import veille_sources as v

class VeilleSourcesTests(unittest.TestCase):
    def test_links_filtrage_domaines(self):
        html = '<a href="https://www.education.gouv.fr/bo/2026/Special4">EPPCS session 2027</a><a href="https://example.org/evil">Bac 2027</a><a href="/autre">Accueil</a>'
        links = v.candidates(html, "https://www.education.gouv.fr/bo")
        self.assertEqual(len(links), 1)
        self.assertIn("https://www.education.gouv.fr/bo/2026/Special4", links)
    def test_page_sans_liens_ne_devient_pas_reference_valide(self):
        old = v.SOURCES
        try:
            v.SOURCES = {"BA Aix": "https://bulacad.ac-aix-marseille.fr/"}
            with tempfile.TemporaryDirectory() as d:
                state, report, n, errors = v.run(Path(d) / "state.json", "2026-11-18", lambda url: "<html><body>Accueil</body></html>")
                self.assertEqual((n, errors), (0, 1))
                self.assertEqual(state["sources"]["BA Aix"], {})
                self.assertIn("ALERTE QUALITÉ", report)
        finally:
            v.SOURCES = old

    def test_reference_et_panne_conserve_etat(self):
        old = v.SOURCES
        try:
            v.SOURCES = {"BO national": "https://www.education.gouv.fr/bo"}
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "state.json"
                html = '<a href="/bo/2026/Special4">EPPCS 2027</a>'
                state, report, n, errors = v.run(path, "2026-11-18", lambda u: html)
                self.assertEqual((n, errors), (0, 0))
                self.assertIn("état de référence", report)
                path.write_text(__import__("json").dumps(state))
                state2, report2, n2, errors2 = v.run(path, "2026-11-19", lambda u: html + '<a href="/bo/2026/Hebdo45">EPS examens 2027</a>')
                self.assertEqual((n2, errors2), (1, 0))
                path.write_text(__import__("json").dumps(state2))
                state3, report3, n3, errors3 = v.run(path, "2026-11-20", lambda u: (_ for _ in ()).throw(OSError("refus")))
                self.assertEqual((n3, errors3), (0, 1))
                self.assertEqual(state3["sources"]["BO national"]["links"], state2["sources"]["BO national"]["links"])
                self.assertIn("ÉCHEC DE CONSULTATION", report3)
        finally:
            v.SOURCES = old

if __name__ == "__main__":
    unittest.main()
