"""Rappels d'échéances : bandeau la veille et le jour même ; échéances passées signalées à l'administrateur
pour que la fiche correspondante soit marquée comme passée."""
import datetime
import json
from pathlib import Path

_MOIS = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
         'septembre', 'octobre', 'novembre', 'décembre')
_PATH = Path(__file__).with_name('config') / 'echeances.json'


def load(path=_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return []
    out = []
    for e in data.get('echeances', []):
        try:
            out.append(dict(e, _date=datetime.date.fromisoformat(e['date'])))
        except Exception:
            continue
    return out


def _concerne(e, academie):
    # Académie non encore choisie : le hub est celui d'Aix-Marseille, ses rappels s'affichent.
    return not e.get('academie') or not academie or academie in ('Non précisée', e['academie'])


def date_fr(d):
    return f"{'1er' if d.day == 1 else d.day} {_MOIS[d.month - 1]} {d.year}"


def rappels(today=None, academie=None, items=None):
    """Échéances de demain (J-1) et d'aujourd'hui, pour l'académie de l'utilisateur."""
    today = today or datetime.date.today()
    out = []
    for e in (load() if items is None else items):
        delta = (e['_date'] - today).days
        if delta in (0, 1) and _concerne(e, academie):
            quand = "Aujourd'hui" if delta == 0 else 'Demain'
            heure = (' à ' + e['heure']) if e.get('heure') else ''
            out.append(dict(e, quand=quand, libelle=f"{quand} ({date_fr(e['_date'])}{heure}), {e['academie']} : {e['texte']}"
                            if e.get('academie') else f"{quand} ({date_fr(e['_date'])}{heure}) : {e['texte']}"))
    return out


def a_mettre_a_jour(today=None, items=None):
    """Échéances passées dont la fiche n'a pas encore été revue : pour l'administrateur."""
    today = today or datetime.date.today()
    return [e for e in (load() if items is None else items) if e['_date'] < today and not e.get('fiche_revue')]


def prochaines(today=None, jours=14, items=None):
    today = today or datetime.date.today()
    return [e for e in (load() if items is None else items) if 0 <= (e['_date'] - today).days <= jours]
