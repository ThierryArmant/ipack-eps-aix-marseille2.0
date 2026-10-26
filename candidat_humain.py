"""Question qui met en scène un animal comme candidat (« mon chat a fait javelot ») : situation incohérente,
le hub demande une précision au lieu d'appliquer une règle."""
import re
import unicodedata

_ANIMAUX = (r"chat|chatte|chaton|chien|chienne|chiot|canari|perroquet|perruche|hamster|lapin|cochon d.inde|"
            r"poisson rouge|tortue|cheval|poney|furet|souris|rat|serpent|lezard|poule|vache|chevre|mouton|dauphin")


def _norm(text):
    text = unicodedata.normalize('NFKD', str(text).lower().replace('’', "'"))
    return ''.join(c for c in text if not unicodedata.combining(c))


def animal_candidat(question):
    """« mon chat », « avec mon canari », « notre chien »… : possessif + animal. « chat perché », le chat de l'ENT
    ou « tchat » ne déclenchent rien."""
    q = _norm(question)
    m = re.search(r"\b(?:mon|ma|mes|notre|nos|son|sa|ses)\s+(" + _ANIMAUX + r")s?\b(?!\s+perche)", q)
    return m.group(1) if m else ''


def precision_animal(question):
    animaux = []
    q = _norm(question)
    for m in re.finditer(r"\b(?:mon|ma|mes|notre|nos|son|sa|ses)\s+(" + _ANIMAUX + r")s?\b(?!\s+perche)", q):
        if m.group(1) not in animaux:
            animaux.append(m.group(1))
    if not animaux:
        return ''
    cites = ' et '.join(('un ' if a not in ('chatte', 'chienne', 'chevre', 'tortue', 'poule', 'vache', 'souris', 'perruche') else 'une ') + a
                        for a in animaux)
    return ('🐾 Votre question mentionne ' + cites + '. Parlez-vous d’élèves ? Reformulez avec la situation réelle '
            '(élève, examen, activités concernées) et je vous réponds.')
