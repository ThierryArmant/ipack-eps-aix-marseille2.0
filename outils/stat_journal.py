"""Statistique de couverture du journal des questions (export du Google Sheet) — sans aucun appel IA.

Usage : python3 outils/stat_journal.py export.csv|export.xlsx [dossier_sortie] [taille_echantillon]
Sorties (à garder HORS du dépôt : les questions peuvent contenir des noms) :
  - couverture.md : répartition par onglet et par public (guide, demande de précision, réponse documentée,
    fiche ciblée, recherche générale sans fiche), fiches les plus sollicitées, sujets sans fiche les plus fréquents ;
  - sans_fiche.csv : questions qui partent en recherche générale, à regrouper en nouvelles fiches ;
  - echantillon_a_noter.csv : tirage stratifié (graine fixe) pour la notation correct / partiel / faux.
"""
import csv, json, random, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import os
os.chdir(ROOT)
import knowledge_catalog as kc
from guide_request import requests_guide, vague_request_opens_guide

PUBLICS = {'college': 'Collège (DNB)', 'collège': 'Collège (DNB)', 'dnb': 'Collège (DNB)',
           'general': 'Lycée Général & Techno', 'générale': 'Lycée Général & Techno', 'gt': 'Lycée Général & Techno',
           'pro': 'Lycée Pro / CAP', 'cap': 'Lycée Pro / CAP', 'professionnel': 'Lycée Pro / CAP',
           '1er': '1er degré', 'primaire': '1er degré', 'ecole': '1er degré', 'école': '1er degré'}
STOP = set("""a au aux avec ce ces comment dans de des du elle en est et il je la le les leur mais me mes mon ne on ou par pas
pour qu que qui sa se ses si son sur ta te tes ton tu un une vous nous y d l j n s c qu est-ce faut faire peut
peux dois doit bonjour merci svp quand quel quelle quels quelles avoir etre été être ai as a ont sont plus tout tous""".split())


def norm(t):
    t = unicodedata.normalize('NFD', str(t or '').lower())
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn')


