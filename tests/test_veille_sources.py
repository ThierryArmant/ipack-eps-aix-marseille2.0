import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import veille_sources as v

class VeilleSourcesTests(unittest.TestCase):
    def test_links_filtrage_domaines(self):
        html = '<a href="https://www.education.gouv.fr/bo/2026/Special4">EPPCS session 2027</a><a href="https://example.org/evil">Bac 2027</a><a href="/autre">Accueil</a>'
        links = v.candidates(html, "https://www.education.gouv.fr/bo")
        self.assertEqual(len(links), 1)
        self.assertIn("https://www.education.gouv.fr/bo/2026/Special4", links)
    def test_recherche_rss_filtre_les_liens_non_officiels(self):
        rss = """<rss><channel>
        <item><title>EPPCS session 2027</title><link>https://www.education.gouv.fr/bo/2026/Special4</link></item>
        <item><title>EPS examen 2027</title><link>https://example.org/faux</link></item>
        </channel></rss>"""
        found = v.rss_candidates(rss)
        self.assertEqual(list(found), ["https://www.education.gouv.fr/bo/2026/Special4"])

    def test_collecte_rss_accepte_le_xml_du_moteur(self):
        response = MagicMock()
        response.headers = {"Content-Type": "text/xml; charset=utf-8"}
        response.read.return_value = (
            b"<rss><channel><item><title>EPS 2027</title>"
            b"<link>https://www.education.gouv.fr/bo/2026/Special4</link>"
            b"</item></channel></rss>"
        )
        with patch.object(v, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            links = v.search_fallback("BO national", v.fetch)
            self.assertIn("https://www.education.gouv.fr/bo/2026/Special4", links)
            with self.assertRaises(ValueError):
                v.fetch(v.SOURCES["BO national"])

    def test_tavily_utilise_basic_et_filtre_les_domaines(self):
        response = MagicMock()
        response.read.return_value = b'{"results":[{"url":"https://www.education.gouv.fr/bo/2026/Special4","title":"EPS 2027"},{"url":"https://www.ac-nice.fr/examens","title":"EPS 2027"}]}'
        with patch.object(v, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            links = v.search_tavily("BO national", v.SOURCES["BO national"], "cle-test")
        request = urlopen.call_args.args[0]
        self.assertIn(b'"search_depth": "basic"', request.data)
        self.assertIn(b'"auto_parameters": false', request.data)
        self.assertEqual(list(links), ["https://www.education.gouv.fr/bo/2026/Special4"])

    def test_veille_reutilise_historique_sur_resultats_tavily(self):
        name = "BO national"
        a, b = [f"https://www.education.gouv.fr/bo/2026/{suffix}" for suffix in ("Special4", "Hebdo45")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(v.json.dumps({"sources": {name: {"last_success": "2026-11-11", "links": {a: "EPS"}}}}))
            with patch.dict(v.SOURCES, {name: v.SOURCES[name]}, clear=True):
                with patch.object(v, "search_tavily", return_value={b: "Examens EPS"}):
                    state, report, count, errors = v.run(path, "2026-11-18", lambda url: "", "cle-test")
        self.assertEqual((count, errors), (1, 0))
        self.assertEqual(set(state["sources"][name]["links"]), {a, b})
        self.assertIn("Tavily, résultats non vérifiés", report)

    def test_recherche_de_secours_apres_refus_http(self):
        old = v.SOURCES
        try:
            v.SOURCES = {"BO national": "https://www.education.gouv.fr/bo"}
            def fake(url):
                if "bing.com" in url:
                    return "<rss><channel><item><title>EPS 2027</title><link>https://www.education.gouv.fr/bo/2026/Special4</link></item></channel></rss>"
                raise OSError("HTTP 403")
            with tempfile.TemporaryDirectory() as d:
                state, report, n, errors = v.run(Path(d) / "state.json", "2026-11-18", fake)
                self.assertEqual((n, errors), (0, 0))
                self.assertIn("recherche indirecte", report)
                self.assertEqual(state["sources"]["BO national"]["mode"], "recherche indirecte (résultats non vérifiés)")
        finally:
            v.SOURCES = old

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
