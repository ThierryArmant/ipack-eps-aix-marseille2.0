"""Restitution bornée de passages logiciels cités ; aucun appel réseau."""
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path

CHAIN = re.compile(r'\[[^\]\n]{1,120}\](?:\s*(?:>|→)\s*\[[^\]\n]{1,120}\])+')
ROOT = Path(__file__).resolve().parent

def normalized(text):
    text=''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'\w+',text))

def signature(claim):
    return (claim.get('text'),tuple((e.get('document_id'),tuple(e.get('passage_ids') or ([e['passage_id']] if e.get('passage_id') else []))) for e in claim.get('evidence',[])))

def restore_navigation(final, accepted, packets, model_packets, root=ROOT):
    """Copie exacte, uniquement pour dix fichiers à empreinte explicitement enregistrés."""
    result=copy.deepcopy(final)
    report={'replacements':[], 'skipped':[], 'extra_ai_calls':0, 'scope':'ten_registered_files'}
    try:
        registry=json.loads((root/'config/navigation_restore_pilot.json').read_text())
        registered={s['path']:s['sha256'] for s in registry['sources']}
    except (OSError,ValueError,KeyError,TypeError):
        report['unavailable']=True
        return result,report
    by_id={p['id']:p for p in packets}
    transmitted={(p['id'],s['id']):s for p in model_packets for s in p.get('passages',[])}
    valid={signature(c) for c in accepted}
    for index,claim in enumerate(result.get('claims',[])):
        if signature(claim) not in valid or claim.get('section')!='etape':
            continue
        refs=claim.get('evidence',[])
        if len(refs)!=1 or len(refs[0].get('passage_ids',[]))!=1:
            continue
        ref=refs[0];packet=by_id.get(ref.get('document_id'),{})
        path=packet.get('path','')
        if path not in registered:
            continue
        span=transmitted.get((ref['document_id'],ref['passage_ids'][0]))
        if not span or span.get('scope',{}).get('level')!='logiciel':
            continue
        text=span.get('text','');chains=CHAIN.findall(text)
        if not chains or all(normalized(c) in normalized(claim['text']) for c in chains):
            continue
        reason=None
        if len(chains)!=1 or len(text)>900:
            reason='passage_long_ou_plusieurs_chemins'
        elif re.match(r'\s*(?:Réponse directe|Provenance|Sources?)\b',text,re.I):
            reason='libelle_editorial_a_separer'
        try:
            source=(root/path).read_bytes()
            if hashlib.sha256(source).hexdigest()!=registered[path]:
                reason='source_modifiee'
        except OSError:
            reason='source_absente'
        if reason:
            report['skipped'].append({'index':index,'reason':reason,'path':path})
            continue
        previous=claim['text'];claim['text']=text
        report['replacements'].append({'index':index,'path':path,'document_id':ref['document_id'],
                                       'passage_ids':list(ref['passage_ids']), 'before':previous,'after':text})
    return result,report
