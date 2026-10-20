"""Prototype local de clarification : aucune dépendance IA, aucune action sur le hub.

Les suggestions portent sur une information absente, pas sur la qualité du français.
Ce module n'est pas branché dans app.py ; il sert d'abord à mesurer les faux positifs.
"""
import json
import re
import unicodedata
from pathlib import Path

_CONFIG = Path(__file__).resolve().parent / 'config' / 'lexique_clarification.json'


def normalized(text):
    text = str(text or '').lower().replace('’', "'").replace('œ', 'oe')
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if not unicodedata.combining(c))


def suggestions(question, *, public='', mode='', academy='', rules=None):
    """Retourne au plus un conseil expérimental ; ne bloque et ne transforme rien."""
    q = normalized(question).strip()
    if len(q.split()) < 3:
        return []
    if rules is None:
        rules = json.loads(_CONFIG.read_text(encoding='utf-8'))['regles']
    found = []
    for rule in rules:
        if mode not in rule.get('modes', []):
            continue
        if any(re.search(p, q) for p in rule.get('exclure_motifs', [])):
            continue
        # Les motifs de ce lexique décrivent la phrase complète, jamais une
        # recherche répétée à chaque position ni la question enrichie du catalogue.
        if not any(re.search('^(?:' + p + ')', q) if p.startswith(('(?=', '(?!'))
                   else re.search(p, q) for p in rule['motifs']):
            continue
        found.append(rule)
    if not found:
        return []
    rule = max(found, key=lambda r: r.get('priorite', 0))
    return [{'id': rule['id'], 'message': rule['message'],
             'options': list(rule['options']), 'blocking': False,
             'statut': 'suggestion_experimentale'}]
