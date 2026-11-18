"""Veille EPS : détection prudente de liens officiels, sans interprétation réglementaire automatique."""
import argparse
from datetime import date
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse, urlencode
from xml.etree import ElementTree
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "docs/veille/surveillance.json"
SOURCES = {
    "BO national": "https://www.education.gouv.fr/bo",
    "BO EPS": "https://www.education.gouv.fr/bo/recherche?search_api_fulltext=education%20physique%20sportive",
    "Aix-Marseille bulletins": "https://bulacad.ac-aix-marseille.fr/",
    "Aix-Marseille examens": "https://www.ac-aix-marseille.fr/examens-et-concours-121498",
    "Aix-Marseille aménagements": "https://www.ac-aix-marseille.fr/amenagement-d-epreuves-aux-examens-121669",
    "Nice": "https://www.ac-nice.fr/",
    "Créteil iPackEPS": "https://ipackeps.ac-creteil.fr/",
    "Éduscol EPS": "https://eduscol.education.gouv.fr/4434/education-physique-et-sportive",
}
KEYWORDS = re.compile(r"eps|physique et sportive|eppcs|cyclades|santorin|baccalaur|\bbac\b|\bcap\b|\bbma\b|examens|amenagement|inaptitude|certificati|2027|2028|bulletin academique|\bbo\b", re.I)
ALLOWED_HOSTS = ("education.gouv.fr", "eduscol.education.gouv.fr", "ac-aix-marseille.fr", "bulacad.ac-aix-marseille.fr", "ac-nice.fr", "ipackeps.ac-creteil.fr")
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text = []
    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(" ".join(self.text).split())))
            self.href = None
            self.text = []

def allowed(url):
    p = urlparse(url)
    return p.scheme == "https" and any(p.hostname == h or p.hostname.endswith("." + h) for h in ALLOWED_HOSTS if p.hostname)

def candidates(html, base):
    parser = Links()
    parser.feed(html)
    found = {}
    for href, title in parser.links:
        url = urljoin(base, href).split("#")[0]
        if allowed(url) and KEYWORDS.search(title + " " + url):
            found[url] = title[:180] or url
    return found

SEARCH_QUERIES = {
    "BO national": "site:education.gouv.fr/bo EPS examen 2027",
    "BO EPS": "site:education.gouv.fr/bo EPS EPPCS baccalauréat",
    "Aix-Marseille bulletins": "site:ac-aix-marseille.fr bulletin académique EPS 2027",
    "Aix-Marseille examens": "site:ac-aix-marseille.fr DIEC EPS examens 2027",
    "Aix-Marseille aménagements": "site:ac-aix-marseille.fr aménagement épreuves EPS 2027",
    "Nice": "site:ac-nice.fr EPS examens 2027",
    "Créteil iPackEPS": "site:ac-creteil.fr iPackEPS 2027",
    "Éduscol EPS": "site:eduscol.education.gouv.fr EPS baccalauréat 2027",
}

def rss_candidates(xml_text):
    """Résultats de moteur de recherche : pistes, jamais preuves de publication."""
    root = ElementTree.fromstring(xml_text)
    found = {}
    for item in root.findall(".//item"):
        url = (item.findtext("link") or "").strip().split("#")[0]
        title = (item.findtext("title") or "").strip()
        if allowed(url) and KEYWORDS.search(title + " " + url):
            found[url] = title[:180] or url
    return found

def search_fallback(name, fetcher):
    query = SEARCH_QUERIES.get(name)
    if not query:
        return {}
    url = "https://www.bing.com/search?" + urlencode({"q": query, "format": "rss"})
    return rss_candidates(fetcher(url))

def search_tavily(name, source_url, api_key):
    host = urlparse(source_url).hostname.removeprefix("www.")
    data = json.dumps({
        "query": SEARCH_QUERIES[name],
        "search_depth": "basic",
        "auto_parameters": False,
        "max_results": 10,
        "include_domains": [host],
        "include_answer": False,
        "include_raw_content": False,
    }).encode("utf-8")
    request = Request("https://api.tavily.com/search", data=data, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })
    with urlopen(request, timeout=18) as response:
        payload = json.loads(response.read(1_000_000))
    found = {}
    for item in payload["results"]:
        url = (item.get("url") or "").strip().split("#")[0]
        title = (item.get("title") or "").strip()
        result_host = urlparse(url).hostname or ""
        if (
            allowed(url)
            and (result_host == host or result_host.endswith("." + host))
            and KEYWORDS.search(title + " " + url)
        ):
            found[url] = title[:180] or url
    return found


