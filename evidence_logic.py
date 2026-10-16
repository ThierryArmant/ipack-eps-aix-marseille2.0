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
_RULE_SCOPE = re.compile(r'universell|\bpartout\b|dans tous les cas|systematiquement')
_NORMATIVE = re.compile(r'prescri|oblig|requis|necessai|impos|interdi|exig|dispens')


def _limited_rule(text):
    return bool(_RULE_SCOPE.search(text) and _NORMATIVE.search(text)
                and re.search(r'\b(?:pas|aucun|aucune|absence|ne)\b', text))


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


def _objects(text):
    """Seulement pour rapprocher deux propositions ; jamais pour prouver une règle."""
    ignored = set('avoir etre pour dans avec sans mais ceci cela cette doit sont peut peuvent pas aucun aucune besoin necessaire necessite obligation obligatoire requis requise selon depend depends alors vous votre leurs les des une est cas conditions condition'.split())
    return {w[:6] for w in re.findall(r"[a-z]{4,}", normalized(text)) if w not in ignored}


def evidence_logic_errors(claims):
    """Ne valide jamais une conclusion : renvoie les pertes explicites détectées."""
    errors = []
    for i, claim in enumerate(claims):
        head = proposition_head(claim['text'])
        proofs = [normalized(e.get('quote', '')) for e in claim.get('evidence', [])]
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
            if limits:
                constraints.append({'document_id':packet['id'], 'passage_id':passage['id'], 'limits':limits})
    return constraints
