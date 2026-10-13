"""Attributions issues des registres maintenus avec les fiches, jamais de l'IA."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KINDS = {'texte_national':'synthese_reglementaire', 'consigne_academique':'academique',
         'logiciel':'logiciel', 'a_verifier':'documentaire'}


def _registry(name):
    try:
        return json.loads((ROOT/'config'/name).read_text(encoding='utf-8')).get('fichiers', {})
    except (OSError, ValueError):
        return {}


def _path(path):
    path=str(path).replace('\\','/')
    return 'data/'+path.split('/data/',1)[1] if '/data/' in path else path


def annotations(path):
    return _registry('nature_sources.json').get(_path(path))


def scoped_segments(path, body):
    record=annotations(path)
    if record is None:
        return None
    local=_registry('portee_academique.json').get(_path(path), {})
    lines=[line for section in local.get('sections', []) for line in section.get('lignes', [])]
    # Inventaire parfois tronqué ou antérieur à une fiche corrigée : pas de correspondance floue.
    matches=[line for line in lines if line in body and not line.startswith(('###','Source'))]
    kinds=record.get('nature', ['a_verifier'])
    segments=[]
    offset=0
    for line in body.splitlines(keepends=True):
        text=line.rstrip('\r\n')
        if text and not text.startswith(('###','[PORTEE:', '[DOCUMENT:', 'Portée :','Nature de la source',
                                         'Nature des sources', 'Sources datées :','Source :','Fiche de contrôle :','http')):
            marked=any(m in text for m in matches)
            # Une fiche mixte est annoncée comme telle : aucune de ses natures n'est arbitrairement choisie.
            scope={'level':KINDS.get(kinds[0], 'documentaire') if len(kinds)==1 else 'mixte',
                   'nature':kinds, 'file_academy':record.get('academie'),
                   'sessions':record.get('sessions', []),
                   'other_academies':record.get('autres_academies_citees', []),
                   'status':'non_verifie' if 'a_verifier' in kinds else 'metadata_fiche'}
            if marked:
                scope['academy']='Aix-Marseille'
            segments.append({'text':text, 'start':offset, 'end':offset+len(text), 'scope':scope})
        offset+=len(line)
    return segments or [{'text':body,'start':0,'end':len(body),
                         'scope':{'level':'documentaire','status':'non_verifie'}}]


def select_academy(packets, academy):
    """Marque les consignes d'Aix hors Aix, sans supprimer une règle nationale mixte."""
    selected, marked=[],[]
    for packet in packets:
        spans=[]
        for span in packet['passages']:
            scope=dict(span.get('scope', {}))
            if scope.get('academy') and scope['academy']!=academy:
                scope['not_confirmed_for']=academy
                marked.append({'document_id':packet['id'],'passage_id':span['id'],
                               'academy':scope['academy'],'reason':'autre_academie_marquee'})
            spans.append({**span,'scope':scope})
        selected.append({**packet,'passages':spans})
    return selected,marked


def model_passage(span):
    result=dict(span)
    scope=span.get('scope', {})
    if scope.get('not_confirmed_for'):
        result['text']=(f"[Consigne de l’académie d’Aix-Marseille — non confirmée pour {scope['not_confirmed_for']}] "
                        +span['text'])
    return result


def evidence_label(evidence, packet, labels):
    scope=evidence.get('scope', {})
    kinds=scope.get('nature', [])
    if len(kinds)>1:
        names={'texte_national':'cadre national','consigne_academique':'circuit académique','logiciel':'logiciel','a_verifier':'portée à vérifier'}
        label='Fiche mixte : '+' + '.join(names.get(k,k) for k in kinds)
    else:
        label=labels.get(scope.get('level') or packet.get('display_level','documentaire'),'Portée à vérifier')
    if scope.get('academy'):
        label+=' — '+scope['academy']
    elif scope.get('file_academy') and 'consigne_academique' in kinds:
        label+=' — origine académique : '+scope['file_academy']
    if scope.get('not_confirmed_for'):
        label+=' (non confirmé pour '+scope['not_confirmed_for']+')'
    if scope.get('other_academies'):
        label+=' — exemples cités : '+', '.join(scope['other_academies'])
    if scope.get('status')=='non_verifie':
        label+=' (portée à vérifier)'
    return label+' : '+packet['title']
