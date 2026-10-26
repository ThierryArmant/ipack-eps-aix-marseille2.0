"""Tutoriels issus des preuves réellement utilisées, indépendants de la prose IA."""
import re
from pathlib import Path
from urllib.parse import urlparse
import json

_PARCOURS = None


def _parcours():
    """Parcours vidéo de l'assistance iPackEPS : repli quand la fiche utilisée n'a pas sa propre vidéo."""
    global _PARCOURS
    if _PARCOURS is None:
        try:
            data = json.loads((Path(__file__).resolve().parent / 'config' / 'tutoriels_parcours_college.json').read_text(encoding='utf-8'))
            _PARCOURS = [{'url': t['url'], 'motifs': [t['motif']]} for t in data.get('tutoriels', [])]
        except (OSError, ValueError, KeyError):
            _PARCOURS = []
    return _PARCOURS


_SECTION_CACHE = {}


def _section_video(path, passage_text, heading=''):
    """Vidéo de la section (« ### … ») d'où vient le passage : une fiche de transcriptions contient une
    vidéo par section, la bonne est celle du passage affiché, pas la première de la fiche."""
    if not path or not passage_text:
        return None
    if path not in _SECTION_CACHE:
        try:
            text = (Path(__file__).resolve().parent / path).read_text(encoding='utf-8')
        except OSError:
            text = ''
        blocks = re.split(r'(?m)^(?=###\s)', text)
        _SECTION_CACHE[path] = [(b, re.findall(r'Vid[ée]os?\s*:\s*(https://\S+)', b, re.I)) for b in blocks]
    probe = re.sub(r'\s+', ' ', passage_text.strip().lstrip('-').strip())
    if len(probe) < 20:
        return None
    found = [urls[0] for block, urls in _SECTION_CACHE[path] if urls and probe in re.sub(r'\s+', ' ', block)]
    if len(found) > 1 and heading:
        # Ligne identique dans plusieurs sections : le titre de section du passage tranche.
        head = re.sub(r'\s+', ' ', heading.strip())
        found = [urls[0] for block, urls in _SECTION_CACHE[path]
                 if urls and probe in re.sub(r'\s+', ' ', block) and head and head in block.split('\n', 1)[0]]
    return found[0].rstrip('.,;)') if len(found) == 1 else None


def _valid_url(value):
    return isinstance(value, str) and urlparse(value).scheme == 'https' and bool(urlparse(value).netloc)


def supporting_tutorials(audit, catalogue, limit=1):
    if not audit or audit.get('final_rejections'):
        return []
    packets = {p['id']: p for p in audit.get('documents', [])}
    result=[]
    claims = list(audit.get('accepted_claims', []))
    if not claims:
        # Mode documenté : pas d'affirmations rédigées, les preuves sont les passages retenus et affichés.
        report = audit.get('exact_extracts') or {}
        spans = {s['id']: s.get('text', '') for src in report.get('selected_sources', [])
                 for s in src.get('passages', [])}
        headings = {s['id']: s.get('section', '') for src in report.get('selected_sources', [])
                    for s in src.get('passages', [])}
        claims = [{'text': spans[i], 'exact': True, 'heading': headings.get(i, ''),
                   'evidence': [{'document_id': re.match(r'(D\d+)', i).group(1)}]}
                  for i in report.get('focused_passage_ids', []) if i in spans and re.match(r'D\d+', i)]
    for claim in claims:
        text=claim.get('text', '')
        if claim.get('exact'):
            # Passage d'une section de fiche qui porte sa propre vidéo : c'est la vidéo de ce passage.
            for evidence in claim.get('evidence', []):
                packet = packets.get(evidence.get('document_id'), {})
                url = _section_video(packet.get('path', ''), text, claim.get('heading', ''))
                if _valid_url(url) and url not in result:
                    result.append(url)
                    if len(result) >= limit:
                        return result
        if not (claim.get('section') == 'etape' or re.search(
                r'clic|menu|onglet|bouton|ouvrir|s[ée]lectionn|choisir|\[', text, re.I)):
            continue
        for evidence in claim.get('evidence', []):
            packet=packets.get(evidence.get('document_id'), {})
            metadata=catalogue.get(packet.get('path', ''), {})
            candidates=list(metadata.get('tutoriels', []))
            # Une fiche à vidéo unique peut être associée sans faire recopier son URL au modèle.
            body=packet.get('text', '')
            urls=re.findall(r'^\s*-?\s*Vid[ée]o\s*:\s*(https://\S+)', body, re.M | re.I)
            if len(set(urls)) == 1:
                candidates.append({'url':urls[0]})
            if not candidates and str(packet.get('path', '')).startswith('data/ipack/'):
                candidates = list(_parcours())
            for candidate in candidates:
                url=candidate.get('url', '')
                motifs=candidate.get('motifs', [])
                # Passages exacts : motifs pris à la lettre (ils portent leurs majuscules), sinon « l'établissement »
                # suffirait à proposer la vidéo « Saisie établissement ».
                flags = 0 if claim.get('exact') else re.I
                if _valid_url(url) and (not motifs or any(re.search(m, text, flags) for m in motifs)) and url not in result:
                    result.append(url)
                    if len(result) >= limit:
                        return result
    return result
