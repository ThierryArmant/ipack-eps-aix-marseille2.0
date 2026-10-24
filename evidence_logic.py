"""Contrôles conservateurs de portée et de suffisance des affirmations sourcées.

Ils repèrent des pertes de modalité explicites, pas toute contradiction sémantique.
Aucun sujet métier ni conclusion attendue n'est codé ici.
"""
import re
import unicodedata


def normalized(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.lower())
                   if not unicodedata.combining(c))
    return text.replace('’', "'")


# Une réserve ajoutée après la conclusion ne conditionne pas cette conclusion.
def proposition_head(text):
    return re.split(r'\b(?:mais|car|puisque|cependant|toutefois|pourtant)\b|[.;:]',
                    normalized(text), maxsplit=1)[0]


_UNIVERSAL = re.compile(r'universell|\bpartout\b|dans tous les cas|(?:nationale?|generale?).{0,18}(?:systematique|absolu)|systematiquement|automatiquement')
_RULE_SCOPE = re.compile(r'universell|\bpartout\b|dans tous les cas|systematiquement|\bgeneral(?:e|es|ement)?\b')
_NORMATIVE = re.compile(r'prescri|oblig|requis|necessai|impos|interdi|exig|dispens')


def _limited_rule(text):
    return bool(_RULE_SCOPE.search(text) and _NORMATIVE.search(text)
                and re.search(r'\b(?:pas|aucun|aucune|absence|ne)\b', text))


def _verification_obligation(head):
    # Examiner la première obligation : une vérification ajoutée plus loin
    # ne neutralise pas une prescription ancienne formulée auparavant.
    obligation = re.search(r'\b(?:doit|doivent|devez)\b', head)
    if not obligation:
        return False
    action = head[obligation.end():].strip()
    return bool(re.match(r'(?:faire\s+)?(?:confirmer|verifier)\b|etre\s+(?:confirme|verifie)\w*\b', action))


def _historical_confirmation(text):
    return bool(re.search(r'\banciens?\b|\banciennes?\b|historique', text)
                and re.search(r'actuel\w*.{0,60}confirm|confirm\w*.{0,60}actuel', text))


_NO_NEED = re.compile(
    r"(?:n[' ]est|ne sont|n[' ]a|n[' ]ont).{0,18}(?:pas|aucun).{0,25}(?:necessaire|besoin|requis|obligatoire)|"
    r"(?:pas besoin|aucun besoin|inutile|facultatif|facultative)|"
    r"(?:pouvez|peut|peuvent).{0,15}(?:s[' ]en passer|se passer de)")
_DEPENDS = re.compile(r'depend|selon|a determiner|a apprecier|ne peut.{0,15}(?:confirmer|determiner)|reste a (?:verifier|evaluer|determiner)')
_NO_STANDARD = re.compile(
    r'(?:pas de|aucun|aucune|absence de).{0,65}(?:ratio|taux|minimum|seuil|bareme)|'
    r"(?:n[' ]existe|ne fixe|ne definit|ne prevoit).{0,25}(?:pas|aucun).{0,65}(?:ratio|taux|minimum|seuil|bareme)")
_SUFFICIENT = re.compile(r'\bsuffi(?:t|sent|re|sant|sante|sants|santes)\b|\best conforme\b|\bsont conformes\b')
_UNCERTAIN = re.compile(
    r"(?:impossible|pas possible|ne peut pas|ne permet pas|ne permet.{0,12}pas).{0,35}(?:confirmer|conclure|garantir|determiner|dire)|"
    r"(?:pas|ne).{0,45}automatiquement.{0,30}(?:suffi|necess|oblig)|"
    r"reste a (?:apprecier|verifier|valider|determiner)")
_CONDITIONAL = re.compile(r'\bsi\b|sous reserve|a condition|apres (?:appreciation|validation|verification)|sous (?:le controle|la responsabilite)|selon|(?:valide|confirme|apprecie).{0,25}par')


def conditional_possibility(text):
    """Une possibilité explicitement suspendue à une appréciation n'est pas un constat.

    La réserve doit appartenir à la même phrase et la proposition principale doit
    être modale. « Suffisent, mais vérifier » reste une conclusion catégorique.
    """
    sentence = re.split(r'[.;!?]', normalized(text), maxsplit=1)[0]
    return bool(re.search(r'\b(?:peut|peuvent|pourrait|pourraient)\s+suffire\b', proposition_head(text))
                and re.search(r'\b(?:mais|cependant|toutefois)\b.{0,35}(?:depend|reste a)', sentence)
                and re.search(r'appreciation|validation|evaluation|decision', sentence))


def _objects(text):
    """Seulement pour rapprocher deux propositions ; jamais pour prouver une règle."""
    ignored = set('avoir etre pour dans avec sans mais ceci cela cette doit sont peut peuvent pas aucun aucune besoin necessaire necessite obligation obligatoire requis requise selon depend depends alors vous votre leurs les des une est cas conditions condition'.split())
    return {w[:6] for w in re.findall(r"[a-z]{4,}", normalized(text)) if w not in ignored}


