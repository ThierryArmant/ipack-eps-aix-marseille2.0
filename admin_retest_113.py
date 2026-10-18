"""Outil d'audit privé réservé à une session administrateur Streamlit.

Diagnostic documentaire uniquement. Aucun appel IA ni journalisation des questions.
"""
import csv
import io
from collections import Counter

def parse_csv(data):
    if len(data) > 2_000_000:
        raise ValueError("Fichier trop volumineux (maximum 2 Mo).")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Le CSV doit être encodé en UTF-8.") from exc
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    needed = {"n", "question", "mode", "public", "verdict"}
    if not needed.issubset(set(reader.fieldnames or [])):
        raise ValueError("Colonnes requises : n, question, mode, public, verdict.")
    rows = list(reader)
    if len(rows) != 113:
        raise ValueError(f"113 questions attendues ; {len(rows)} trouvées.")
    ids = [str(r["n"]).strip() for r in rows]
    if not all(ids) or len(set(ids)) != 113:
        raise ValueError("Identifiants vides ou en doublon.")
    if any(not r["question"].strip() for r in rows):
        raise ValueError("Une question est vide.")
    if any(r["mode"].strip().lower() not in {"ipack", "examens", "textes"} for r in rows):
        raise ValueError("Mode inconnu.")
    return rows

def render(st):
    if not st.session_state.get("is_admin", False):
        return
    with st.expander("🧪 Audit privé — 113 questions (préparation)", expanded=False):
        st.info("Diagnostic documentaire uniquement : aucun appel IA. Les réponses réelles ne sont pas encore rejouées.")
        uploaded = st.file_uploader("CSV historique privé des 113 questions", type=["csv"], key="audit113_csv")
        if uploaded is None:
            return
        try:
            rows = parse_csv(uploaded.getvalue())
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
            st.warning("0/113 réponses IA rejouées : ce diagnostic ne mesure pas la qualité des réponses.")
