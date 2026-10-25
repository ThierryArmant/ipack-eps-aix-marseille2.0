"""Outil d'audit privé réservé à une session administrateur Streamlit.

Diagnostic documentaire uniquement. Aucun appel IA ni journalisation des questions.
"""
import csv
import io
from collections import Counter

def _key(value):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', str(value or '').strip().lower())
                   if unicodedata.category(c) != 'Mn').replace('_', ' ')


MAX_CSV_BYTES = 50_000_000


def parse_csv(data, default_mode=None, default_public=None):
    """Accepter les exports avec traces et convertir toute erreur CSV pour l'interface."""
    if csv.field_size_limit() < MAX_CSV_BYTES:
        csv.field_size_limit(MAX_CSV_BYTES)
    try:
        return _parse_csv(data, default_mode, default_public)
    except csv.Error:
        raise ValueError("CSV illisible : vérifiez le séparateur et les guillemets, puis réexportez le tableau en CSV UTF-8.") from None


def _parse_csv(data, default_mode=None, default_public=None):
    """Reconnaît le tableau sans inventer le public ou le contexte manquants."""
    if len(data) > MAX_CSV_BYTES:
        raise ValueError("Fichier trop volumineux (maximum 50 Mo).")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Le CSV doit être encodé en UTF-8 (export CSV UTF-8 du tableur).") from exc
    if not text.strip():
        raise ValueError("Le fichier est vide.")
    try:
        dialect = csv.Sniffer().sniff(text[:20000], delimiters=";,\t")
        reader = csv.DictReader(io.StringIO(text), dialect=dialect, strict=True)
    except csv.Error:
        reader = csv.DictReader(io.StringIO(text), delimiter=";", strict=True)
    aliases = {'n': 'n', 'id': 'n', 'numero': 'n', 'question': 'question',
               'questions': 'question', 'demande': 'question', 'mode': 'mode',
               'contexte': 'mode', 'onglet': 'mode', 'public': 'public',
               'niveau': 'public', 'public cible': 'public', 'academie': 'academie',
               'academy': 'academie', 'verdict': 'verdict'}
    columns = {}
    for heading in reader.fieldnames or []:
        canonical = aliases.get(_key(heading))
        if canonical:
            if canonical in columns:
                raise ValueError(f"Deux colonnes désignent {canonical} : conservez une seule colonne pour ce champ.")
            columns[canonical] = heading
    if 'question' not in columns:
        raise ValueError("Colonne question introuvable : nommez-la Question, Questions ou Demande.")
    modes = {'ipack': 'ipack', 'ipackeps': 'ipack', 'assistance technique ipackeps': 'ipack',
             'examens': 'examens', 'examen': 'examens', 'examens & santorin': 'examens',
             'texte': 'textes', 'textes': 'textes', 'texte officiel': 'textes', 'textes officiels': 'textes',
             'securite & responsabilite juridique (textes officiels)': 'textes'}
    publics = {'college': 'Collège (DNB)', 'college (dnb)': 'Collège (DNB)',
               'college dnb': 'Collège (DNB)', '1er degre': '1er degré', 'premier degre': '1er degré',
               'lycee voie generale': 'Lycée Général & Techno', 'lycee general & techno': 'Lycée Général & Techno',
               'lycee general et technologique': 'Lycée Général & Techno',
               'lycee voie professionnelle': 'Lycée Pro / CAP', 'lycee pro / cap': 'Lycée Pro / CAP'}
    rows, ids = [], set()
    for line, raw in enumerate(reader, 2):
        if not any(str(v or '').strip() for k, v in raw.items() if k is not None):
            continue
        if None in raw:
            raise ValueError(f"Ligne {line} : trop de cellules ; vérifiez le séparateur et les guillemets.")
        row = {k: str(raw.get(h) or '').strip() for k, h in columns.items()}
        if not row.get('question'):
            raise ValueError(f"Ligne {line} : la question est vide.")
        ident = row.get('n') or str(len(rows) + 1)
        if ident in ids:
            raise ValueError(f"Ligne {line} : identifiant en doublon ({ident}).")
        ids.add(ident)
        mode = _key(row.get('mode') or default_mode).replace('l’onglet ', '').replace("l'onglet ", '')
        public = _key(row.get('public') or default_public)
        if mode not in modes:
            value = row.get('mode') or '(vide)'
            raise ValueError(f"Ligne {line} : Mode inconnu : {value!r}. Valeurs acceptées : ipack, examen(s), texte(s). Pour une cellule vide, choisissez le contexte commun ci-dessous.")
        if public not in publics:
            raise ValueError(f"Ligne {line} : public absent ou non reconnu. Indiquez le niveau ou choisissez le public commun ci-dessous.")
        rows.append(dict(row, n=ident, mode=modes[mode], public=publics[public],
                         academie=row.get('academie', ''), verdict=row.get('verdict', '')))
    if not rows:
        raise ValueError("Le tableau ne contient aucune question.")
    return rows


