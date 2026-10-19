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
    def documentary_absence(p):
        # Le silence sur un point ne retire pas une règle explicite dans une
        # autre phrase du même passage. Les simples renvois ne sont pas des règles.
        statements = [part.strip() for part in re.split(r'[.;!?]', p) if part.strip()]
        factual = [part for part in statements if not re.match(
            r"(?:faire|faites|veuillez|verifier|verifiez|consulter|consultez|demander|demandez|contacter|contactez|"
            r"ne pas (?:affirmer|transformer|conclure))\b|(?:sources?|nature de la source|references?)\s*:|https?://", part)]
        return bool(factual) and all(_ABSENCE.search(part) or re.search(
            r"(?:les )?sources.{0,40}ne prevoient pas|aucun texte (?:des sources|de la base|du corpus).{0,25}ne prevoit|"
            r"aucun texte (?:de la base|disponible)|aucune consigne (?:de la base|disponible)", part)
            for part in factual)
    if not proof or not all(documentary_absence(p) for p in proof):
        return False
    # Une reprise littérale d'un constat limité au corpus ne le généralise pas.
    if documentary_limit(text) and any(normalized(text).strip().lstrip('-* ') == p.strip().lstrip('-* ') for p in proof):
        return False
    # Vérifier auprès d'un service reste une démarche sûre ; une réserve dans
    # une autre phrase ne sauve pas une conclusion catégorique.
    for sentence in re.split(r'[.;!?]', normalized(text)):
        nonexistent_rule = re.search(r"(?:n'existe|ne existe|n'existent).{0,12}pas.{0,45}(?:regle|consigne|texte|interdiction|autorisation)|aucune.{0,20}(?:regle|consigne|interdiction).{0,20}n'existe", sentence)
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


def activity_field_errors(claims, *, public=None):
    """Refuse un classement explicitement contraire à la table documentaire.

    Ne statue ni sur un dépôt ni sur la validation d'un ensemble complet.
    """
    if public is not None and not re.search(r'lycee|\bgt\b', normalized(public)):
        return []
    from pathlib import Path
    rows = (Path(__file__).resolve().parent / 'config' / 'activites_champs.csv').read_text().splitlines()
    fields = [(name, int(field)) for line in rows if ';' in line
              for name, field in [line.split(';', 1)] if field.isdigit()]
    errors = []
    for i, claim in enumerate(claims):
        text = normalized(claim.get('text', '')).replace('-', ' ').replace('course de duree', 'course en duree')
        if re.search(r"\bsi\b|lorsque|dans le cas", text):
            continue
        named = [(name, field) for name, field in fields if re.search(r'\b' + re.escape(name) + r'\b', text)]
        if len(named) != 2 or named[0][1] == named[1][1]:
            continue
        denied_distinctness = re.search(r"ne peuvent.{0,45}pas.{0,90}(?:deux epreuves distinctes|deux activites distinctes)", text)
        same_field = re.search(r"(?:relevent (?:bien )?du|appartiennent (?:bien )?au) meme champ", text)
        if denied_distinctness or same_field:
            errors.append({'index': i, 'errors': ['activités explicitement classées dans deux champs différents par la table documentaire : ne pas affirmer qu’elles constituent le même champ ou ne sont pas distinctes']})
    return errors


def workflow_fidelity_errors(claims, question):
    """Préserver les opérations/préalables explicitement cités, sans créer de règle."""
    q = normalized(question)
    combined = normalized(' '.join(c.get('text', '') for c in claims))
    errors = []
    for i, c in enumerate(claims):
        text = normalized(c.get('text', ''))
        proof = normalized(' '.join(e.get('quote', '') for e in c.get('evidence', [])))
        bounded = bool(re.search(r"(?:ne|n').{0,45}(?:permet|precise|documente|confirme|fixe|indique|etablit).{0,20}pas|(?:pas|non) document|a verifier|reste a confirmer", text))
        if (re.search(r'rapport|accident', q) and re.search(r'etabl\w*.{0,65}48', proof)
                and not re.search(r'(?:transm|envoy|adress)\w*.{0,55}48', proof)
                and not bounded
                and (re.search(r'delai.{0,35}(?:transmission|envoi)', text)
                     or re.search(r'(?:transm|envoy|adress)\w*.{0,65}48', text))
                and re.search(r'48', text)):
            errors.append({'index':i, 'errors':['le délai cité porte sur l’établissement du rapport, pas sur un délai exact de transmission ; conserver cette opération et signaler la limite']})
        if (re.search(r'protocole.{0,40}(?:dnb|brevet)', text)
                and not re.search(r'\bdnb\b|brevet|college', proof)):
            errors.append({'index':i, 'errors':['une fiche générique ne justifie pas un protocole DNB ; utiliser le passage qui précise le circuit collège']})
        if (re.search(r'equipement|gymnase|installation', q)
                and re.search(r'(?:forcer|forcee).{0,30}synchro|synchro\w*.{0,30}(?:forcer|forcee)', text)
                and not bounded and (not re.search(r'(?:cliquer|bouton|commande).{0,40}synchro', proof)
                                     or re.search(r'ne documente pas|pas de commande|aucune commande|sans commande', proof))):
            errors.append({'index':i, 'errors':['modifier un libellé ne prouve pas une commande de synchronisation forcée : conserver l’action documentée']})
        if (re.search(r'export|import', q) and 'cyclades' in q
                and re.search(r'apres l.import des candidats dans cyclades', proof)
                and re.search(r'export|generer un fichier|importe directement', text)
                and not bounded and not re.search(r'(?:candidats?|eleves?).{0,65}(?:import|present|figur|charg|enregistr)|(?:import|charg|enregistr)\w*.{0,50}(?:candidats?|eleves?)|cyclades.{0,30}(?:contien|contenir).{0,30}(?:candidats?|eleves?)', combined)):
            errors.append({'index':i, 'errors':['l’import préalable des candidats par le rectorat fait partie des préalables cités ; le conserver avec la validation des protocoles']})
        if (re.search(r'import|organis', q) and re.search(r'restreint|organis|ordre|configur', q)
                and 'organisation des classes' in proof and 'importation des eleves' in proof
                and c.get('section') == 'etape' and re.search(r'configur', text)
                and re.search(r'import', text) and not re.search(r'\borganisation\b', combined)):
            errors.append({'index':i, 'errors':['le parcours cité passe par Organisation des Classes avant l’import ; conserver cette étape pour attribuer le professeur']})
    return errors