def fetch(url):
    parsed = urlparse(url)
    rss = parsed.hostname == "www.bing.com" and parsed.path == "/search"
    accepted = ("application/rss+xml", "application/xml", "text/xml") if rss else ("text/html", "application/xhtml+xml")
    req = Request(url, headers={
        "User-Agent": "HUB-IA-EPS-Veille/1.0 (public documentation)",
        "Accept": ", ".join(accepted),
    })
    with urlopen(req, timeout=18) as res:
        content_type = res.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type not in accepted:
            raise ValueError("Format inattendu : " + content_type)
        return res.read(1_000_000).decode("utf-8", "replace")

def run(state_path=STATE, today=None, fetcher=fetch, tavily_api_key=None):
    today = today or date.today().isoformat()
    old = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"sources": {}}
    result = {"date": today, "sources": {}}
    lines = [f"# Veille EPS — {today}", "", "Repérage automatique, **sans validation réglementaire**. Toute publication doit être lue et confrontée aux fiches avant intégration.", ""]
    if not tavily_api_key:
        lines.append("Tavily indisponible : le secret de la veille n’est pas configuré.")
    total_new = 0
    errors = 0
    for name, url in SOURCES.items():
        previous = old.get("sources", {}).get(name, {})
        try:
            mode = "direct"
            try:
                found = candidates(fetcher(url), url)
                if not found:
                    raise ValueError("Page accessible mais aucun lien EPS pertinent détecté")
            except Exception as direct_error:
                found = {}
                tavily_note = "Tavily non configuré"
                mode = "recherche indirecte (résultats non vérifiés)"
                if tavily_api_key and name in SEARCH_QUERIES:
                    try:
                        found = search_tavily(name, url, tavily_api_key)
                        tavily_note = "Tavily sans résultat officiel exploitable"
                        if found:
                            mode = "recherche indirecte (Tavily, résultats non vérifiés)"
                    except Exception as exc:
                        tavily_note = f"Tavily indisponible ({type(exc).__name__})"
                        if getattr(exc, "code", None) is not None:
                            tavily_note += f" HTTP {exc.code}"
                if not found:
                    try:
                        found = search_fallback(name, fetcher)
                    except Exception as search_error:
                        raise ValueError(f"Direct : {direct_error}; {tavily_note}; RSS : {search_error}") from search_error
                    if not found:
                        raise ValueError(f"Direct : {direct_error}; {tavily_note}; RSS sans résultat exploitable")
            previous_links = previous.get("links", {})
            new = {u: t for u, t in found.items() if u not in previous_links}
            first = not previous.get("last_success")
            if first:
                new = {}  # Premier relevé = état de référence, pas nouveauté.
            total_new += len(new)
            result["sources"][name] = {"url": url, "last_success": today, "mode": mode, "links": previous_links | found}
            lines += [f"## {name}", f"Source : {url}", f"Mode : {mode}.", f"Liens repérés : {len(found)} ; {'premier état de référence' if first else str(len(new)) + ' nouveaux liens à examiner'}.", ""]
            for u, t in list(new.items())[:40]:
                lines.append(f"- [{t.replace(']', '')}]({u}) — **à vérifier**")
            lines.append("")
        except Exception as exc:
            errors += 1
            result["sources"][name] = previous
            lines += [f"## {name}", f"**ÉCHEC DE CONSULTATION OU D’EXTRACTION : {type(exc).__name__} — {str(exc)[:180]}**. Aucune conclusion sur l'absence de nouveautés.", ""]
    lines.insert(3, f"**Résultat : {total_new} liens nouveaux à examiner ; {errors} sources non exploitables.** Le nombre de liens ne correspond pas au nombre de nouveaux textes.")
    if any(v.get("mode", "").startswith("recherche indirecte") for v in result["sources"].values()):
        lines.insert(4, "**ATTENTION : certains liens proviennent d’un moteur de recherche. Leur publication, leur date et leur portée doivent être vérifiées sur le site officiel.**")
    if errors:
        lines.insert(4, "**ALERTE QUALITÉ : veille incomplète. Ne pas conclure à l’absence de nouveaux textes.**")
    lines += ["## Contrôles humains obligatoires", "- Vérifier date, NOR, session, diplôme, académie et entrée en vigueur.", "- Comparer les fiches existantes avant toute modification ; ne pas remplacer une règle nationale par une consigne locale.", "- Vérifier explicitement les documents DIEC et les bulletins académiques de la session en cours.", ""]
    return result, "\n".join(lines), total_new, errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=date.today().isoformat())
    p.add_argument("--state", type=Path, default=STATE)
    args = p.parse_args()
    state, report, _, errors = run(args.state, args.date, tavily_api_key=os.environ.get("TAVILY_API_KEY"))
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.state.parent / ("controle-" + args.date + ".md")).write_text(report, encoding="utf-8")
    print(report)
    if state["sources"] and errors == len(state["sources"]):
        raise SystemExit("ÉCHEC : aucune source officielle exploitable ; rapport enregistré.")

if __name__ == "__main__":
    main()
