"""Contrôles ciblés de restitution ; aucune nouvelle décision réglementaire."""
import re
if __package__:
    from .evidence_logic import normalized
else:
    from evidence_logic import normalized

_ABSENCE = re.compile(r"(?:aucun\w*|pas de|absence de).{0,90}(?:consigne|texte|regle|procedure|documentation).{0,60}(?:(?:re)?trouv|disponible|etabli)|(?:consigne|texte|regle|procedure).{0,60}(?:non (?:re)?trouve|non etabli)|\ba verifier\b|ne .{0,35}(?:demontre\w*|etabli\w*|prouve\w*).{0,12}pas (?:la possibilite|que)|possibilite.{0,80}n.a pas ete (?:releve\w*|confirme\w*|verifie\w*)|faire verifier (?:ce|le) point")
_CATEGORICAL = re.compile(r"\b(?:interdit\w*|obligatoire\w*|autorise\w*|impossible|devez|doit|doivent|ne (?:peut|peuvent).{0,20}pas|n.est.{0,15}pas (?:permis|autorise|possible))\b")
_LIMIT = re.compile(r"(?:ne|n').{0,55}(?:peut|permet|permettent).{0,20}pas.{0,35}(?:confirmer|affirmer|conclure|etablir)|(?:pas|aucun\w*).{0,65}(?:consigne|texte|regle|procedure).{0,60}(?:(?:re)?trouv|etabli)|reste a (?:verifier|confirmer)|a faire confirmer|n.est pas possible de (?:confirmer|affirmer|conclure|etablir)")


def documentary_limit(text):
    """Constat de recherche borné au corpus, jamais une inexistence de règle."""
    value = normalized(text)
    if re.search(r"n'existe|n'existent|reponse directe|ne pas repondre|pour les (?:questions|situations)", value):
        return False
    return bool(re.search(r"aucun texte de la base|aucune consigne de la base|(?:aucun\w*|pas de|absence de).{0,75}(?:consigne|texte|regle|procedure).{0,65}(?:(?:re)?trouv|dans (?:la base|le corpus|la documentation))", value)
                or re.search(r"(?:passages|sources|documents|description).{0,100}ne (?:suffit|permet|permettent) pas.{0,30}confirmer.{0,30}(?:possibilite|obligation|autorisation|interdiction)", value))


def mixed_documentary_limit_conflict(text, supports):
    """Une règle voisine dans la preuve ne lève pas une limite sur un autre objet.

    Contrôle lexical borné, pas une preuve d'implication sémantique générale.
    Les règles explicitement prescriptives sur le même objet restent recevables.
    """
    stop = {'cett', 'ceci', 'cela', 'doit', 'doiv', 'faut', 'avec', 'dans', 'pour',
            'obli', 'auto', 'inte', 'poss', 'impo', 'nati', 'regl', 'text', 'pass',
            'comm', 'form', 'cons', 'chaq', 'tout', 'plus', 'etre', 'sont', 'sera'}
    def roots(value):
        return {w[:4] for w in re.findall(r"[a-z]{4,}", value) if w[:4] not in stop}
    limit = re.compile(r"(?:ne |n.).{0,35}(?:suffit|permet).{0,20}pas.{0,35}(?:demontrer|etablir|confirmer).{0,30}"
                       r"(?:obligation|autorisation|interdiction|possibilite)\s+(.*)")
    statements = [part.strip() for proof in supports for part in re.split(r'[.;!?]', normalized(proof)) if part.strip()]
    objects = [roots(match.group(1)) for part in statements if (match := limit.search(part))]
    # Une réserve porte sur sa proposition, pas sur une conclusion voisine.
    # « ne signifie pas que X est obligatoire » nie une déduction, pas X.
    clauses = re.split(r'[.;!?]|,\s*|\b(?:mais|cependant|toutefois|pourtant|donc|en revanche)\b', normalized(text))
    for clause in clauses:
        non_entailment = re.search(
            r"\bne\s+(?:signifie|veut dire|implique|demontre|prouve)\s+pas\s+(?:necessairement\s+)?qu[ei']", clause)
        if non_entailment:
            continue
        # Faire vérifier un point n'affirme pas que l'action métier est autorisée.
        # Forme passive bornée : une seconde prescription reste contrôlée.
        if re.fullmatch(r"[^;.!?]{1,220}\b(?:doit|doivent)\s+etre\s+(?:verifie|confirme|precise)(?:e|es|s)?"
                        r"(?:\s+(?:aupres de|par) [^;.!?]+)?\s*", clause):
            continue
        if not _CATEGORICAL.search(clause) or re.search(r"ne.{0,40}pas.{0,25}(?:prouver|demontrer|etablir|confirmer|conclure)|non (?:demontre|etabli|confirme)", clause):
            continue
        claim_roots = roots(clause)
        for target in objects:
            shared = target & claim_roots
            if len(shared) < 2:
                continue
            explicit = any(_CATEGORICAL.search(part) and not limit.search(part)
                           and not _ABSENCE.search(part) and not _LIMIT.search(part)
                           and len(roots(part) & shared) >= 2 for part in statements)
            if not explicit:
                return True
    return False