def read_rows(path):
    path = Path(path)
    if path.suffix.lower() in ('.xlsx', '.xlsm'):
        import openpyxl
        ws = openpyxl.load_workbook(path, read_only=True, data_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        head = [str(h or '').strip() for h in rows[0]]
        return [dict(zip(head, r)) for r in rows[1:]]
    text = path.read_text(encoding='utf-8-sig')
    dialect = csv.Sniffer().sniff(text[:4000], delimiters=',;\t')
    return list(csv.DictReader(text.splitlines(), dialect=dialect))


def column(row, *names):
    for k, v in row.items():
        if k and any(n in norm(k) for n in names):
            return '' if v is None else str(v)
    return ''


def mode_of(value):
    v = norm(value)
    if 'ipack' in v:
        return 'ipack'
    if 'exam' in v or 'cyclades' in v or 'santorin' in v:
        return 'examens'
    if 'text' in v or 'regl' in v:
        return 'textes'
    return v or 'inconnu'


def public_of(value):
    raw = str(value or '').strip()
    if raw in ('Collège (DNB)', 'Collège', 'Lycée Général & Techno', 'Lycée Pro / CAP', '1er degré'):
        return 'Collège (DNB)' if raw == 'Collège' else raw
    v = norm(raw)
    for k, p in PUBLICS.items():
        if norm(k) in v:
            return p
    return raw or 'inconnu'


def route(question, mode, public):
    if mode == 'ipack' and (requests_guide(question, mode, public) or vague_request_opens_guide(question, mode, public)):
        return 'guide pas à pas', ''
    try:
        if kc.clarification(question, public):
            return 'demande de précision', ''
    except Exception:
        pass
    try:
        direct, md = kc.documented_response(question, public, mode)
        if direct:
            return 'réponse documentée', md.get('title', '')
    except Exception:
        pass
    try:
        titles = kc.priority_titles(question, public, mode)
    except Exception:
        titles = []
    if titles:
        prio = {md.get('title'): md.get('priorite', 0) or 0 for md in kc.catalog().values()}
        return 'fiche ciblée', max(titles, key=lambda t: prio.get(t, 0))
    return 'recherche générale (sans fiche ciblée)', ''


def main():
    src = sys.argv[1]
    out = Path(sys.argv[2] if len(sys.argv) > 2 else 'stat_journal')
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    out.mkdir(parents=True, exist_ok=True)
    rows = read_rows(src)
    data, seen, todo = [], set(), {}
    for r in rows:
        q = column(r, 'question').strip()
        if len(q) >= 8:
            todo.setdefault((q, mode_of(column(r, 'mode', 'onglet', 'module')), public_of(column(r, 'niveau', 'public'))), None)
    from multiprocessing import Pool
    with Pool(4) as pool:
        routes = dict(zip(todo, pool.starmap(route, list(todo), chunksize=8)))
    for i, r in enumerate(rows, 1):
        q = column(r, 'question').strip()
        if len(q) < 8:
            continue
        mode = mode_of(column(r, 'mode', 'onglet', 'module'))
        public = public_of(column(r, 'niveau', 'public'))
        key = (norm(q), mode, public)
        dup = key in seen
        seen.add(key)
        kind, title = routes[(q, mode, public)]
        data.append({'ligne': i, 'date': column(r, 'date', 'horodat', 'timestamp'), 'mode': mode, 'public': public,
                     'question': q, 'reponse': column(r, 'reponse', 'réponse'), 'version': column(r, 'version'),
                     'traitement': kind, 'fiche': title, 'doublon': 'oui' if dup else ''})
    uniques = [d for d in data if not d['doublon']]
    lines = [f'# Couverture du journal — {len(data)} questions lues, {len(uniques)} sans doublon', '',
             'Calcul sans appel IA : quelle fiche le hub transmettrait aujourd\'hui (version locale du dépôt).', '']
    by = defaultdict(Counter)
    for d in uniques:
        by[(d['mode'], d['public'])][d['traitement']] += 1
    kinds = ['fiche ciblée', 'réponse documentée', 'guide pas à pas', 'demande de précision', 'recherche générale (sans fiche ciblée)']
    lines += ['| Onglet | Public | Total | ' + ' | '.join(kinds) + ' |', '|' + '---|' * (3 + len(kinds))]
    total = Counter()
    for (m, p), c in sorted(by.items(), key=lambda x: -sum(x[1].values())):
        n = sum(c.values()); total.update(c)
        lines.append(f'| {m} | {p} | {n} | ' + ' | '.join(f'{c[k]} ({100*c[k]//n} %)' for k in kinds) + ' |')
    n = sum(total.values()) or 1
    lines.append(f'| **Tous** | | {n} | ' + ' | '.join(f'{total[k]} ({100*total[k]//n} %)' for k in kinds) + ' |')
    fiches = Counter(d['fiche'] for d in uniques if d['fiche'])
    lines += ['', '## Fiches les plus sollicitées', ''] + [f'- {t} : {c}' for t, c in fiches.most_common(25)]
    orphans = [d for d in uniques if d['traitement'].startswith('recherche')]
    words = Counter()
    for d in orphans:
        toks = [w for w in re.findall(r'[a-z0-9]{3,}', norm(d['question'])) if w not in STOP]
        words.update(set(toks)); words.update({' '.join(b) for b in zip(toks, toks[1:])})
    lines += ['', f'## Sujets des {len(orphans)} questions sans fiche ciblée (mots et paires les plus fréquents)', '']
    lines += [f'- {w} : {c}' for w, c in words.most_common(60) if c >= 3]
    (out / 'couverture.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    fields = ['ligne', 'date', 'mode', 'public', 'question', 'traitement', 'fiche', 'version']
    with open(out / 'sans_fiche.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(orphans)
    rnd = random.Random(20261018)
    strata = defaultdict(list)
    for d in uniques:
        strata[d['mode']].append(d)
    sample = []
    for m, items in strata.items():
        k = max(1, round(size * len(items) / max(1, len(uniques))))
        sample += rnd.sample(items, min(k, len(items)))
    rnd.shuffle(sample)
    with open(out / 'echantillon_a_noter.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['n', 'ligne', 'mode', 'public', 'version', 'question', 'reponse', 'traitement', 'fiche',
                                          'verdict (correct/partiel/faux)', 'gravite (0-2)', 'commentaire'], extrasaction='ignore')
        w.writeheader()
        for i, d in enumerate(sample, 1):
            w.writerow(dict(d, n=i))
    print((out / 'couverture.md').read_text(encoding='utf-8')[:3000])


if __name__ == '__main__':
    main()
