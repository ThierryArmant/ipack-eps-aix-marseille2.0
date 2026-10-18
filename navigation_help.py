"""Repérage facultatif, tiré du parcours documenté ; aucune mémoire conversationnelle."""
from pathlib import Path
import html
import re

CLARIFICATION = 'Pouvez-vous préciser ce que vous souhaitez renseigner dans iPackEPS ?'
SOURCE = Path(__file__).resolve().parent / 'data/ipack/situations_2026_10_17/ordre_premiere_connexion_fiche_professeur.txt'


def offer_navigation_help(mode, public, origin, body):
    return (mode == 'ipack' and public == 'Collège (DNB)' and origin == 'clarification'
            and CLARIFICATION in body)


def documented_navigation_help():
    try:
        lines = SOURCE.read_text(encoding='utf-8').splitlines()
    except OSError:
        return ''
    line = next((line for line in lines if line.startswith('Ordre à suivre depuis le tableau de bord : ')), '')
    steps = re.findall(r'(?:^|; )\d\) (.*?)(?=; \d\)|$)', line.partition(': ')[2])
    source = next((line for line in lines if line.startswith('Source : ')), '')
    if len(steps) != 3 or not source:
        return ''
    return ('<p>Si vous avez besoin de vous repérer, voici le début du parcours documenté. '
            'Ce repère ne détermine pas à votre place ce que vous souhaitez saisir. '
            'Si ces étapes sont déjà réalisées, ne recommencez pas les saisies.</p><ol>'
            + ''.join('<li>' + html.escape(step) + '</li>' for step in steps) + '</ol>'
            '<p>Indiquez ensuite simplement le nom de l’écran ou de la rubrique où vous êtes bloqué.</p>'
            '<details><summary>Source du parcours</summary><p>' + html.escape(source) + '</p></details>')