def unsupported_certainty(text, supports):
    """Le silence documentaire seul ne prouve jamais une prescription."""
    if mixed_documentary_limit_conflict(text, supports):
        return True
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
        # Une obligation de vérifier n'est pas une obligation métier. Retirer
        # seulement ces verbes du test, sans masquer une interdiction voisine.
        categorical_sentence = re.sub(r"\b(?:doit|doivent) etre (?:verifie\w*|confirme\w*)\b", '', sentence)
        if (not _CATEGORICAL.search(categorical_sentence) and not nonexistent_rule) or _LIMIT.search(sentence):
            continue
        if re.search(r'\b(?:doit|doivent|devez)\s+(?:faire\s+)?(?:verifier|confirmer|consulter|demander)\b', sentence):
            continue
        return True
    return False


def unrelated_retrospective_limit(claim, question):
    """Écarter un seul constat de connaissance sur une saisie rétrospective.

    Aucun droit, condition d'accès, délai, archivage ou règle de conservation
    ne doit être retiré. Une demande portant sur l'historique conserve la réserve.
    """
    if claim.get('section') != 'limite':
        return False
    q = normalized(question)
    if re.search(r"n[ −–-]1|precedent|anterieur|retrospect|histori|archiv|ancien|dernier|passe|il y a|conserv|\b20\d{2}\b", q):
        return False
    text = normalized(claim.get('text', ''))
    parts = [part.strip() for part in re.split(r'[.!?;]', text) if part.strip()]
    if not parts:
        return False
    # Le constat doit viser explicitement une opération passée non confirmée,
    # et ne porter aucune autre prescription que faire vérifier cette possibilité.
    first = parts[0]
    retrospective = re.search(r"retrospect|annee (?:precedente|anterieure)|n[ −–-]1", first)
    absence = re.fullmatch(
        r"(?:la possibilite de|les passages ne permettent pas de confirmer la possibilite de) "
        r"(?:saisir|renseigner|modifier|completer).{1,500}", first)
    if not retrospective or not absence:
        return False
    if not (re.search(r"n.est pas confirmee|n.a pas ete confirmee|reste non confirmee", first)
            or first.startswith('les passages ne permettent pas de confirmer')):
        return False
    if re.search(r"interdit|autorise|obligatoire|uniquement|seulement|doit|doivent|ne peut|delai|conserv", first):
        return False
    return all(re.fullmatch(
        r"(?:cette verification doit etre faite(?: separement)?|"
        r"il est recommande de verifier ce point(?: aupres du .{1,100})?)", part)
        for part in parts[1:])


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


# Familles d'opérations : rapprochements de vocabulaire, aucune réponse métier.
_ACTION_FAMILIES = (
    r'accept|admett|admis|admission|accueill',
    r'export|import|transfert|televers',
    r'evaluation differee|epreuve differee|rattrapage',
    r'evaluation ponctuelle|epreuve ponctuelle|examen ponctuel|ponctuel de remplacement',
)


