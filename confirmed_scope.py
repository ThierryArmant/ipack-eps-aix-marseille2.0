"""Sonde privée : corrections explicites de logiciel, sans réponse métier ni modification des sources."""
import re
import unicodedata

SOFTWARE = {
    'santorin': r'\bsantorin\b', 'cyclades': r'\bcyclades\b',
    'ipackeps': r'\bipack(?:eps)?\b', 'pronote': r'\bpronote\b',
    'ecoledirecte': r'\becole[ -]?directe\b', 'lsu': r'\blsu\b',
}


def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c))


def explicit_scope(confirmation):
    """Ne traite que les corrections explicites ; une difficulté dans X ne nie pas X."""
    text=norm(confirmation)
    rejected=[]
    for name,pattern in SOFTWARE.items():
        word=pattern.replace(r'\b','')
        expressions=[r"(?:ce |c.)?n.est pas\s+(?:dans |sur )?(?:le logiciel )?"+word+r'\b',
                     r"ne (?:parle|s.agit) pas (?:de |du logiciel )"+word+r'\b',
                     r"pas "+word+r"\s*[,;:]?\s*mais\b"]
        if any(re.search(p,text) for p in expressions):rejected.append(name)
    mentioned=[name for name,p in SOFTWARE.items() if re.search(p,text)]
    affirmed=[name for name in mentioned if name not in rejected]
    return dict(rejected=rejected, affirmed=affirmed,
                determinate=bool(rejected) and len(affirmed)==1)


def routing_question(original, confirmation):
    """Le texte original reste intact dans le dossier ; seule une copie de recherche est filtrée."""
    scope=explicit_scope(confirmation)
    full=original+'\n\nPrécision confirmée par le demandeur : '+confirmation
    routing=full
    if scope['determinate']:
        # N'enlever que les logiciels explicitement écartés par l'utilisateur, pas les négations.
        for name in scope['rejected']:
            routing=re.sub(SOFTWARE[name], '[logiciel explicitement écarté]', routing, flags=re.I)
    return dict(original_question=original, confirmation=confirmation,
                question_for_answer=full, routing_question=routing, scope=scope)


def filter_rejected_software(packets, scope):
    """Écarter un titre portant sur le logiciel explicitement nié, sauf titre comparant aussi le logiciel confirmé."""
    if not scope['determinate']:return list(packets),[]
    kept,excluded=[],[]
    for packet in packets:
        title=norm(packet.get('title',''))
        rejected=any(re.search(SOFTWARE[n],title) for n in scope['rejected'])
        affirmed=any(re.search(SOFTWARE[n],title) for n in scope['affirmed'])
        (excluded if rejected and not affirmed else kept).append(packet)
    return kept,excluded


def confirmed_learner_in_lot(confirmation):
    """Repère seulement une liste de candidats/élèves dans un lot explicitement confirmée."""
    text=norm(confirmation)
    if re.search(r"n.est pas|ne .{0,30}pas|\bpas de\b",text):
        return False
    return bool(re.search(r'liste (?:des|de mes) (?:candidats?|eleves?)',text)
                and re.search(r'\blots?\b',text))


def filter_lot_owner_mismatch(packets, confirmation):
    if not confirmed_learner_in_lot(confirmation):return list(packets),[]
    kept,excluded=[],[]
    for packet in packets:
        title=norm(packet.get('title',''))
        teacher=bool(re.search(r'collegue|enseignant|professeur|correcteur|co.?evaluateur',title))
        learner=bool(re.search(r'eleve|candidat',title))
        lot=bool(re.search(r'\blots?\b|missions?',title))
        (excluded if teacher and lot and not learner else kept).append(packet)
    return kept,excluded


def missing_learner_search(original, confirmation):
    """Synonyme de recherche, pas fait métier : la personne est explicitement confirmée, l'absence est dans la demande."""
    if not confirmed_learner_in_lot(confirmation):return None
    q=norm(original)
    if not re.search(r'ne (?:retrouve|trouve|vois) pas|manqu|absen|n.apparai',q):return None
    # Le terme « candidat » est validé par la précision, aucun inscrit/examen/date n'est ajouté.
    subject='candidats' if re.search(r'candidat',norm(confirmation)) else 'eleves'
    return 'Il manque des '+subject+'. '+confirmation


def filter_absent_lot_when_open(packets, confirmation):
    """Ne pas déduire qu'un lot existe : il faut une ouverture explicitement confirmée."""
    q=norm(confirmation)
    opened=bool(re.search(r'lot (?:est |s.)?(?:ouvert|ouvre|accessible)',q))
    learner=bool(re.search(r'eleve|candidat',q))
    if not (opened and learner):return list(packets),[]
    kept,excluded=[],[]
    for p in packets:
        title=norm(p.get('title',''))
        absent_container=bool(re.search(r'aucun lot|pas de lot|lot manquant',title))
        learner_title=bool(re.search(r'eleve|candidat',title))
        (excluded if absent_container and not learner_title else kept).append(p)
    return kept,excluded


def retrieve_confirmed(original, confirmation, public, mode, retrieve):
    """Une recherche de base puis au plus un complément ; aucune génération IA."""
    from knowledge_catalog import effective_context
    from documentary_review import source_packets,mark_excerpt
    plan=routing_question(original,confirmation)
    public,mode=effective_context(plan['routing_question'],public,mode)
    lookups=[]
    def lookup(search=None):
        docs,sources,diag,error=retrieve(plan['routing_question'],public,mode,search)
        lookups.append(dict(search=search,sources=sources,diagnostic=diag,error=error))
        if error:raise RuntimeError('Recherche indisponible.')
        return source_packets(docs)
    initial=lookup()
    def filter_all(packets):
        kept,a=filter_rejected_software(packets,plan['scope'])
        kept,b=filter_lot_owner_mismatch(kept,confirmation)
        kept,c=filter_absent_lot_when_open(kept,confirmation)
        return kept,a+b+c
    kept,excluded=filter_all(initial)
    complement=missing_learner_search(original,confirmation)
    if complement and not any(re.search(r'eleve|candidat',norm(p['title'])) for p in kept):
        extra=lookup(complement)
        seen={(p['path'],p['sha256']) for p in initial}
        initial+= [p for p in extra if (p['path'],p['sha256']) not in seen]
        kept,excluded=filter_all(initial)
    documents='\n\n'.join(mark_excerpt(p['text'],path=p['path'],title=p['title'],priority=p['priority'],
                                       origin=p['origin'],url=p['url'],selection=p['selection'],scopes=p['scopes']) for p in kept)
    return dict(plan=plan,public=public,mode=mode,lookups=lookups,
                excluded=[dict(path=p['path'],title=p['title']) for p in excluded],
                kept=[dict(path=p['path'],title=p['title']) for p in kept],documents=documents)
