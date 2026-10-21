"""Recherche commune au hub et au comparateur administrateur."""
import re
import unicodedata

def normaliser(txt):
    return "".join(c for c in unicodedata.normalize("NFD", txt.lower()) if unicodedata.category(c) != "Mn")

from knowledge_catalog import incompatible, reference_notice, passage_key
from response_controls import reference_url
from documentary_review import mark_excerpt

def retrieve_documents(*, prompt, p_norm, p_low, niveau_actuel_form, mode, est_college, est_clairement_lycee, mots_cles_intention_peda, recherche_mots, chercher_par_mots, retriever_textes, retriever_peda, retriever_santorin, retriever_ipack, libelle_source, _url_source, search_prompt=None, reference_notice=reference_notice):
    """Cherche les passages utiles dans les bases pour la question en cours.
    Renvoie (extraits pour l'IA, sources affichables, fiches pour le diagnostic admin, message d'erreur)."""
    _extraits, _sources, _diag, _erreur, _vus = [], [], [], "", set()
    _priorites_fiches = []

    # ✅ AJOUT : beaucoup de fiches de la FAQ donnent une réponse PAR EXAMEN (« Réponse Lycée GT Bac »,
    # « Réponse Lycée Pro Bac / Lycée Pro CAP », « Réponse Lycée Pro CAP », « Réponse Collège DNB »), chacune dans
    # son propre passage. L'IA piochait parfois la réponse d'un autre examen (ex. CAP : 2 épreuves, servie pour
    # une question sur le bac pro : 3 épreuves). On écarte donc ici les réponses qui visent un autre examen que
    # celui de la question (ou, à défaut, que celui du public sélectionné).
    _cibles = set()
    if re.search(r"\b(?:cp|ce[12]|cm[12])\b|premier degre|elementaire|maternelle|ecole primaire", p_norm):
        _cibles.add("primaire")
    if re.search(r"\bbac(calaureat)?s? ?pro\b|baccalaureat professionnel|\bbacs? professionnels?\b|\bbcp\b", p_norm):
        _cibles.add("pro")
    if re.search(r"\bcap\b", p_norm):
        _cibles.add("cap")
    if niveau_actuel_form != "1er degré" and (re.search(r"\b(dnb|brevet|college|collegiens?)\b|(eleves? de|classes? de|mes|nos|les) (sixiemes?|cinquiemes?|quatriemes?|troisiemes?|6e|5e|4e|3e)\b", p_norm) or (est_college and not est_clairement_lycee)):
        _cibles.add("dnb")
    if re.search(r"bac(calaureat)? ?(general|techno|gt)\b|\blgt\b|voie (generale|techno)", p_norm):
        _cibles.add("gt")
    if not _cibles:
        _cibles = {"Collège (DNB)": {"dnb"}, "Lycée Général & Techno": {"gt"}, "Lycée Pro / CAP": {"pro", "cap"}, "1er degré": {"primaire"}}.get(niveau_actuel_form, set())

    def _autre_examen(txt):
        """Vrai si le passage ne contient que des réponses destinées à d'autres examens que celui visé."""
        if incompatible(txt, _cibles):
            return True
        if not _cibles:
            return False
        _etiquettes = re.findall(r"R[ée]ponse\s+((?:Lyc[ée]e|Coll[èe]ge)[^*:\n]*)", txt)
        if not _etiquettes:
            return False
        _vises = set()
        for _e in _etiquettes:
            _e = normaliser(_e)
            if "gt" in _e:
                _vises.add("gt")
            if "pro bac" in _e:
                _vises.add("pro")
            if "cap" in _e:
                _vises.add("cap")
            if "college" in _e or "dnb" in _e:
                _vises.add("dnb")
        return bool(_vises) and not (_vises & _cibles)

    # Hors circuit d’examen, ne pas transposer les procédures CCF de lycée au collège. Une question sur le
    # dossier EPS recevait des fiches d'export vers Cyclades et l'IA les recopiait.
    _college_hors_examen = niveau_actuel_form == "Collège (DNB)" and not re.search(
        r"cyclades|santorin|imagin|examen|ccf|protocole|referentiel|dnb|brevet", p_norm)

    def _ajouter_par_mots(nom_base, etiquette="", maximum=3):
        nonlocal _erreur
        if len(_extraits) >= 10:
            return
        try:
            _passages = chercher_par_mots(recherche_mots, nom_base, search_prompt or prompt, maximum)
        except Exception as e_mots:
            _erreur = str(e_mots)
            _diag.append(("Recherche par mots indisponible : " + nom_base, None))
            print(f"Erreur de recherche par mots dans {nom_base}: {e_mots}")
            return
        for _txt in _passages:
            if len(_extraits) >= 10:
                break
            _cle = passage_key(_txt)
            if _cle in _vus or _autre_examen(_txt):
                continue
            if _college_hors_examen and re.search(r"cyclades|santorin|imag.?in", normaliser(_txt[:500])):
                continue
            _vus.add(_cle)
            _bloc = (etiquette + " " if etiquette else "") + _txt
            _provenance_id = re.search(r"\[DOCUMENT: ([^;]+);", _txt)
            _extraits.append(mark_excerpt(_bloc, path=_provenance_id.group(1) if _provenance_id else '',
                url=_url_source(_provenance_id.group(1) if _provenance_id else '', _txt, prompt),
                title=next((line.lstrip('# ').strip() for line in _txt.splitlines()
                            if line.strip() and not line.startswith(('[DOCUMENT:', '[PORTEE:'))), ''))
                             if mode in ("examens", "ipack", "textes") else _bloc)
            _provenance = re.search(r"\[DOCUMENT: ([^;]+);", _txt)
            if _provenance:
                _sources.append((_provenance.group(1), None))
            _diag.append(("[mots] " + (etiquette + " " if etiquette else "") + _txt.strip().split("\n")[0][:100], None))

    def _ajouter(retriever, etiquette="", avec_sources=False, avec_diag=False, maximum=None):
        nonlocal _erreur
        if not retriever or len(_extraits) >= 10:
            return
        try:
            _nodes = retriever.retrieve(search_prompt or prompt)
        except Exception as e_retriever:
            _erreur = str(e_retriever)
            # Une base indisponible ne doit pas bloquer les autres bases.
            _diag.append(("Recherche indisponible : " + etiquette, None))
            print(f"Erreur de recherche dans {etiquette}: {e_retriever}")
            return
        _retenus = 0
        for n in _nodes:
            if len(_extraits) >= 10:
                break
            _txt = n.node.text or ""
            _cle = passage_key(_txt)
            if _cle in _vus:
                continue  # même passage présent dans deux bases : transmis une seule fois
            if incompatible(_txt, _cibles, n.node.metadata) or _autre_examen(_txt):
                continue  # réponse rédigée pour un autre examen que celui de la question
            if _college_hors_examen and re.search(r"cyclades|santorin|imag.?in", normaliser(_txt[:500])):
                continue  # question de collège sans rapport avec les examens : pas de fiche Cyclades / Santorin
            _vus.add(_cle)
            _retenus += 1
            _bloc = (etiquette + " " if etiquette else "") + _txt
            _extraits.append(mark_excerpt(_bloc,
                path=n.node.metadata.get('path', n.node.metadata.get('source', '')),
                url=_url_source(n.node.metadata.get('path', n.node.metadata.get('source', '')), _txt, prompt),
                title=n.node.metadata.get('title', ''), scopes=n.node.metadata.get('examens', [])) if mode in ("examens", "ipack", "textes") else _bloc)
            if avec_sources:
                _sources.append((libelle_source(n, prompt), getattr(n, "score", None)))
            if avec_diag:
                _diag.append(((etiquette + " " if etiquette else "") + _txt.strip().split("\n")[0][:110], getattr(n, "score", None)))
            if maximum and _retenus >= maximum:
                break

    try:
        for _path, _md in reference_notice(_cibles, search_prompt or prompt, niveau_actuel_form):
            if _md.get('modes') and mode not in _md['modes']:
                continue
            if len(_extraits) >= 10:
                break
            with open(_path, encoding='utf-8') as _f:
                _txt = _f.read()
            _cle = passage_key(_txt)
            if _cle in _vus:
                continue
            _vus.add(_cle)
            _bloc = '[FICHE PRIORITAIRE — statut: ' + _md.get('statut', '') + '] ' + _txt
            _extraits.append(mark_excerpt(_bloc, path=_path, title=_md.get('title', ''), priority=_md.get('priorite', 0), url=(reference_url(_md, prompt) or _url_source(_path, _txt, prompt)), selection='catalogue', scopes=_md.get('examens', []))
                             if mode in ("examens", "ipack", "textes") else _bloc)
            _priorites_fiches.append(_md.get('priorite', 0))
            _url = reference_url(_md, prompt)
            _sources.append((_md.get('title', _path) + (' — ' + _url if _url else ''), None))
            _diag.append(('[prioritaire] ' + _md.get('title', _path), None))
            # Une demande explicitement hors périmètre ne doit pas recevoir
            # une procédure voisine qui réalise l'action dans l'autre sens.
            if any(re.search(m, p_norm) for m in _md.get('exclusif_motifs', [])):
                # L'exclusivité arrête la recherche complémentaire ; elle conserve
                # les fiches spécifiques déjà sélectionnées et leurs conditions.
                _indices = [len(_extraits) - 1]
                if mode in ("examens", "ipack", "textes"):
                    _indices = [i for i, priority in enumerate(_priorites_fiches[:-1])
                                if priority >= 300 and priority > _md.get('priorite', 0)] + _indices
                return ("\n\n".join(_extraits[i] for i in _indices),
                        [_sources[i] for i in _indices], [_diag[i] for i in _indices], '')
        if mode in ('ipack', 'examens') and re.search(r'inapt|dispens|absen|reglement|dnb|brevet|ccf', p_norm):
            _ajouter(retriever_textes, '[Cadre réglementaire]', avec_sources=True, maximum=4)
        if niveau_actuel_form == "1er degré":
            _ajouter(retriever_textes, "[Référentiel Textes Officiels 1er Degré]", avec_sources=True)
            _ajouter(retriever_peda, "[Référentiel Pédagogique 1er Degré]", avec_sources=True)
        elif mode == "textes":
            _ajouter(retriever_textes, "[Textes Officiels & Juridiques / Partenariats]", avec_sources=True)
            if any(w in p_low for w in mots_cles_intention_peda):
                _ajouter(retriever_peda, "[Référentiel Pédagogique]", avec_sources=True)
        elif mode == "examens":
            _ajouter_par_mots("santorin", maximum=3)
            _ajouter_par_mots("ipack", "[Base iPackEPS]", maximum=2)
            _ajouter(retriever_santorin, avec_sources=True, avec_diag=True, maximum=8)
            # ✅ AJOUT : beaucoup de fiches Santorin / Cyclades sont rangées dans ipack.txt (livret Santorin, FAQ examens,
            # cas d'élèves : arrivée en cours d'année, 2 notes sur 3, haut niveau...). Depuis l'onglet Examens elles étaient
            # introuvables : l'IA inventait alors des menus ou restait dans le vague. On va aussi les chercher, à parts égales.
            _ajouter(retriever_ipack, "[Base iPackEPS]", avec_sources=True, avec_diag=True, maximum=8)
        elif mode == "ipack":
            _ajouter_par_mots("ipack", maximum=3)
            _ajouter(retriever_ipack, avec_sources=True, avec_diag=True)
            if not _college_hors_examen:
                _ajouter_par_mots("santorin", "[Base Examens & Santorin]", maximum=2)
                _ajouter(retriever_santorin, "[Base Examens & Santorin]", avec_sources=True, avec_diag=True, maximum=4)
        else:
            _ajouter(retriever_peda, "[Référentiel Pédagogique & Programmes]")
    except Exception as e_rag:
        # ✅ CORRECTION : l'erreur était avalée en silence ; l'IA recevait alors un contexte vide et répondait
        # « je ne dispose pas de la procédure ». Elle est maintenant notée (visible en mode admin et dans les journaux).
        _erreur = str(e_rag)
        _diag.append(("Recherche complémentaire interrompue", None))
        print(f"Erreur de recherche documentaire : {_erreur}")
    return ("".join(e + "\n\n" for e in _extraits), _sources, _diag, _erreur if not _extraits else "")
