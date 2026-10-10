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
    match = re.search(r'\[PORTEE: ([a-z,]+)\]', text)
    declared = (metadata or {}).get('examens') or []
    scopes = set(declared) if declared else (set(match.group(1).split(',')) if match else set())
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
    medical = bool(re.search(r'inapt|dispens|certificat medical', q))
    decision = bool(re.search(r'\b(di|disp|zero|0)\b|sais|notes?|ccf|epreuv', q))
    exam = bool(re.search(r'\b(cap|dnb|brevet|college|lgt|gt)\b|bac(calaureat)?\s+(pro|professionnel|general|technologique)', q))
    if public == 'Lycée Pro / CAP' and decision and not exam:
        return ('Précisez le diplôme concerné : CAP ou baccalauréat professionnel, ainsi que la session. '
                'Ces deux examens n\'ont pas les mêmes modalités. Aucun code de saisie ne peut être choisi à ce stade.')
    medical_type = bool(re.search(r'partiel|total', q))
    medical_period = bool(re.search(r'temporaire|permanent|toute l.annee|'
                                    r'\bdu\s+\d|\bjusqu|\bpendant\s+\d|\bpour\s+\d', q))
    if medical and decision and not (medical_type and medical_period):
        return ('Pour décider d\'une note ou d\'un statut, précisez si l\'inaptitude est totale ou partielle, '
                'sa période de validité, les évaluations déjà réalisées et la possibilité d\'une épreuve adaptée ou différée. '
                'Le mot « dispensé » seul ne permet pas de choisir entre zéro, DI et une dispense d\'épreuve.')
    return ''


def reference_notice(targets, question=None):
    entries = catalog()
    result = []
    for path, md in entries.items():
        if not md.get('prioritaire') or (md.get('examens') and not set(md['examens']) & set(targets)):
            continue
        if question is not None:
            q = normalise(question)
            if not any(re.search(m, q) for m in md.get('motifs', [])):
                continue
            if any(re.search(m, q) for m in md.get('exclure_motifs', [])):
                continue
        result.append((path, md))
    return result