# Marqueur rédactionnel explicite, indépendant du sujet métier.
_BRANCH = re.compile(r'^\s*Branche\s*[—–-]\s*([^:\n]{3,180})\s*:', re.I)
_BRANCH_STOP = set("branche cas pour dans avec sans sous selon les des une est sont ces cette meme cours annee deja soit leur leurs aux lorsque".split())
_BRANCH_RULE = re.compile(r"\b(?:doit|doivent|devez|faut|necessaire|obligatoire|interdit|autorise|possible|peut|peuvent)\b|\bne (?:peut|peuvent|sera|seront)\b")


def _branch_words(text):
    return {w[:6] for w in re.findall(r"[a-z]{4,}", normalized(text)) if w not in _BRANCH_STOP}


def explicit_branch_condition_lost(claim):
    """Signale une prescription qui cite une branche mais en perd le périmètre.

    Contrôle lexical borné aux preuves dont le libellé commence par « Branche — ».
    Les variantes sémantiques ne sont pas prouvées ; une reformulation très éloignée
    peut demander de conserver le libellé explicite. Aucune décision métier codée.
    """
    heads = [proposition_head(part) for part in re.split(r'[.;!?]\s*', claim['text']) if part.strip()]
    normative = [part for part in heads if _BRANCH_RULE.search(part) and not _UNCERTAIN.search(part)]
    if not normative:
        return False
    alternatives = []
    for evidence in claim.get('evidence', []):
        match = _BRANCH.match(evidence.get('quote', ''))
        if match:
            for part in re.split(r'\s+ou\s+', normalized(match.group(1))):
                ordered = [w[:6] for w in re.findall(r'[a-z]{4,}', part) if w not in _BRANCH_STOP]
                if ordered:
                    alternatives.append((set(ordered), ordered if re.search(r'\bavant\b|\bapres\b',part) else []))
    def preserved(text, alternative):
        words, ordered = alternative
        if not words <= _branch_words(text):
            return False
        if not ordered:
            return True
        # Les mots « avant » et « après » présents ailleurs ne réparent pas
        # l'ordre inversé de la condition citée. Aucun calendrier métier ici.
        return bool(re.search(r'\b'+r'\w*\b.*?\b'.join(map(re.escape,ordered))+r'\w*\b',normalized(text)))
    return bool(alternatives) and any(not any(preserved(part, alternative) for alternative in alternatives)
                                      for part in normative)


def non_implication_to_obligation(claim):
    """« X ne constitue pas Y » ne prouve pas que X est obligatoire."""
    head = proposition_head(claim['text'])
    if not re.search(r'\b(?:necessaire|obligatoire|doit|doivent|devez|faut)\b', head):
        return False
    proofs = [normalized(e.get('quote', '')) for e in claim.get('evidence', [])]
    for proof in proofs:
        for sentence in re.split(r'[.;!?]\s*', proof):
            match = re.search(r"(.{5,220}?)\s+(?:ne constitue|ne vaut|n'equivaut).{0,10}pas", sentence)
            if not match:
                continue
            action = _branch_words(match.group(1))
            if len(action & _branch_words(head)) < 2:
                continue
            direct = any(re.search(r'\b(?:necessaire|obligatoire|doit|doivent|devez|faut)\b', other)
                         and len(action & _branch_words(other)) >= 2
                         for source in proofs for other in re.split(r'[.;!?]\s*', source)
                         if not re.search(r"ne constitue|ne vaut|n'equivaut", other))
            if not direct:
                return True
    return False


def optional_action_made_mandatory(claim):
    """Une action explicitement « au besoin » ne devient pas une obligation."""
    head = proposition_head(claim['text'])
    if not re.search(r'\b(?:necessaire|obligatoire|doit|doivent|devez|faut)\b',head):
        return False
    if _CONDITIONAL.search(head) or re.search(r'au besoin|si necessaire|en cas de besoin',head):
        return False
    proofs = [normalized(e.get('quote','')) for e in claim.get('evidence',[])]
    for proof in proofs:
        for action in re.findall(r'\b([a-z]{4,})\s+au besoin\b',proof):
            root = action[:4]
            if not re.search(r'\b'+re.escape(root)+r'[a-z]*\b',head):
                continue
            direct = any('au besoin' not in other and not _CONDITIONAL.search(other)
                         and re.search(r'\b(?:necessaire|obligatoire|doit|doivent|devez|faut)\b',other)
                         and re.search(r'\b'+re.escape(root)+r'[a-z]*\b',other)
                         for source in proofs for other in re.split(r'[.;!?]\s*',source))
            if not direct:
                return True
    return False


