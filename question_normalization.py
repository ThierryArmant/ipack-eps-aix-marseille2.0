"""Copie de recherche locale ; aucune correction probabiliste ni modification des preuves."""
import re
import unicodedata

VERSION = 'espaces-metier-v1'


def _key(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold())
                   if unicodedata.category(c) != 'Mn')


# Liste fermée : uniquement des frontières plausibles, jamais des synonymes.
_BUSINESS = set('''reaffecter affecter deplacer saisir enregistrer importer imprimer
configurer modifier supprimer remplacer valider verrouiller deverrouiller
protocole protocoles enseignant enseignants examinateur examinateurs
etablissement etablissements candidat candidats lot lots note notes
attestation attestations referentiel referentiels'''.split())
_FUNCTION = set('un une le la les des du mes mon ma nos notre votre vos ce cette ces a au aux de dans pour'.split())
_PROTECTED = set('afl aflp afl1 afl2 afl3 asns fca cap gt di ab eps ccf dnb dec diec santorin cyclades imagin ipackeps'.split())
_TYPOS = {'protocloe': 'protocole', 'rempalcer': 'remplacer',
          'reaffceter': 'réaffecter'}


def normalise_question(question):
    """Retourne original, copie de recherche et journal des seules corrections sûres.

    Pas de correction générale des mots inconnus, noms, sigles, chiffres,
    négations, dates ou statuts médicaux. Les caractères des mots sont conservés.
    """
    changes = []
    opaque = [m.span() for m in re.finditer(
        r'https?://\S+|\S+@\S+|\b\S*[/\\]\S*', question)]
    def split(match):
        word = match.group()
        if any(start <= match.start() < end for start, end in opaque):
            return word
        key = _key(word)
        if key in _TYPOS:
            corrected = _TYPOS[key]
            if word.isupper():
                corrected = corrected.upper()
            elif word[0].isupper():
                corrected = corrected.capitalize()
            changes.append({'avant': word, 'apres': corrected, 'type': 'coquille_connue'})
            return corrected
        if key in _BUSINESS | _FUNCTION | _PROTECTED:
            return word
        boundaries = [i for i in range(1, len(word))
                      if ((_key(word[:i]) in _BUSINESS and _key(word[i:]) in _FUNCTION)
                          or (_key(word[:i]) in _FUNCTION and _key(word[i:]) in _BUSINESS))]
        if len(boundaries) != 1:
            return word
        i = boundaries[0]
        corrected = word[:i] + ' ' + word[i:]
        changes.append({'avant': word, 'apres': corrected, 'type': 'espace_manquant'})
        return corrected
    # Lettres uniquement : ne pas découper AFL1, années, identifiants ou chemins.
    value = re.sub(r'(?<![\w/])[A-Za-zÀ-ÖØ-öø-ÿ]+(?![\w/])', split, question)
    value = re.sub(r'\s+', ' ', value).strip()
    if value != question and not changes:
        changes.append({'type': 'espaces'})
    return {'original': question, 'recherche': value, 'corrections': changes,
            'version': VERSION}
