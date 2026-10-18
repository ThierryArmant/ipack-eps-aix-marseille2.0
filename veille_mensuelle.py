"""Bandeau admin de la veille : lit le dernier rapport mensuel déposé dans docs/veille/ (aucun appel réseau ni IA)."""
from pathlib import Path
import re

DEPOT = 'https://github.com/ThierryArmant/ipack-eps-aix-marseille2.0/blob/main/'
DOSSIER = Path(__file__).resolve().parent / 'docs' / 'veille'


def dernier_rapport(dossier=DOSSIER):
    """Renvoie {mois, passage, nouveaux, reference, titres, url} ou None s'il n'y a pas encore de rapport."""
    try:
        rapports = sorted(p for p in Path(dossier).glob('*.md') if re.fullmatch(r'\d{4}-\d{2}\.md', p.name))
    except OSError:
        return None
    if not rapports:
        return None
    p = rapports[-1]
    try:
        texte = p.read_text(encoding='utf-8')
    except OSError:
        return None
    m = re.search(r'Passage\s*:\s*([0-9/]+).*?Textes nouveaux\s*:\s*(\d+)', texte)
    titres = re.findall(r'^- \[([^\]]+)\]\((https?://[^)\s]+)\)', texte, re.M)
    return {
        'mois': p.stem,
        'passage': m.group(1) if m else p.stem,
        'nouveaux': int(m.group(2)) if m else len(titres),
        'reference': 'état de référence' in texte,
        'titres': titres[:5],
        'url': DEPOT + 'docs/veille/' + p.name,
    }


def texte_bandeau(rapport):
    """Libellés du bandeau, sans HTML : (titre, phrase)."""
    if not rapport:
        return ('Veille mensuelle des textes', 'Premier passage le 1er novembre 2026 (Bulletin officiel, Éduscol EPS, académie d’Aix-Marseille).')
    if rapport['reference']:
        return (f"Veille mensuelle — passage du {rapport['passage']}", 'État de référence enregistré ; les nouveautés seront signalées à partir du passage suivant.')
    n = rapport['nouveaux']
    if n == 0:
        return (f"Veille mensuelle — passage du {rapport['passage']}", 'Aucun texte nouveau depuis le passage précédent.')
    return (f"Veille mensuelle — passage du {rapport['passage']}", f"{n} texte{'s' if n > 1 else ''} nouveau{'x' if n > 1 else ''} à examiner pour les fiches.")
