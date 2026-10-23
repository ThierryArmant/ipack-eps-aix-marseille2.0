"""Contrôles hors ligne du pilote ; ne génère ni ne valide une réponse métier."""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIPLOMAS = {'college', 'gt', 'pro', 'cap', 'premier_degre'}
NATURES = {'logiciel', 'academique', 'reglementaire', 'synthese_reglementaire'}

def normalized(text):
    value = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'\w+', value))

def validate(pilot, root=ROOT):
    """Vérifie structure et copies exactes ; aucune appréciation de droit ou de sens."""
    errors = []
    for key in ('format_version', 'id', 'type', 'situation', 'scope', 'verification', 'sources', 'branches'):
        if key not in pilot:
            errors.append('champ absent : ' + key)
    if errors:
        return errors
    if pilot['format_version'] != 1:
        errors.append('version de format inconnue')
    if pilot['type'] not in ('diagnostic', 'navigation', 'regle_et_circuit'):
        errors.append('type inconnu')
    if pilot['verification'].get('status') != 'structure_controlee_sources_non_revalidees':
        errors.append('statut de validation non autorisé pour ce pilote')
    def check_scope(scope, location):
        if not isinstance(scope, dict):
            errors.append(location + ' : portée absente'); return
        for key in ('diplomas', 'academies', 'software'):
            if key not in scope or not isinstance(scope[key], list):
                errors.append(location + ' : portée invalide ' + key)
        if not set(scope.get('diplomas', [])) <= DIPLOMAS:
            errors.append(location + ' : diplôme inconnu')
    check_scope(pilot['scope'], 'fiche')
    sources = {}
    for source in pilot['sources']:
        if source['id'] in sources:
            errors.append('source dupliquée : ' + source['id'])
        path = (root / source['path']).resolve()
        if not path.is_relative_to(root.resolve()):
            errors.append('source hors dépôt'); continue
        if not path.is_file():
            errors.append('source absente : ' + source['path']); continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            errors.append('source modifiée : ' + source['path'])
        sources[source['id']] = raw.decode('utf-8')
    branch_ids, step_ids = set(), set()
    if not pilot['branches']:
        errors.append('aucune branche')
    for branch in pilot['branches']:
        if branch['id'] in branch_ids:
            errors.append('branche dupliquée : ' + branch['id'])
        branch_ids.add(branch['id'])
        check_scope(branch.get('scope'), branch['id'])
        if not set(branch.get('scope', {}).get('diplomas', [])) <= set(pilot['scope'].get('diplomas', [])):
            errors.append('branche hors portée de la fiche : ' + branch['id'])
        if not branch.get('condition') or not branch.get('steps'):
            errors.append('condition ou étapes absentes : ' + branch['id'])
        for limit in branch.get('limits', []):
            if not any(limit in text for text in sources.values()):
                errors.append('limite sans citation exacte : ' + branch['id'])
        for step in branch.get('steps', []):
            sid = step['id']
            if sid in step_ids:
                errors.append('étape dupliquée : ' + sid)
            step_ids.add(sid)
            if not step.get('actor') or step.get('nature') not in NATURES:
                errors.append('acteur ou nature manquant : ' + sid)
            evidence = step.get('evidence', [])
            if not evidence:
                errors.append('preuve absente : ' + sid)
            for item in evidence:
                text = sources.get(item['source_id'], '')
                if not item.get('quote') or item['quote'] not in text:
                    errors.append('citation absente de la source : ' + sid)
            if not any(step.get('text') == item.get('quote') for item in evidence):
                errors.append('étape non recopiée exactement : ' + sid)
            for element in step.get('navigation', []) + step.get('required_elements', []):
                if not element or element not in step.get('text', ''):
                    errors.append('élément absent du passage : ' + sid)
    return errors

def coverage(pilot, branch_ids, answer):
    """Signalement lexical sur branches choisies explicitement, sans réparation automatique."""
    unknown = set(branch_ids) - {branch['id'] for branch in pilot['branches']}
    if unknown:
        raise ValueError('Branches inconnues : ' + ', '.join(sorted(unknown)))
    text, findings, not_checked = normalized(answer), [], []
    for branch in pilot['branches']:
        if branch['id'] not in branch_ids:
            continue
        for step in branch['steps']:
            elements = step.get('required_elements', []) + step.get('navigation', [])
            if not elements:
                not_checked.append(step['id'])
            for element in elements:
                if normalized(element) not in text:
                    findings.append({'branch_id': branch['id'], 'step_id': step['id'],
                                     'element': element, 'signal': 'omission_lexicale_possible'})
    return {'findings': findings, 'not_checked': not_checked,
            'semantic_validation': False, 'automatic_repair': False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path)
    parser.add_argument('--pilot', type=Path)
    parser.add_argument('--branches', nargs='+')
    args = parser.parse_args()
    paths = sorted((ROOT/'docs/fiches_pilotes').glob('*.json'))
    for path in paths:
        errors = validate(json.loads(path.read_text()))
        if errors:
            raise SystemExit(path.name + ': ' + '; '.join(errors))
    print(str(len(paths)) + ' prototypes : structure, empreintes et citations exactes vérifiées ; sources non revalidées.')
    if args.trace:
        if not args.pilot or not args.branches:
            parser.error('--trace nécessite --pilot et --branches ; aucune applicabilité déduite automatiquement')
        trace = json.loads(args.trace.read_text())
        claims = trace.get('proposal', {}).get('claims', [])
        answer = '\n'.join(claim.get('text', '') for claim in claims)
        print(json.dumps(coverage(json.loads(args.pilot.read_text()), args.branches, answer), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
