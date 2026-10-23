#!/usr/bin/env python3
"""Vérifications reproductibles du corpus : aucun client IA ni accès réseau.

Ce contrôle ne valide ni la vérité des sources ni une réponse générée.
Lancer depuis la racine : python -m scripts.audit_corpus_offline --output /tmp/corpus.json
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from knowledge_catalog import active_paths, catalog
from documentary_review import mark_excerpt, source_packets


def audit():
    entries = catalog()
    registry = {r['path']: r for r in json.loads(Path('docs/audit_fiches/registre.json').read_text())['fiches']}
    rows = []
    for folder in ('data/ipack', 'data/examens'):
        for path in active_paths(folder):
            name = path.as_posix()
            text = path.read_text(encoding='utf-8')
            errors = []
            if not text.strip():
                errors.append('fichier_vide')
            if '\x00' in text or '\ufffd' in text:
                errors.append('caractere_corrompu')
            if re.search(r'\b\d+ tokens? truncated\b|\[\.\.\.\s*truncated', text, re.I):
                errors.append('troncature_editoriale')
            entry = registry.get(name)
            if not entry:
                errors.append('absent_registre')
            elif entry['sha256'] != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append('empreinte_perimee')
            packets = source_packets(mark_excerpt(text, path=name))
            proof_text = '\n'.join(s['text'] for p in packets for s in p['passages'])
            # Les titres deviennent des métadonnées ; chaque ligne de contenu doit rester
            # dans les preuves. Les répétitions de contexte ajoutées sont autorisées.
            compact = lambda s: re.sub(r'\s+', '', s)
            content_lines = [line for line in text.splitlines() if line.strip()
                             and not line.lstrip().startswith(('###', '===', 'Nature de', 'Nature des', 'Sources datées :', 'Source :', 'Fiche de contrôle :', 'http', '[PORTEE:', '[SECTION:', '[DOCUMENT:'))]
            if any(compact(line) not in compact(proof_text) for line in content_lines):
                errors.append('ligne_de_contenu_absente_des_preuves')
            signals = []
            if re.search(r'instruction de routage|ignorer les procedures|appliquer strictement', text, re.I):
                signals.append('consigne_de_routage_dans_source')
            if re.search(r'principe absolu|stricte obligation', text, re.I):
                signals.append('regle_absolue_a_examiner')
            rows.append({'path': name, 'indexation_autorisee': entries.get(name, {}).get('retrieval_enabled') is not False,
                         'statut_documentaire': entry.get('statut_audit') if entry else None,
                         'erreurs_mecaniques': errors, 'signaux_non_conclusifs': signals})
    return {'methode': 'controle_mecanique_sans_IA_ni_validation_semantique',
            'fichiers': len(rows), 'fichiers_avec_erreur_mecanique': sum(bool(r['erreurs_mecaniques']) for r in rows),
            'fichiers_avec_signal': sum(bool(r['signaux_non_conclusifs']) for r in rows), 'details': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'details'}, ensure_ascii=False))
    return bool(result['fichiers_avec_erreur_mecanique'])


if __name__ == '__main__':
    raise SystemExit(main())
