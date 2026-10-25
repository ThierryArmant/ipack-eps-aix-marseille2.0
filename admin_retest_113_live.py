"""Retest privé par lots, utilisant le traitement normal du HUB via current_prompt."""
import csv
import io
import json

def provider_for_replay(state, configured):
    batch = state.get('audit113_batch') or {}
    return 'openai' if (state.get('is_admin') and batch.get('waiting')
                        and batch.get('provider') == 'openai') else configured


def _replay_row(state):
    batch = state.get('audit113_batch') or {}
    if not state.get('is_admin') or not batch.get('waiting'):
        return None
    index = batch.get('index')
    rows = batch.get('rows') or []
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(rows):
        return None
    return rows[index]


def is_replay_question(state):
    return _replay_row(state) is not None


def academy_context_for_replay(state, configured, notice=''):
    """Une ligne rejouée ne dépend jamais de l'académie mémorisée par l'interface."""
    from academie import ACADEMIES, NON_PRECISEE, academy_context
    row = _replay_row(state)
    if row is None:
        return configured, notice
    selected = str(row.get('academie') or '').strip()
    selected = selected if selected in ACADEMIES + [NON_PRECISEE] else NON_PRECISEE
    question = row.get('question', '')
    effective, message = academy_context(question, selected)
    if effective != selected:
        return effective, message
    # Deux formulations de périmètre rencontrées dans les CSV : intitulé initial
    # « Cyclades Académie session : ... » et question terminée par « à Académie ? ».
    # Une simple citation de guide/tutoriel d'une académie ne suffit pas.
    import re
    import unicodedata
    def norm(text):
        return ''.join(c for c in unicodedata.normalize('NFKD', text.lower())
                       if not unicodedata.combining(c)).replace('’', "'").replace('-', ' ')
    q = norm(question)
    declared = []
    for name in ACADEMIES:
        if name in ('Autre', "Établissement français à l'étranger"):
            continue
        place = re.escape(norm(name)).replace(r'\ ', r'\s+')
        if (re.search(r'^(?:(?:cyclades|santorin|ipackeps)\s+)?' + place + r'(?:\s+20\d{2})?\s*[:—]', q)
                or re.search(r"\b(?:a|dans l'academie de|pour l'academie de)\s+" + place + r'\s*[?!.]?\s*$', q)
                or re.search(r"\ba\s+" + place + r'(?=\s*[,;:]|\s+et\b)', q)):
            declared.append(name)
    if len(declared) == 1:
        effective = declared[0]
        message = (f"Ligne CSV : {selected} ; question : {effective}. La réponse utilise {effective}.") if selected != NON_PRECISEE and effective != selected else ''
    return effective, message


def academy_for_replay(state, configured):
    return academy_context_for_replay(state, configured)[0]


def replay_academy_details(state):
    row = _replay_row(state)
    if row is None:
        return {}
    from academie import ACADEMIES, NON_PRECISEE
    effective, _ = academy_context_for_replay(state, NON_PRECISEE)
    raw = str(row.get('academie') or '').strip()
    base = raw if raw in ACADEMIES else NON_PRECISEE
    return {'academie_effective': effective,
            'academie_origine': ('question' if effective != base
                                 else 'csv' if raw in ACADEMIES else 'non_precisee')}


def select_replay_numbers(rows, value):
    """Sélectionner les identifiants n du CSV, dans l'ordre demandé, sans doublon."""
    import re
    tokens = str(value).split(',')
    if any(not re.fullmatch(r'[0-9]+', token.strip()) for token in tokens):
        raise ValueError('Saisissez des numéros séparés par des virgules, par exemple 3,5,8. Aucun élément vide ni intervalle.')
    requested = list(dict.fromkeys(str(int(token.strip())) for token in tokens))
    lookup = {}
    for row in rows:
        raw = str(row.get('n', '')).strip()
        if re.fullmatch(r'[0-9]+', raw):
            number = str(int(raw))
            if number in lookup:
                raise ValueError(f'Numéro ambigu dans le CSV : {number}. Corrigez les identifiants avant le rejeu.')
            lookup[number] = row
    missing = [number for number in requested if number not in lookup]
    if missing:
        raise ValueError('Numéros absents du CSV : ' + ', '.join(missing))
    return [lookup[number] for number in requested]



