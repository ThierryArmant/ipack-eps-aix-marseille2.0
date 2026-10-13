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


def attributed_segments(path, body, segments):
    """Applique seulement les annotations exactes, uniques et non chevauchantes."""
    record = _registry('nature_passages.json').get(_path(path))
    if not record:
        return segments
    annotations = []
    for annotation in record.get('passages', []):
        text = annotation.get('texte', '')
        kinds = annotation.get('nature', [])
        if not text or body.count(text) != 1 or not kinds or any(k not in KINDS for k in kinds):
            continue
        start = body.index(text)
        annotations.append((start, start + len(text), annotation))
    annotations.sort(key=lambda item: item[0])
    if any(a[1] > b[0] for a, b in zip(annotations, annotations[1:])):
        annotations = []
    result = []
    for span in segments:
        cuts = {span['start'], span['end']}
        for start, end, _ in annotations:
            if span['start'] <= start < end <= span['end']:
                cuts.update((start, end))
        cuts = sorted(cuts)
        for start, end in zip(cuts, cuts[1:]):
            text = body[start:end]
            if not text.strip():
                continue
            scope = dict(span.get('scope', {}))
            match = next((a for astart, aend, a in annotations if astart <= start and end <= aend), None)
            # L'étiquette de toute la fiche ne doit pas remplacer une attribution manquante.
            scope.pop('academy', None)
            scope.pop('not_confirmed_for', None)
            kinds = match['nature'] if match else record.get('nature_non_attribuee', ['a_verifier'])
            scope.update(nature=kinds, level=KINDS[kinds[0]] if len(kinds)==1 else 'mixte',
                         status='passage_attribue' if match else 'passage_non_attribue')
            if match:
                scope['reference'] = match.get('reference', '')
                if match.get('academie'):
                    scope['academy'] = match['academie']
                elif kinds == ['texte_national']:
                    scope.pop('file_academy', None)
                    scope.pop('other_academies', None)
            elif span.get('scope', {}).get('academy'):
                scope['academy'] = span['scope']['academy']
            result.append({'text':text,'start':start,'end':end,'scope':scope})
    return result


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
                   'status':'non_verifie' if 'a_verifier' in kinds else ('passage_non_attribue' if len(kinds)>1 else 'metadata_fiche')}
            if record.get('academies_applicables'):
                scope.update(academy='Région académique Provence-Alpes-Côte d’Azur', academies_applicables=record['academies_applicables'])
            elif record.get('type_source') == 'courriel_assistance':
                scope.update(level='assistance', academy='Aix-Marseille', reference=record.get('source_reference', ''), status='retour_assistance_date')
            elif marked:
                scope['academy']='Aix-Marseille'
            segments.append({'text':text, 'start':offset, 'end':offset+len(text), 'scope':scope})
        offset+=len(line)
    return attributed_segments(path, body, segments or [{'text':body,'start':0,'end':len(body),
                         'scope':{'level':'documentaire','status':'non_verifie'}}])


def select_academy(packets, academy):
    """Marque les consignes d'Aix hors Aix, sans supprimer une règle nationale mixte."""
    selected, marked=[],[]
    for packet in packets:
        spans=[]
        for span in packet['passages']:
            scope=dict(span.get('scope', {}))
            if scope.get('academy') and academy not in scope.get('academies_applicables', [scope['academy']]):
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
        if len(scope.get('nature', [])) > 1:
            prefix=(f"[Fiche mixte, passage inventorié pour Aix-Marseille : distinguer le cadre national "
                    f"de l’application locale, à vérifier pour {scope['not_confirmed_for']}] ")
        else:
            origin = ('l’académie d’Aix-Marseille' if scope.get('academy') == 'Aix-Marseille' else scope.get('academy', 'l’académie d’Aix-Marseille'))
            prefix=f"[Consigne de {origin} — non confirmée pour {scope['not_confirmed_for']}] "
        result['text']=prefix+span['text']
    return result


def _nom_academie(code):
    # Le registre stocke un identifiant (« aix-marseille ») ; l'affichage garde le nom officiel.
    from academie import ACADEMIES
    return next((a for a in ACADEMIES if a.lower().replace(' ', '-') == str(code).lower()), str(code))


def evidence_label(evidence, packet, labels):
    scope=evidence.get('scope', {})
    kinds=scope.get('nature', [])
    if len(kinds)>1:
        names={'texte_national':'cadre national','consigne_academique':'circuit académique','logiciel':'logiciel','a_verifier':'portée à vérifier'}
        label=('Passage non attribué — fiche mixte : ' if scope.get('status') == 'passage_non_attribue' else 'Fiche mixte : ')+' + '.join(names.get(k,k) for k in kinds)
    else:
        label=labels.get(scope.get('level') or packet.get('display_level','documentaire'),'Portée à vérifier')
    if scope.get('academy'):
        label+=' — '+scope['academy']
    elif scope.get('file_academy') and 'consigne_academique' in kinds:
        label+=' — origine académique : '+_nom_academie(scope['file_academy'])
    if scope.get('not_confirmed_for'):
        label+=(' (application locale à vérifier pour ' if len(kinds)>1 else ' (non confirmé pour ')+scope['not_confirmed_for']+')'
    if scope.get('other_academies'):
        label+=' — exemples cités : '+', '.join(scope['other_academies'])
    if scope.get('status')=='non_verifie':
        label+=' (portée à vérifier)'
    if scope.get('reference'):
        label+=' — '+scope['reference']
    return label+' : '+packet['title']
