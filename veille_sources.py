"""Veille EPS : détection prudente de liens officiels, sans interprétation réglementaire automatique."""
import argparse
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
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

def fetch(url):
    req = Request(url, headers={"User-Agent": "HUB-IA-EPS-Veille/1.0 (public documentation)", "Accept": "text/html"})
    with urlopen(req, timeout=18) as res:
        ctype = res.headers.get("Content-Type", "")
        if "html" not in ctype:
            raise ValueError("Format non HTML : " + ctype)
        return res.read(1_000_000).decode("utf-8", "replace")

def run(state_path=STATE, today=None, fetcher=fetch):
    today = today or date.today().isoformat()
    old = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"sources": {}}
    result = {"date": today, "sources": {}}
    lines = [f"# Veille EPS — {today}", "", "Repérage automatique, **sans validation réglementaire**. Toute publication doit être lue et confrontée aux fiches avant intégration.", ""]
    total_new = 0
    errors = 0
    for name, url in SOURCES.items():
        previous = old.get("sources", {}).get(name, {})
        try:
            found = candidates(fetcher(url), url)
            previous_links = previous.get("links", {})
            new = {u: t for u, t in found.items() if u not in previous_links}
            first = not previous.get("last_success")
            if first:
                new = {}  # Premier relevé = état de référence, pas nouveauté.
            total_new += len(new)
            result["sources"][name] = {"url": url, "last_success": today, "links": found}
            lines += [f"## {name}", f"Source : {url}", f"Liens repérés : {len(found)} ; {'premier état de référence' if first else str(len(new)) + ' nouveaux liens à examiner'}.", ""]
            for u, t in list(new.items())[:40]:
                lines.append(f"- [{t.replace(']', '')}]({u}) — **à vérifier**")
            lines.append("")
        except Exception as exc:
            errors += 1
            result["sources"][name] = previous
            lines += [f"## {name}", f"**ÉCHEC DE CONSULTATION : {type(exc).__name__}**. Aucune conclusion sur l'absence de nouveautés.", ""]
    lines.insert(3, f"**Résultat : {total_new} liens nouveaux à examiner ; {errors} sources indisponibles.** Le nombre de liens ne correspond pas au nombre de nouveaux textes.")
    lines += ["## Contrôles humains obligatoires", "- Vérifier date, NOR, session, diplôme, académie et entrée en vigueur.", "- Comparer les fiches existantes avant toute modification ; ne pas remplacer une règle nationale par une consigne locale.", "- Vérifier explicitement les documents DIEC et les bulletins académiques de la session en cours.", ""]
    return result, "\n".join(lines), total_new, errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=date.today().isoformat())
    p.add_argument("--state", type=Path, default=STATE)
    args = p.parse_args()
    state, report, _, _ = run(args.state, args.date)
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.state.parent / ("controle-" + args.date + ".md")).write_text(report, encoding="utf-8")
    print(report)

if __name__ == "__main__":
    main()