COMPARISON_COLUMNS = ["reponse_mini", "reponse_albert", "modele_mini", "modele_albert",
                      "usage_mini", "usage_albert", "erreur_mini", "erreur_albert"]


def comparison_step(state, runner, version):
    """Une question par rafraîchissement ; jamais de relance payante après interruption."""
    batch = state.get('audit113_batch') or {}
    if (not state.get('is_admin') or batch.get('comparison') != 'mini_albert'
            or batch.get('stopped') or batch['index'] >= len(batch['rows'])):
        return False
    if batch.get('version') and batch['version'] != version:
        batch['stopped'] = True
        batch['stop_reason'] = 'Version modifiée pendant le lot : arrêt pour ne pas mélanger les versions.'
        return False
    batch['version'] = version
    row = batch['rows'][batch['index']]
    # Le marqueur reste présent si Streamlit interrompt le traitement : ne pas refacturer la ligne.
    interrupted = batch.get('comparison_inflight') is not None
    batch['comparison_inflight'] = batch['index']
    academy, _ = academy_context_for_replay(dict(is_admin=True, audit113_batch=dict(
        waiting=True, index=0, rows=[row])), 'Non précisée')
    try:
        if interrupted:
            raise RuntimeError('Traitement interrompu ; aucune relance automatique.')
        result = runner(row, academy)
    except Exception:
        result = dict(version=version, branches={name:dict(error=(
            'Traitement interrompu ; aucune relance automatique.' if interrupted else
            'Comparaison interrompue ; consulter les journaux techniques.'), usage={}) for name in ('Mini','Albert')})
    mini = result['branches'].get('Mini', {})
    albert = result['branches'].get('Albert', {})
    record = dict(n=row['n'], mode=row['mode'], public=row['public'], academie=row.get('academie',''),
                  academie_effective=academy, question=row['question'], version=version,
                  nouvelle_reponse=mini.get('answer',''), usage_ia=mini.get('usage',{}),
                  diagnostic_ia=json.dumps(result, ensure_ascii=False, separators=(',',':')),
                  videos='')
    for name, item in [('mini',mini),('albert',albert)]:
        record['reponse_'+name] = item.get('answer','')
        record['modele_'+name] = item.get('model','')
        record['usage_'+name] = json.dumps(item.get('usage',{}), ensure_ascii=False)
        record['erreur_'+name] = item.get('error','')
    batch['results'].append(record)
    batch['index'] += 1
    batch.pop('comparison_inflight',None)
    return True


