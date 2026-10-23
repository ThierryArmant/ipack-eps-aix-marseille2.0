"""Revue administrateur locale ; aucun appel IA, aucune modification de réponse."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading

_LOCK = threading.RLock()
ROOT = Path(__file__).resolve().parent

def load_checker(root=ROOT):
    path = root/'scripts/fiche_pilot.py'
    source = path.read_bytes()
    name = '_eps_fiche_checker_' + hashlib.sha256(source).hexdigest()
    with _LOCK:
        if name not in sys.modules:
            module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
            exec(compile(source, str(path), 'exec'), module.__dict__)
            sys.modules[name] = module
        return sys.modules[name]

def available_pilots(trace, root=ROOT):
    selected = set(trace.get('model_document_ids') or [])
    paths = {p.get('path') for p in trace.get('documents', []) if p.get('id') in selected}
    result = []
    for path in sorted((root/'docs/fiches_pilotes').glob('*.json')):
        pilot = json.loads(path.read_text())
        if any(s.get('path') in paths for s in pilot.get('sources', [])):
            result.append(pilot)
    return result

def review(trace, pilot, branch_ids, root=ROOT):
    checker = load_checker(root)
    errors = checker.validate(pilot, root)
    if errors:
        return {'status': 'prototype_a_revoir', 'errors': errors, 'automatic_repair': False}
    allowed = {p['id'] for p in available_pilots(trace, root)}
    if pilot['id'] not in allowed:
        raise ValueError('La source du prototype ne fait pas partie des documents transmis au modèle.')
    if not branch_ids:
        raise ValueError('Choisissez les branches à examiner, sans les considérer comme établies.')
    claims = trace.get('proposal', {}).get('claims', [])
    answer = '\n'.join(c.get('text', '') for c in claims)
    return {'status': 'revue_lexicale', 'pilot_id': pilot['id'], 'branch_ids': list(branch_ids),
            'target': 'proposition_initiale', 'trace_version': trace.get('version'),
            **checker.coverage(pilot, branch_ids, answer)}

def render(st, trace, key):
    try:
        pilots = available_pilots(trace)
    except (OSError, ValueError, KeyError):
        st.warning('Prototypes indisponibles ; aucune vérification effectuée.')
        return
    with st.expander('Contrôle pilote des étapes et chemins — sans appel IA'):
        st.caption('Revue de la proposition initiale. Choisissez explicitement les branches utiles ; cela ne confirme pas leurs conditions. Aucune réparation automatique, aucun nouvel appel IA.')
        if not pilots:
            st.caption('Aucun des trois prototypes ne correspond aux documents transmis pour cette réponse.')
            return
        lookup = {p['id']: p for p in pilots}
        selected = st.selectbox('Fiche pilote', list(lookup), key=key+'_pilot')
        pilot = lookup[selected]
        labels = {b['id']: b['id'] + ' — ' + b['condition'] for b in pilot['branches']}
        branches = st.multiselect('Branches à examiner', list(labels), format_func=lambda value: labels[value], key=key+'_branches')
        if st.button('Vérifier les éléments conservés — sans appel IA', key=key+'_run'):
            try:
                trace['fiche_pilot_review'] = review(trace, pilot, branches)
            except (OSError, ValueError, KeyError) as exc:
                st.warning(str(exc))
        report = trace.get('fiche_pilot_review')
        if report:
            st.caption("Dernier contrôle : " + str(report.get("pilot_id", "prototype")) + " · branches : " + ", ".join(report.get("branch_ids", [])))
            if report.get('errors'):
                st.warning('Prototype à revoir : ' + '; '.join(report['errors']))
            elif report.get('findings'):
                st.warning('Éléments potentiellement omis : ' + str(len(report['findings'])))
                st.dataframe(report['findings'], hide_index=True)
            else:
                st.info('Aucune omission lexicale détectée sur les éléments choisis. Cela ne valide ni le sens ni la réponse complète.')
            st.caption('Rapport inclus dans la trace téléchargeable. Les réponses affichées ne sont pas modifiées.')