def evidence_relation_errors(claims, question):
    """Contrôler des transferts explicites de prédicat et de condition.

    Ne prouve pas l'implication sémantique générale : aucun fait nouveau produit.
    Une réserve d'incertitude reste possible quand le prédicat n'est pas documenté.
    """
    errors = []
    for i, claim in enumerate(claims):
        text = normalized(claim.get('text', ''))
        proof = normalized(' '.join(e.get('quote', '') for e in claim.get('evidence', [])))
        if not proof:
            continue
        # Deux inversions explicites ; aucun choix réglementaire n'est produit.
        # Le recoupement du sujet évite de transférer une anomalie voisine.
        stop = {'normal', 'normale', 'cette', 'celui', 'comme', 'dans', 'pour', 'avec', 'sont', 'mais', 'peut', 'doit'}
        roots = lambda value: {w[:5] for w in re.findall(r"[a-z]{4,}", value) if w not in stop}
        negative_normal = r"\banormal(?:e|es|s)?\b|(?:ne\s+\w+|n.est)\s+pas(?:\s+\w+){0,5}\s+normal(?:e|es|s)?\b"
        for clause in re.split(r'[.;!?]', text):
            head = re.split(r'\bcar\b|parce que|puisque', clause, maxsplit=1)[0]
            if (re.search(r"\b(?:il est|c.est) normal(?:e)?\b", head)
                    and not re.search(r"\bne\b.{0,45}\bpas\b|\bn[’']", head)
                    and any(re.search(negative_normal, part) and len(roots(head) & roots(part)) >= 2
                            for part in re.split(r'[.;!?]', proof))):
                errors.append({'index': i, 'errors': ['conclusion normale opposée à une anomalie explicite dans sa preuve : conserver le sens négatif du passage cité']})
        for exclusion in re.finditer(r"\bne s.applique(?:nt)? pas (?:a|au|aux)\s+([^.;!?]+)", text):
            target = roots(exclusion.group(1))
            if (target and not target & roots(proof)
                    and not re.search(r'uniquement|seulement|exclusivement|reserve.{0,20}a', proof)):
                errors.append({'index': i, 'errors': ['exclusion d’un cas absent de la preuve sans restriction explicite : une liste d’exemples ne prouve pas cette exclusion']})
        bounded = bool(re.search(r"(?:sources|passages|documents|documentation).{0,40}ne.{0,30}pas|"
                                 r"ne.{0,25}pas.{0,15}confirmer|pas (?:possible de confirmer|documente)|non confirme|reste a verifier", text))
        if bounded:
            continue
        q = normalized(question)
        # Une affectation à un protocole ne constitue pas une inscription.
        for clause in re.split(r'[.;!?]', text):
            if (re.search(r"(?:apparait|apparaitre|present|presence|figur\w*).{0,20}(?:dans |sur )?cyclades", clause)
                    and re.search(r"(?:doit|faut|necessaire|condition|pour qu|pour apparaitre)", clause)
                    and re.search(r"assoc\w*|affect\w*", clause)
                    and re.search(r"protocole", clause)
                    and not re.search(r"ne .{0,40}pas|n.est pas|ne suffit pas|pas necessaire", clause)):
                errors.append({'index': i, 'errors': ['ne pas confondre inscription dans Cyclades et association à un protocole : une procédure pour un candidat déjà inscrit ne justifie pas cette condition de présence']})
        optional = r'\boption\b|optionnel|option eps|eps option|facultati'
        scoped_proof = re.sub(r"en complement de l.epreuve obligatoire(?: ponctuelle)?", '', proof)
        if (re.search(r'ponctuel|epreuve obligatoire', q) and not re.search(optional, q)
                and re.search(r'optionnel|enseignement option|option eps|eps option|facultati', scoped_proof) and not re.search(r'obligatoire|enseignement commun', scoped_proof)
                and not re.search(optional, text)):
            errors.append({'index': i, 'errors': ['une preuve limitée à l’option ne justifie pas une règle de l’épreuve obligatoire : retrouver le passage du régime demandé']})
        single = r'\bdi(?:\s*\+\s*|\s+)di\b|note unique|une seule (?:note|epreuve|evaluation)|une (?:note|epreuve) sur trois'
        if (re.search(r'inapt', q) and re.search(r'sais|declar|enregistr', q)
                and not re.search(single + r'|moyenne|calcul|deux notes|deux epreuves', q)
                and re.search(r'note unique|une seule note', text)
                and not re.search(r'(?:\bsi\b|lorsque|dans le cas).{0,100}(?:une seule note|note unique|deux.{0,40}(?:imposs|inapt|di))', text)):
            errors.append({'index': i, 'errors': ['le nombre de notes déjà obtenues n’est pas établi par la demande : ne pas appliquer le cas de note unique sans condition']})
        # Un qualificatif constitutif d'un droit doit être étayé, pas déduit du
        # thème commun de la preuve (par ex. une indemnité quelconque).
        if re.search(r'\bprotege\w*\b', text) and not re.search(r'\bprotege\w*\b|protection|garanti', proof):
            errors.append({'index': i, 'errors': ['garantie ou protection affirmée sans passage qui l’établit : conserver seulement le droit et les conditions effectivement documentés']})
        # Toute décision sur l'admission doit porter sur ce prédicat : le
        # contrôle vaut aussi pour la reformulation de la réparation et pour
        # une permission inventée, pas seulement pour un « non » littéral.
        admission = bool(re.search(r'(?:accept\w*|admett\w*|accueill\w*) (?:un |le |ce |les |des |ces )?(?:candidat|eleve)', text)
                         or re.search(r'(?:candidat|eleve).{0,90}(?:etre|est|sera|sont|seront) (?:accept|admis|accueill)', text)
                         or (re.search(r'candidat|eleve', q) and re.search(r'admission', text))
                         or (re.search(r'candidat|eleve', q) and not re.search(r'certificat|justificatif|fichier|lot|protocole', text)))
        for action in _ACTION_FAMILIES[:1]:
            # La modalité doit qualifier l'action dans la même proposition.
            # « Vérifier avant de décider » ne décide pas d'une admission.
            # Examiner aussi la proposition suivante pour ne pas laisser une
            # permission/refus passer après une introduction de vérification.
            heads = [re.split(r"\bavant (?:de\b|d[' ])", clause, maxsplit=1)[0]
                     for clause in re.split(r'[.;!?,]', text)]
            unsupported = any(re.search(action, head) and re.search(
                r'\b(?:peut|peuvent|doit|doivent|devez|non)\b|possible|impossible|interdit|autorise|refus|(?:ne|n.).{0,45}pas', head)
                for head in heads)
            if admission and unsupported and not re.search(action, proof):
                errors.append({'index': i, 'errors': ['le passage cité ne justifie pas cette décision sur une autre opération : autorisation et refus doivent être documentés, sinon conserver les vérifications établies']})
        # Une condition d'une branche ne restreint pas une autre alternative.
        exclusive = re.search(r'uniquement si|seulement si|sauf(?: dans| en)?', text)
        if exclusive:
            for action in _ACTION_FAMILIES[2:]:
                head = text[:exclusive.start()]
                if not re.search(action, head):
                    continue
                branches = re.split(r'\bsoit\b|(?<=[.;])\s+', proof)
                matching = [b for b in branches if re.search(action, b)]
                other = ' '.join(b for b in branches if not re.search(action, b))
                tail = text[exclusive.end():]
                # Un fait d'évaluation antérieure et une cause de différé sont
                # des conditions distinctes, pas des synonymes.
                for condition, marker in ((r'notes?.{0,30}(?:deja|obten|acquis)|(?:deja|obten|acquis).{0,30}notes?', r'\bnotes?\b'), (r'force majeure', r'force majeure')):
                    if (matching and re.search(condition, tail) and re.search(marker, other)
                            and not any(re.search(marker, b) for b in matching)):
                        errors.append({'index': i, 'errors': ['condition empruntée à une autre branche du passage : conserver les alternatives sans ajouter de préalable ni d’exception à l’opération demandée']})
        # Un périmètre logiciel négatif doit nommer l'objet qu'il exclut. Les
        # synonymes de notes/bulletins ne démontrent pas le périmètre d'un référentiel.
        if (re.search(r'curseur', text) and re.search(r'ne.{0,45}pas.{0,20}ger|ne.{0,35}gere|pas.{0,25}gere', text)
                and not re.search(r'curseur', proof)):
            errors.append({'index': i, 'errors': ['le passage cité ne documente pas cet objet logiciel : ne pas déduire son absence du périmètre d’un autre objet']})
    return errors
