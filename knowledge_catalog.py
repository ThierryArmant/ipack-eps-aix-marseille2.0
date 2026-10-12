"""Catalogue documentaire local : aucune dépendance réseau ni appel d'API."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path


def normalise(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


def active_paths(folder):
    """Parcours stable, récursif, sans les archives conservées pour traçabilité."""
    root = Path(folder)
    return sorted(p for p in root.rglob('*.txt')
                  if not {'archives', 'archive', 'a_verifier'} & set(p.parts))


def fingerprint():
    digest = hashlib.sha256()
    for folder in ('data', 'config'):
        for p in sorted(Path(folder).rglob('*')):
            if p.is_file() and p.suffix in ('.txt', '.json', '.csv'):
                digest.update(str(p).encode())
                digest.update(p.read_bytes())
    return digest.hexdigest()


def catalog():
    path = Path('config/catalogue_documents.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def document_records(folder):
    entries, seen = catalog(), set()
    paths = active_paths(folder)
    if folder in ('data/ipack', 'data/examens', 'data/textes'):
        paths += active_paths('data/commun')
    for p in paths:
        content = p.read_text(encoding='utf-8')
        signature = hashlib.sha256(content.encode()).hexdigest()
        if signature in seen:
            continue
        seen.add(signature)
        metadata = dict(entries.get(p.as_posix(), {}))
        metadata.update(source=p.name, path=p.as_posix())
        metadata.setdefault('statut', 'synthese_non_revalidee')
        yield content, metadata


def incompatible(text, targets, metadata=None):
    """Filtre uniquement les portées explicitement déclarées ; pas d'inférence sur un mot isolé."""
    match = re.search(r'\[PORTEE:\s*([a-z,\s]+)\]', text)
    declared = (metadata or {}).get('examens') or []
    scopes = set(declared) if declared else ({s.strip() for s in match.group(1).split(',')} if match else set())
    return bool(targets and scopes and not scopes & set(targets))


def passage_key(text):
    """Deux passages différents ne deviennent pas doublons par leur introduction."""
    return hashlib.sha256(re.sub(r'\s+', ' ', text).strip().encode()).hexdigest()


def obsolete_reference(text):
    """Ces références ne justifient plus une réponse pour la session courante."""
    q = normalise(text)
    if 'mene2517122c' in q or 'mene2505383c' in q:
        return False  # une fiche actuelle peut expliquer quel texte elle remplace
    return bool(re.search(r'mene2037057c|mene2018678c|circulaire (du )?29 decembre 2020|'
                          r'circulaire (du )?17 juillet 2020', q))


def section_scopes(title):
    q = normalise(title)
    scopes = set()
    if re.search(r'bac(calaureat)? ?(general|gt|technologique)|lycee gt', q):
        scopes.add('gt')
    if re.search(r'bac(calaureat)? ?(pro|professionnel)|lycee pro|\bbma\b', q):
        scopes.add('pro')
    if re.search(r'\bcap\b', q):
        scopes.add('cap')
    if re.search(r'\bdnb\b|\bbrevet\b', q):
        scopes.add('dnb')
    return sorted(scopes)


def clarification(question, public):
    q = normalise(question)
    # Les conditions médicales restent nécessaires pour choisir une valeur
    # individuelle, pas pour expliquer un circuit logiciel ou les possibilités.
    if re.search(r'dispens.{0,20}epreuve.{0,15}eps|\baflp\d?\b|'
                 r'ccf.{0,40}(?:mercredi|emploi du temps)|'
                 r'(?:transform|modifi|corrig).{0,25}(?:note|dispense)|'
                 r'note.{0,30}transform|dispens.{0,25}deux activites', q):
        return ''
    individual_value = bool(re.search(
        r'\b(?:di|disp|ab|abs|zero|0)\b(?! (?:candidat|eleve|lot))|je (?:mets|dois mettre)|'
        r'(?:quelle|quel|comment).{0,25}(?:note|code|statut).{0,25}(?:mettre|saisir|choisir)', q))
    # Une question sur le certificat lui-même (arrivé en retard, rétroactif, valable, modèle) ne porte pas
    # sur le choix d'une note : la demande de précisions médicales la détournait (audit en ligne, D8).
    certificate_question = bool(re.search(
        r'certificat.{0,80}(?:arriv|retard|tardi|apres|retroacti|antidat|valable|valide|accept|recevable|'
        r'conforme|modele|date|delai)|(?:retroacti|antidat|en retard).{0,60}certificat', q))
    if certificate_question and not individual_value:
        return ''
    procedure = bool(re.search(
        r'santorin|cyclades|protocole|lot|reinitialis|reaffect|'
        r'qui.{0,35}(?:choisi|decid|valid|coch)|cfa|apprenti|'
        r'(?:epreuve|evaluation).{0,20}adapt|'
        r'adapt.{0,25}(?:epreuve|evaluation)|dispens.{0,25}epreuve', q))
    if procedure and not individual_value:
        return ''
    # General procedures do not choose a medical status or an individual grade.
    asks_code = bool(re.search(r'\b(di|disp|ab|zero|0)\b|je (mets|dois mettre)|je saisis', q))
    general_procedure = bool(re.search(
        r'quel.*certificat|qui.*(?:valide|decide|declare)|comment.*(?:declarer|enregistrer)|'
        r'inscri.*(?:inapt|apte)|inapt.*inscri|formation continue|'
        r'difference.*(?:ccf|ponctuel)|amenag.*(?:delai|recours)|'
        r'(?:delai|recours).*amenag', q))
    if general_procedure and not asks_code:
        return ''
    medical = bool(re.search(r'inapt|dispens|certificat medical', q))
    decision = bool(re.search(r'\b(di|disp|zero|0)\b|sais|notes?|ccf|epreuv', q))
    exam = bool(re.search(r'\b(cap|dnb|brevet|college|lgt|gt)\b|bac(calaureat)?\s+(pro|professionnel|general|technologique)', q))
    # Le choix CAP / bac pro ne change que les décisions individuelles ou médicales ;
    # une question d'outil (export, import, absences, tablette) reçoit les deux réponses.
    if public == 'Lycée Pro / CAP' and decision and not exam and (medical or individual_value):
        return ('Précisez le diplôme concerné : CAP ou baccalauréat professionnel, ainsi que la session. '
                'Ces deux examens n\'ont pas les mêmes modalités. Aucun code de saisie ne peut être choisi à ce stade.')
    general_information = bool(re.search(
        r'comment est calcul|quel certificat|quels? certificats|comment declarer|comment enregistrer|'
        r'qui (le )?valide|quelle (est la )?note finale|(?:on|doit.on|peut.on) fai(?:t|re) la moyenne|'
        r'comment calculer|quel calcul|coefficient|comment fonctionne.*(?:inapt|dispens)', q))
    if general_information and not re.search(r'\b(di|disp|ab|zero|0)\b|\bsais|je (mets|dois mettre)', q):
        return ''
    medical_type = bool(re.search(r'partiel|total', q))
    medical_period = bool(re.search(r'temporaire|permanent|toute l.annee|'
                                    r'\bdu\s+\d|\bjusqu|\bpendant\s+\d|\bpour\s+\d', q))
    if medical and decision and not (medical_type and medical_period):
        return ('Pour décider d\'une note ou d\'un statut, précisez si l\'inaptitude est totale ou partielle, '
                'sa période de validité, les évaluations déjà réalisées et la possibilité d\'une épreuve adaptée ou différée. '
                'Le mot « dispensé » seul ne permet pas de choisir entre zéro, DI et une dispense d\'épreuve.')
    return ''


