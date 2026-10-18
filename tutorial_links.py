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


def _valid_url(value):
    return isinstance(value, str) and urlparse(value).scheme == 'https' and bool(urlparse(value).netloc)


def supporting_tutorials(audit, catalogue, limit=1):
    if not audit or audit.get('final_rejections'):
        return []
    packets = {p['id']: p for p in audit.get('documents', [])}
    result=[]
    for claim in audit.get('accepted_claims', []):
        text=claim.get('text', '')
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
                if _valid_url(url) and (not motifs or any(re.search(m, text, re.I) for m in motifs)) and url not in result:
                    result.append(url)
                    if len(result) >= limit:
                        return result
    return result
