"""Revue administrateur locale ; aucun appel IA, aucune modification de réponse."""
import copy
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

def navigation_preview(trace, pilot, branch_ids, root=ROOT):
    """Aperçu seulement : recopie d'un passage réellement cité et transmis."""
    report = review(trace, pilot, branch_ids, root)
    result = {'status': 'apercu_seulement', 'pilot_id': pilot['id'], 'branch_ids': list(branch_ids),
              'trace_version': trace.get('version'), 'replacements': [], 'claims': [],
              'automatic_repair': False, 'original_response_changed': False}
    if report.get('errors'):
        result['errors'] = report['errors']
        return result
    claims = copy.deepcopy(trace.get('final_claims') or [])
    result['claims'] = claims
    if not claims:
        result['reason'] = 'Aucune affirmation finale acceptée : aucune restitution proposée.'
        return result
    data = None
    for call in reversed(trace.get('calls', [])):
        if call.get('stage') != 'generation':
            continue
        tail = call.get('prompt', '').rpartition('DONNEES :')[2].lstrip()
        if tail:
            try:
                data, _ = json.JSONDecoder().raw_decode(tail)
            except (ValueError, TypeError):
                continue
            if isinstance(data, dict) and isinstance(data.get('documents'), list):
                break
            data = None
    if data is None:
        result['reason'] = 'Documents transmis non retrouvés : aucune restitution proposée.'
        return result
    paths = {p['id']: p.get('path') for p in trace.get('documents', [])}
    allowed_paths = {s['path'] for s in pilot['sources']}
    spans = {(d['id'], p['id']): p['text'] for d in data['documents']
             if paths.get(d['id']) in allowed_paths for p in d.get('passages', [])}
    checker = load_checker(root)
    answer = '\n'.join(c.get('text', '') for c in claims)
    changed = set()
    for branch in pilot['branches']:
        if branch['id'] not in branch_ids:
            continue
        for step in branch['steps']:
            # Pas de restitution des règles, choix ou autorités sur simple ressemblance lexicale.
            if step.get('nature') != 'logiciel' or not step.get('navigation'):
                continue
            if all(checker.normalized(path) in checker.normalized(answer) for path in step['navigation']):
                continue
            for index, claim in enumerate(claims):
                evidence = claim.get('evidence', [])
                if index in changed or len(evidence) != 1 or len(evidence[0].get('passage_ids', [])) != 1:
                    continue
                item = evidence[0]
                passage = spans.get((item['document_id'], item['passage_ids'][0]))
                if passage != step['text']:
                    continue
                # Remplacer le texte entier conserve les conditions et l'acteur de la source.
                previous = claim['text']
                claim['text'] = passage
                changed.add(index)
                result['replacements'].append({'index': index, 'step_id': step['id'],
                                               'before': previous, 'after': passage,
                                               'evidence': copy.deepcopy(evidence)})
                answer = '\n'.join(c.get('text', '') for c in claims)
                break
    return result


def render(st, trace, key):
    try:
        pilots = available_pilots(trace)
    except (OSError, ValueError, KeyError):
        st.warning('Prototypes indisponibles ; aucune vérification effectuée.')
        return
    with st.expander('Contrôle pilote des étapes et chemins — sans appel IA'):
        st.caption('Revue de la proposition initiale : les restitutions appliquées ensuite à la réponse finale sont indiquées séparément. Le contrôle manuel ne modifie pas la réponse et ne lance aucun appel IA.')
        restored = trace.get('navigation_restore') or {}
        if restored.get('applied'):
            st.info(str(len(restored.get('replacements', []))) + ' passage(s) avec chemin restitué(s) dans la réponse finale ; la proposition initiale reste disponible pour comparaison.')
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
        if st.button('Prévisualiser les passages cités avec leur chemin — sans appel IA', key=key+'_preview'):
            try:
                trace['fiche_pilot_preview'] = navigation_preview(trace, pilot, branches)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                st.warning(str(exc))
        preview = trace.get('fiche_pilot_preview')
        if preview:
            st.caption('Aperçu : ' + str(preview.get('pilot_id', 'prototype')) + ' · branches : ' + ', '.join(preview.get('branch_ids', [])))
            st.caption('Aperçu expérimental séparé : la réponse originale reste inchangée. Le réviseur doit confirmer l’applicabilité du passage et de son acteur.')
            if preview.get('errors'):
                st.warning('Prototype à revoir : ' + '; '.join(preview['errors']))
            elif preview.get('replacements'):
                for change in preview['replacements']:
                    st.write('Passage recopié — ' + change['step_id'])
                    st.write(change['after'])
                st.json(preview)
            else:
                st.info(preview.get('reason') or 'Aucun remplacement admissible : un passage avec chemin doit être cité seul et avoir été transmis intégralement.')
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