def evidence_logic_errors(claims):
    """Ne valide jamais une conclusion : renvoie les pertes explicites détectées."""
    errors = []
    for i, claim in enumerate(claims):
        if optional_action_made_mandatory(claim):
            errors.append({'index': i, 'errors': ['action prévue au besoin transformée en obligation : conserver la condition de nécessité de cette action']})
        if non_implication_to_obligation(claim):
            errors.append({'index': i, 'errors': ['constat de non-équivalence transformé en obligation : la preuve dit que cette action ne vaut pas décision, sans établir que cette action soit obligatoire']})
        if explicit_branch_condition_lost(claim):
            errors.append({'index': i, 'errors': ['condition explicite de la branche citée omise : conserver son périmètre dans la prescription, sans appliquer cette branche à un cas non établi']})
        head = proposition_head(claim['text'])
        proofs = [normalized(e.get('quote', '')) for e in claim.get('evidence', [])]
        historical_pending = any(_historical_confirmation(p) for p in proofs)
        # Chaque phrase est contrôlée : une première vérification ne couvre
        # pas une obligation catégorique ajoutée dans la phrase suivante.
        heads = [proposition_head(sentence) for sentence in re.split(r'[.;!?]\s*', claim['text']) if sentence.strip()]
        if historical_pending and any(
                not _verification_obligation(part)
                and re.search(r'\bdoit\b|\bdoivent\b|\bdevez\b|obligatoire|exig[eé]|\brequis(?:e|es)?\b', part)
                and not re.search(r'selon|d.apres|(?:note|texte|circulaire).{0,40}\b(?:19|20)\d{2}\b|a confirmer|reste a verifier', part)
                for part in heads):
            errors.append({'index': i, 'errors': [
                'prescription ancienne dont les modalités actuelles sont à confirmer : attribuer la prescription à sa source datée et conserver la vérification actuelle, sans en faire une obligation actuelle certaine']})
        if any(re.search(r'\b(?:vous pouvez|est autorise|sont autorises|est possible|sont possibles)\b', part)
                and re.search(r'\bsous (?:certaines )?conditions\b', part)
                and not _CONDITIONAL.search(part) for part in heads):
            errors.append({'index': i, 'errors': [
                'permission assortie de conditions non précisées : énoncer les conditions concrètes dans la conclusion ou conserver le cadre sans autoriser le cas']})
        qualified_negative = bool(_UNIVERSAL.search(head))
        categorical_no_need = bool(_NO_NEED.search(head)) and not qualified_negative and not _CONDITIONAL.search(head) and not _UNCERTAIN.search(head)
        if categorical_no_need and any(_limited_rule(p) for p in proofs):
            # Un autre passage peut explicitement établir une dispense pour ce cas.
            direct = any(_NO_NEED.search(proposition_head(p)) and not _UNIVERSAL.search(proposition_head(p)) and not _UNCERTAIN.search(proposition_head(p))
                         for p in proofs)
            if not direct:
                errors.append({'index': i, 'errors': [
                    'absence de prescription universelle transformée en absence de nécessité dans ce cas : conserver la portée et les faits manquants']})
        if (_SUFFICIENT.search(head) and not _CONDITIONAL.search(head) and not _UNCERTAIN.search(head)
                and not conditional_possibility(claim['text'])
                and any(_NO_STANDARD.search(p) for p in proofs)):
            direct = any(_SUFFICIENT.search(proposition_head(p)) and not _NO_STANDARD.search(p) and not _UNCERTAIN.search(proposition_head(p))
                         for p in proofs)
            if not direct:
                errors.append({'index': i, 'errors': [
                    'suffisance déduite de l’absence de seuil : la validation du cas et son autorité doivent être établies, pas supposées']})
        if categorical_no_need:
            for j, other in enumerate(claims):
                if j == i or not _DEPENDS.search(normalized(other['text'])):
                    continue
                if len(_objects(head) & _objects(other['text'])) >= 2:
                    errors.append({'index': i, 'related_index': j, 'errors': [
                        'conclusion d’absence de nécessité contredite par une appréciation encore conditionnelle sur le même objet']})
                    break
    return errors


def evidence_constraints(packets):
    """Limites explicites des preuves signalées avant rédaction, sans décision métier."""
    constraints = []
    for packet in packets:
        for passage in packet.get('passages', []):
            text = normalized(passage['text'])
            limits = []
            if _limited_rule(text):
                limits.append('absence_de_prescription_universelle_ne_prouve_pas_une_dispense_dans_le_cas')
            if _NO_STANDARD.search(text):
                limits.append('absence_de_seuil_ne_prouve_pas_la_suffisance_du_dispositif')
            if _historical_confirmation(text):
                limits.append('prescription_ancienne_a_attribuer_et_modalites_actuelles_a_confirmer')
            if limits:
                constraints.append({'document_id':packet['id'], 'passage_id':passage['id'], 'limits':limits})
    return constraints