def render(st):
    if not st.session_state.get("is_admin", False):
        return
    state = st.session_state
    batch = state.get("audit113_batch")
    if batch and batch.get("waiting") and batch.get("comparison") != "mini_albert":
        messages = state.get("messages_hub", [])
        message = next((m for m in reversed(messages)
                        if m.get("role") == "assistant" and m.get("type") == "text"), {})
        answer = message.get("content", "")
        if answer:
            row = batch["rows"][batch["index"]]
            batch["results"].append({"n": row["n"], "mode": row["mode"],
                                     "public": row["public"], "academie": row.get("academie", ""),
                                     "question": row["question"], "nouvelle_reponse": answer,
                                     **replay_academy_details(state),
                                     "version": message.get("version", ""),
                                     "usage_ia": message.get("usage_ia") or {},
                                     # Trace conservée en texte compact : bien plus légère en mémoire qu'un dictionnaire.
                                     "diagnostic_ia": json.dumps(message.get("diagnostic_ia") or {}, ensure_ascii=False),
                                     # Les vidéos sont des messages séparés : sans cette colonne, le CSV ne les montrait jamais.
                                     "videos": " ".join(m.get("content", "") for m in messages if m.get("type") == "video")})
            batch["index"] += 1
            batch["waiting"] = False
            batch.pop("retries", None)
        elif "current_prompt" not in state:
            # Traitement interrompu (clic, rafraîchissement, coupure) : la question n'a rien produit
            # et ne sera jamais traitée. Une relance, puis la ligne est notée bloquée et le lot continue.
            row = batch["rows"][batch["index"]]
            if batch.get("retries", 0) < 1:
                batch["retries"] = batch.get("retries", 0) + 1
                batch["waiting"] = False
            else:
                batch["results"].append({"n": row["n"], "mode": row["mode"], "public": row["public"],
                                         "academie": row.get("academie", ""), "question": row["question"],
                                         "nouvelle_reponse": "[BLOQUÉE : traitement interrompu deux fois, aucune réponse]",
                                         **replay_academy_details(state), "version": "", "usage_ia": {},
                                         "diagnostic_ia": "{}"})
                batch["index"] += 1
                batch["waiting"] = False
                batch.pop("retries", None)
    st.markdown("""<style>.st-key-admin_retest_opaque{background:#fff!important;color:#14263d!important;border:2px solid #17365d!important;border-radius:14px;padding:20px!important}.st-key-admin_retest_opaque p,.st-key-admin_retest_opaque label{color:#14263d!important}.st-key-admin_retest_opaque [data-testid="stAlert"]{background:#eaf2fc!important;opacity:1!important}.st-key-admin_retest_opaque [data-testid="stFileUploader"]{background:#f1f5fb!important;opacity:1!important}.st-key-admin_retest_opaque button{background:#17365d!important;color:#fff!important;border:2px solid #17365d!important;opacity:1!important}.st-key-admin_retest_opaque button p,.st-key-admin_retest_opaque button span{color:#fff!important;font-weight:700!important}.st-key-admin_retest_opaque button:hover{background:#245b94!important}</style>""",unsafe_allow_html=True)
    st.markdown("""<div style="background:#17365d;color:#fff;border:3px solid #f6b73c;border-radius:12px;padding:16px 20px;margin:18px 0 8px 0;font-size:22px;font-weight:800">🧪 ADMINISTRATION — TESTS IA DU HUB<br><span style="font-size:15px;font-weight:500">Outil réservé à l’administrateur • nombre de questions au choix</span></div>""", unsafe_allow_html=True)
    with st.container(border=True, key="admin_retest_opaque"):
        st.info("⬇️ IMPORTER LE FICHIER CSV, PUIS LANCER LES TESTS CI-DESSOUS")
        st.warning("Les tests utilisent la clé IA du HUB et peuvent être facturés. "
                   "Les réponses sont envoyées au journal Google Sheets. Le CSV avec les traces reste à télécharger avant de quitter cette session.")
        uploaded = st.file_uploader("Tableau CSV privé des questions", type=["csv"], key="audit113_live_csv")
        if batch:
            st.write(f"Réponses obtenues : {len(batch['results'])}/{len(batch['rows'])}")
            # Mémoire : le fichier (plusieurs Mo) n'est fabriqué qu'une fois le lot terminé, ou sur demande ;
            # le recréer à chaque rafraîchissement pendant le lot accumulait des copies en mémoire.
            finished = batch["index"] >= len(batch["rows"])
            partial = (not finished and batch["results"]
                       and st.button("Préparer un fichier des réponses déjà obtenues", key="audit113_partial"))
            if partial:
                batch["stopped"] = True
                batch["stop_reason"] = "Lot mis en pause pour sauvegarder les résultats déjà obtenus."
            if batch["results"] and (finished or partial or batch.get("stopped")):
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["n","mode","public","academie","question","nouvelle_reponse","version","usage_ia","diagnostic_ia","academie_effective","academie_origine","videos"] + (COMPARISON_COLUMNS if batch.get("comparison") == "mini_albert" else []), delimiter=";", extrasaction="ignore")
                writer.writeheader()
                for result in batch["results"]:
                    writer.writerow({**result, "usage_ia": json.dumps(result.get("usage_ia", {}), ensure_ascii=False),
                                     "diagnostic_ia": (result["diagnostic_ia"] if isinstance(result.get("diagnostic_ia"), str)
                                                       else json.dumps(result.get("diagnostic_ia", {}), ensure_ascii=False))})
                st.download_button("Télécharger les réponses obtenues", output.getvalue().encode("utf-8-sig"),
                                   file_name="retest_113_reponses_privees.csv", mime="text/csv")
            if st.button("🔄 Nouveau test — choisir nombre de questions au choix", key="audit113_reset", type="primary"):
                state.pop("audit113_batch", None)
                state.pop("current_prompt", None)
                st.rerun()
            if st.button("Arrêter après la question en cours", key="audit113_stop"):
                batch["stopped"] = True
                st.rerun()
            if batch.get("comparison") == "mini_albert":
                st.caption("Comparatif Mini / Albert : mêmes documents, réponses et traces séparées. Aucun envoi au journal Google Sheets par ce parcours.")
                if batch.get("stop_reason"):
                    st.warning(batch["stop_reason"])
                return
            if not batch["waiting"] and not batch.get("stopped") and batch["index"] < len(batch["rows"]):
                row = batch["rows"][batch["index"]]
                if batch["results"] and batch["results"][-1].get("usage_ia", {}).get("fallback_used"):
                    batch["stopped"] = True
                    st.warning("Secours payant utilisé : lot suspendu pour conserver la mesure du fournisseur principal. Téléchargez les réponses obtenues.")
                    return
                state["active_module"] = row["mode"].strip().lower()
                state["niveau_actif_form"] = row["public"]
                # « Tous publics » est une case de l'onglet Textes : remise à zéro à chaque ligne.
                state["textes_tous_publics"] = row["public"] == "Tous publics"
                academy = (row.get("academie") or "").strip()
                from academie import ACADEMIES
                state["academie_utilisateur"] = academy if academy in ACADEMIES else None
                state["current_prompt"] = row["question"]
                state["messages_hub"] = []
                batch["waiting"] = True
                # Le traitement normal s'exécute plus bas dans app.py, puis st.rerun().
            return
        if uploaded is None:
            return
        from admin_csv_loader import load_csv_import
        csv_import = load_csv_import()
        parse_csv, import_defaults = csv_import.parse_csv, csv_import.import_defaults
        defaults = import_defaults(st, "audit_live_defaults")
        try:
            rows = parse_csv(uploaded.getvalue(), *defaults)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success(f"{len(rows)} questions reconnues. Vous choisissez combien en rejouer.")
        numbers = st.text_input("Numéros des questions séparés par des virgules (facultatif)",
                                key="audit113_question_numbers", placeholder="3,5,8,19,26,30,40,41,44,49")
        st.caption("Utilise la colonne n du CSV, dans l'ordre saisi, sans rejouer les doublons. Laisser vide pour une plage consécutive.")
        if numbers.strip():
            try:
                selected_rows = select_replay_numbers(rows, numbers)
            except ValueError as exc:
                st.error(str(exc))
                return
            n = len(selected_rows)
            st.caption("Questions choisies : " + ", ".join(str(row['n']) for row in selected_rows))
        else:
            start = int(st.number_input("Commencer à la question", min_value=1, max_value=len(rows), value=1, step=1))
            remaining = len(rows) - start + 1
            n = int(st.number_input("Nombre de questions à rejouer", min_value=1, max_value=remaining,
                                    value=min(5, remaining), step=1))
            selected_rows = rows[start-1:start-1+n]
            st.caption(f"Questions {start} à {start + n - 1} sur {len(rows)} ; aucune autre ligne ne sera rejouée.")
        st.caption("Chaque question utilise son académie CSV ou celle déclarée dans la question ; une cellule vide reste Non précisée. Les réponses ne sont pas évaluées automatiquement.")
        comparison_choice = st.selectbox("Traitement du rejeu", ["Mini seul — moteur habituel du HUB", "Comparer Mini et Albert — mêmes documents"] , key="audit113_comparison_choice")
        compare = comparison_choice.startswith("Comparer")
        albert_model = ""
        if compare:
            st.warning("Comparaison documentée : au maximum 2 appels Mini + 2 appels Albert par question, hors recherche documentaire. 50 questions = au maximum 100 appels par modèle. Ce parcours compare les modèles et ne reproduit pas les réponses directes du moteur habituel.")
            albert_model = st.text_input("Modèle Albert du lot", value=st.secrets.get("ALBERT_MODEL") or "gpt-oss-120b", key="audit113_albert_model")
            if n > 50:
                st.error("Limitez le comparatif à 50 questions par lot.")
                return
            if not st.secrets.get("ALBERT_API_KEY"):
                st.error("Clé ALBERT_API_KEY absente : aucun comparatif lancé.")
                return
            if not albert_model.strip():
                st.error("Indiquez le modèle Albert.")
                return
        else:
            st.caption("Rejeu en Mini seul (gpt-4o-mini) : aucun appel à Albert.")
        if st.button((f"Comparer {n} questions — Mini et Albert" if compare else f"Lancer {n} questions dans le moteur réel du HUB"), type="primary", key="audit113_live_start"):
            state["audit113_batch"] = {"rows": selected_rows, "index": 0, "results": [],
                                       "waiting": False, "stopped": False, "provider": "openai",
                                       "comparison": "mini_albert" if compare else None,
                                       "albert_model": albert_model.strip()}
            st.rerun()
