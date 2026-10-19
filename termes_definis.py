"""Termes définis par les textes, signalés dans la réponse affichée (sans appel IA).

« À titre exceptionnel » (transport d'élèves par un enseignant) : le mot est surligné et sa définition,
tirée de la note de service n° 86-101 et de la fiche « Texte transport des élèves », est ajoutée une fois
sous la réponse."""
import html as _html
import re
import unicodedata

DEFINITION_EXCEPTIONNEL = (
    "« À titre exceptionnel » (transport d'élèves par un enseignant) : en dernier recours, c'est-à-dire en cas "
    "d'absence momentanée d'un transporteur professionnel ou de refus de celui-ci (note de service n° 86-101) ; "
    "pour un déplacement donné, avec un ordre de mission précis et ponctuel, jamais à l'année ; pour une activité "
    "obligatoire ou de l'association sportive ; décision au cas par cas du chef d'établissement, avec l'accord "
    "exprès de l'enseignant. Une organisation habituelle ou choisie d'avance pour éviter le coût d'un transporteur "
    "n'est pas exceptionnelle au sens de ces textes.")

_MOT = re.compile(r"(?<![\w-])(exceptionnel(?:le)?s?|exceptionnellement)(?![\w-])", re.IGNORECASE)
_TRANSPORT = re.compile(r"minibus|vehicule|voiture|transport|conduir|conducteur|ordre de mission|covoitur|autocar|\bcar\b|\bbus\b")


def _norm(text):
    text = str(text or '').lower()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def mark_exceptionnel(body, question=''):
    """Surligne « exceptionnel » dans une réponse sur le transport d'élèves et ajoute la définition une fois."""
    if not body or not _MOT.search(body) or not (_TRANSPORT.search(_norm(question)) or _TRANSPORT.search(_norm(body))):
        return body
    titre = _html.escape(DEFINITION_EXCEPTIONNEL, quote=True)
    parts = re.split(r'(<[^>]+>)', body)
    for i, part in enumerate(parts):
        if part.startswith('<'):
            continue
        parts[i] = _MOT.sub(lambda m: '<span class="terme-defini" title="' + titre + '" style="color:#F59E0B;'
                            'font-weight:600;border-bottom:1px dotted #F59E0B;cursor:help">' + m.group(1) + '</span>', part)
    return ''.join(parts) + ('<div class="terme-defini-note" style="margin-top:0.8em;padding:0.5em 0.8em;'
                             'border-left:4px solid #F59E0B;background:rgba(245,158,11,0.10);border-radius:6px">'
                             '<strong style="color:#F59E0B">' + _html.escape(DEFINITION_EXCEPTIONNEL.split(' : ', 1)[0]) +
                             '</strong> : ' + _html.escape(DEFINITION_EXCEPTIONNEL.split(' : ', 1)[1]) + '</div>')
