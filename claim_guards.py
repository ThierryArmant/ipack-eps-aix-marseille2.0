"""Contrôles ciblés de restitution ; aucune nouvelle décision réglementaire."""
import re
from evidence_logic import normalized

_ABSENCE = re.compile(r"(?:aucun\w*|pas de|absence de).{0,90}(?:consigne|texte|regle|procedure|documentation).{0,60}(?:(?:re)?trouv|disponible|etabli)|(?:consigne|texte|regle|procedure).{0,60}(?:non (?:re)?trouve|non etabli)|\ba verifier\b")
_CATEGORICAL = re.compile(r"\b(?:interdit\w*|obligatoire\w*|autorise\w*|impossible|devez|doit|doivent|ne (?:peut|peuvent).{0,20}pas|n.est.{0,15}pas (?:permis|autorise))\b")
_LIMIT = re.compile(r"(?:ne|n').{0,55}(?:peut|permet|permettent).{0,20}pas.{0,35}(?:confirmer|affirmer|conclure|etablir)|(?:pas|aucun\w*).{0,65}(?:consigne|texte|regle|procedure).{0,60}(?:(?:re)?trouv|etabli)|reste a (?:verifier|confirmer)|a faire confirmer")


def documentary_limit(text):
    """Constat de recherche borné au corpus, jamais une inexistence de règle."""
    value = normalized(text)
    if re.search(r"n'existe|n'existent|reponse directe|ne pas repondre|pour les (?:questions|situations)", value):
        return False
    return bool(re.search(r"aucun texte de la base|aucune consigne de la base|(?:aucun\w*|pas de|absence de).{0,75}(?:consigne|texte|regle|procedure).{0,65}(?:(?:re)?trouv|dans (?:la base|le corpus|la documentation))", value))


def unsupported_certainty(text, supports):
    """Le silence documentaire seul ne prouve jamais une prescription."""
    proof = [normalized(p) for p in supports if p]
    documentary_absence = lambda p: bool(_ABSENCE.search(p) or re.search(r"aucun texte (?:de la base|disponible)|aucune consigne (?:de la base|disponible)", p))
    if not proof or not all(documentary_absence(p) for p in proof):
        return False
    # Une reprise littérale d'un constat limité au corpus ne le généralise pas.
    if documentary_limit(text) and any(normalized(text).strip().lstrip('-* ') == p.strip().lstrip('-* ') for p in proof):
        return False
    # Vérifier auprès d'un service reste une démarche sûre ; une réserve dans
    # une autre phrase ne sauve pas une conclusion catégorique.
    for sentence in re.split(r'[.;!?]', normalized(text)):
        nonexistent_rule = re.search(r"(?:n'existe|ne existe|n'existent).{0,12}pas.{0,45}(?:regle|consigne|texte|interdiction)|aucune.{0,20}(?:regle|consigne|interdiction).{0,20}n'existe", sentence)
        if (not _CATEGORICAL.search(sentence) and not nonexistent_rule) or _LIMIT.search(sentence):
            continue
        if re.search(r'\b(?:doit|doivent|devez)\s+(?:faire\s+)?(?:verifier|confirmer|consulter|demander)\b', sentence):
            continue
        return True
    return False


def operation_errors(claims, question):
    """Rejeter deux substitutions explicites, sans exiger de verbe dans les réserves."""
    q = normalized(question)
    deleting = bool(re.search(r'supprim|effac|retir', q))
    restoring = bool(re.search(r'restaur|recuper|retabl', q))
    errors = []
    for i, claim in enumerate(claims):
        text = normalized(claim.get('text', ''))
        # Ne viser que des instructions positives, pas une explication de limite.
        positive = not re.search(r"\b(?:ne|pas|aucun|sans|impossible|non)\b|n'", text)
        wrong_action = positive and ((deleting and not restoring and re.search(r'restaur|recuper|retabl', text) and not re.search(r'supprim|effac|retir', text))
                                     or (restoring and not deleting and re.search(r'supprim|effac', text) and not re.search(r'restaur|recuper|retabl', text)))
        wrong_tool = (deleting and 'cyclades' in q and 'ipack' not in q
                      and 'ipack' in text and 'cyclades' not in text and positive
                      and re.search(r'supprim|effac|retir', text))
        if wrong_action or wrong_tool:
            errors.append({'index': i, 'errors': ['opération ou logiciel différent de la demande : conserver l’action et l’outil demandés, ou signaler la limite documentaire']})
    return errors
