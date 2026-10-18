"""Demandes explicites de repérage, indépendantes des questions métier."""
import re
import unicodedata

MESSAGE = 'Pas d’inquiétude, nous allons avancer étape par étape. Ouvrez le guide ci-dessous et choisissez simplement une rubrique.'
PUBLICS = ('Collège', 'Collège (DNB)', 'Lycée Général & Techno', 'Lycée Pro / CAP', 'Lycée voie générale', 'Lycée voie professionnelle')

def requests_guide(question, mode, public):
    if mode != 'ipack' or public not in PUBLICS:
        return False
    q = ''.join(c for c in unicodedata.normalize('NFD', question.lower()) if unicodedata.category(c) != 'Mn')
    words = re.findall(r'[a-z]+', q)
    # Une demande générique seulement : une question précise reste dans son circuit habituel.
    allowed = set('aide aidez aider moi nous pouvez vous peux tu svp s il te vous plait bonjour merci je j on suis est perdu perdue perdus perdues completement totalement un peu vraiment ici dans sur avec ipack ipackeps le hub ne n sais sait savons pas plus par ou quoi comment commencer faire me m y retrouver guide guider besoin d de et au secours rien comprends comprend comprendrais arrive utiliser'.split())
    return (bool(words) and set(words) <= allowed and
            bool(re.search(r'perdu|par ou commencer|(?:aide|aidez|guide|guidez)[ -]moi|au secours|(?:m.y|me) retrouver', q)))