# Le niveau choisi compte comme un mot de la question pour les exclusions de fiche :
# une fiche collège qui exclut « lycee » ne doit pas répondre à un professeur de lycée.
_LEVEL_WORD = {'Collège (DNB)': 'college', 'Lycée Général & Techno': 'lycee',
               'Lycée Pro / CAP': 'lycee', '1er degré': 'ecole primaire'}


def reference_notice(targets, question=None, public=None):
    entries = catalog()
    result = []
    level = _LEVEL_WORD.get(public, '')
    for path, md in entries.items():
        if not md.get('prioritaire') or (md.get('examens') and not set(md['examens']) & set(targets)):
            continue
        if question is not None:
            q = normalise(question)
            years = set(re.findall(r'\b20\d{2}\b', q))
            if years and md.get('sessions') and not years & set(md['sessions']):
                continue
            if not any(re.search(m, q) for m in md.get('motifs', [])):
                continue
            if any(re.search(m, q) or (level and re.search(m, level)) for m in md.get('exclure_motifs', [])):
                continue
        result.append((path, md))
    # Une fiche de situation doit précéder une synthèse générale : dix passages
    # sont transmis au maximum et une fiche exclusive peut interrompre la recherche.
    return sorted(result, key=lambda item: -item[1].get('priorite', 0))


def documented_response(question, public, mode):
    """Réponse relue et ciblée du catalogue, sans réécriture par le modèle."""
    q = normalise(question)
    targets = set()
    if re.search(r'bac(?:calaureat)?\s+(?:pro|professionnel)', q):
        targets.add('pro')
    if re.search(r'\bcap\b', q):
        targets.add('cap')
    if re.search(r'bac(?:calaureat)?\s+(?:general|gt|technologique)', q):
        targets.add('gt')
    if re.search(r'\bdnb\b|\bbrevet\b', q):
        targets.add('dnb')
    if not targets:
        targets = {'Collège (DNB)': {'dnb'}, 'Lycée Général & Techno': {'gt'},
                   'Lycée Pro / CAP': {'pro', 'cap'}}.get(public, set())
    for path, md in reference_notice(targets, question, public):
        if md.get('modes') and mode not in md['modes']:
            continue
        if not Path(path).is_file():
            continue
        responses = md.get('reponses_directes', []) + [{
            'motifs': md.get('reponse_directe_motifs', []),
            'reponse': md.get('reponse_directe', '')}]
        for response in responses:
            if response.get('reponse') and any(re.search(m, q) for m in response.get('motifs', [])):
                return response['reponse'], md
    return '', {}


def effective_context(question, public, mode):
    """Les diplômes explicites priment ; un protocole seul reste ambigu."""
    q = normalise(question)
    pro = bool(re.search(r"\bbac(?:calaureat)?\s+(?:pro|professionnel)|\bcap\b", q))
    gt = bool(re.search(r"\bbac(?:calaureat)?\s+(?:gt|general|technologique)|\b(?:seconde|premiere|terminale)\b", q))
    college = bool(re.search(r"\bdnb\b|\bbrevet\b|\bcollege\b|"
                             r"(?:eleves?|classes?|mes|nos|les|de|en) (?:sixiemes?|cinquiemes?|quatriemes?|troisiemes?|6e|5e|4e|3e)\b", q))
    if sum((pro, gt, college)) == 1:
        public = 'Lycée Pro / CAP' if pro else 'Lycée Général & Techno' if gt else 'Collège (DNB)'
    # Une question sur iPackEPS lui-même (version, interfaçage) reste dans iPackEPS même si elle cite Cyclades.
    if mode == 'ipack' and re.search(r"\bcyclades\b|\bsantorin\b", q) and not re.search(r"\bipack", q):
        mode = 'examens'
    return public, mode