def import_defaults(st, key):
    with st.expander("Si le fichier ne précise pas le contexte ou le public", expanded=False):
        mode = st.selectbox("Contexte commun aux lignes non renseignées",
                            [None, 'ipack', 'examens', 'textes'],
                            format_func=lambda x: {None: 'À préciser dans le fichier', 'ipack': 'iPackEPS', 'examens': 'Examens', 'textes': 'Textes'}[x], key=key+'_mode')
        public = st.selectbox("Public commun aux lignes non renseignées",
                              [None, '1er degré', 'Collège (DNB)', 'Lycée Général & Techno', 'Lycée Pro / CAP'],
                              format_func=lambda x: x or 'À préciser dans le fichier', key=key+'_public')
    return mode, public


def render(st):
    if not st.session_state.get("is_admin", False):
        return
    with st.expander("🧪 Audit privé — préparation des questions", expanded=False):
        st.info("Diagnostic documentaire uniquement : aucun appel IA. Les réponses réelles ne sont pas encore rejouées.")
        uploaded = st.file_uploader("Tableau CSV privé des questions", type=["csv"], key="audit113_csv")
        if uploaded is None:
            return
        defaults = import_defaults(st, "audit_prepare_defaults")
        try:
            rows = parse_csv(uploaded.getvalue(), *defaults)
        except ValueError as exc:
            st.error(str(exc))
            return
        counts = Counter(r["mode"].strip().lower() for r in rows)
        st.success(f"Fichier validé : {len(rows)} questions · iPackEPS {counts['ipack']} · Examens {counts['examens']} · Textes {counts['textes']}")
        st.caption("Les questions ne sont ni affichées ni enregistrées dans GitHub ou dans les journaux.")
        if st.button("Contrôler le routage documentaire (sans IA)", key="audit113_run"):
            st.session_state.pop("audit113_output", None)
            import knowledge_catalog as kc
            result = []
            bar = st.progress(0)
            for i, row in enumerate(rows):
                try:
                    titles = kc.priority_titles(row["question"], row["public"], row["mode"])
                    status = "ok"
                except Exception as exc:
                    titles, status = [], type(exc).__name__
                result.append({"n": row["n"], "mode": row["mode"], "public": row["public"],
                               "routage": status, "fiches": " | ".join(titles)})
                bar.progress((i + 1) / len(rows))
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(result[0]), delimiter=";")
            writer.writeheader()
            writer.writerows(result)
            st.session_state["audit113_output"] = output.getvalue().encode("utf-8-sig")
        if st.session_state.get("audit113_output"):
            st.download_button("Télécharger le diagnostic", data=st.session_state["audit113_output"],
                               file_name="audit_113_routage.csv", mime="text/csv", key="audit113_download")
            st.warning("Aucune réponse IA rejouée : ce diagnostic ne mesure pas la qualité des réponses.")
