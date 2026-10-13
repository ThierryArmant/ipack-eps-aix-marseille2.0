"""Régénère config/portee_academique.json à partir des fiches.

Une ligne est marquée « consigne d'Aix-Marseille » si elle nomme explicitement l'académie
(Aix, Marseille, DIEC, BA académique numéroté, ESTEREL, adresse ac-aix), hors simple glose
entre parenthèses du type « (DIEC à Aix-Marseille) » ajoutée à un acteur générique.
Toute ligne d'une section dont le titre nomme Aix est aussi marquée, sauf les lignes de
cadre national. Les règles nationales et le fonctionnement des logiciels ne sont pas marqués.

Usage, après toute modification de fiche :  python portee_registre.py --write
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRE = ROOT / 'config' / 'portee_academique.json'

AIX = re.compile(r"\bAix\b|Marseille|\bDIEC|ESTEREL|\bBA (?:sp[ée]cial )?n?°? ?\d{3,4}\b|ac-aix|"
                 r"bulletin acad[ée]mique d.Aix", re.I)
GLOSE = re.compile(r"\((?!Source)(?=[^()]{0,80}\bDIEC\b)[^()]{0,80}\)", re.I)
NATIONAL = re.compile(r"cadre national|texte national|\bMENE\d|\bBO\b|note de service|\barticle [DLR]\.? ?\d", re.I)
# « Aucune consigne d'Aix trouvée » constate une absence : ce n'est pas une consigne d'Aix.
ABSENCE = re.compile(r"\b(?:aucune|sans|pas de) consignes?[^.]{0,40}\bAix", re.I)
IGNOREES = ('Sigles', 'Source', 'Sources', 'http', 'Nature de', 'Nature des', 'Fiche de contrôle',
            '[PORTEE', '[DOCUMENT', 'Portée :', 'Recoupement')
REGLE = ("Ligne marquée si elle nomme explicitement l'académie d'Aix-Marseille (Aix, Marseille, DIEC, BA académique "
         "numéroté, ESTEREL, adresse ac-aix), hors simple glose « DIEC à Aix-Marseille » entre parenthèses. Toute "
         "ligne d'une section dont le titre nomme Aix est marquée, sauf les lignes de cadre national. Les règles "
         "nationales et le fonctionnement des logiciels ne sont pas marqués. Généré par portee_registre.py.")


def lignes_aix(texte):
    section, sections = '(début)', {}
    for ligne in texte.splitlines():
        if ligne.startswith('###'):
            section = ligne.strip()
            continue
        t = ligne.strip()
        if not t or t.startswith(IGNOREES) or ABSENCE.search(t):
            continue
        section_aix = bool(re.search(r"\bAix\b|Marseille", section)) and not re.search(r"sans consigne", section, re.I)
        if AIX.search(GLOSE.sub('', t)) or (section_aix and not NATIONAL.search(t)):
            sections.setdefault(section, []).append(t)
    return [{'section': s, 'lignes': l} for s, l in sections.items()]


def inventaire():
    fichiers = json.loads((ROOT / 'config' / 'nature_sources.json').read_text(encoding='utf-8'))['fichiers']
    out = {}
    for chemin in sorted(fichiers):
        sections = lignes_aix((ROOT / chemin).read_text(encoding='utf-8'))
        if sections:
            out[chemin] = {'academie': 'aix-marseille', 'sections': sections}
    return out


if __name__ == '__main__':
    registre = json.loads(REGISTRE.read_text(encoding='utf-8'))
    registre['fichiers'] = inventaire()
    registre['regle'] = REGLE
    if '--write' in sys.argv:
        REGISTRE.write_text(json.dumps(registre, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(len(registre['fichiers']), 'fichiers,',
          sum(len(s['lignes']) for v in registre['fichiers'].values() for s in v['sections']), 'lignes')
