"""Retest privé par lots, utilisant le traitement normal du HUB via current_prompt."""
import csv
import io

def render(st):
    if not st.session_state.get("is_admin", False):
        return
    state = st.session_state
    batch = state.get("audit113_batch")
    if batch and batch.get("waiting"):
        messages = state.get("messages_hub", [])
        answer = next((m.get("content", "") for m in reversed(messages)
                       if m.get("role") == "assistant" and m.get("type") == "text"), "")
        if answer:
            row = batch["rows"][batch["index"]]
            batch["results"].append({"n": row["n"], "mode": row["mode"],
                                     "public": row["public"], "academie": row.get("academie", ""),
                                     "nouvelle_reponse": answer})
            batch["index"] += 1
            batch["waiting"] = False
    st.markdown("""<style>.st-key-admin_retest_opaque{background:#fff!important;color:#14263d!important;border:2px solid #17365d!important;border-radius:14px;padding:20px!important}.st-key-admin_retest_opaque p,.st-key-admin_retest_opaque label{color:#14263d!important}.st-key-admin_retest_opaque [data-testid="stAlert"]{background:#eaf2fc!important;opacity:1!important}.st-key-admin_retest_opaque [data-testid="stFileUploader"]{background:#f1f5fb!important;opacity:1!important}.st-key-admin_retest_opaque button{background:#17365d!important;color:#fff!important;border:2px solid #17365d!important;opacity:1!important}.st-key-admin_retest_opaque button p,.st-key-admin_retest_opaque button span{color:#fff!important;font-weight:700!important}.st-key-admin_retest_opaque button:hover{background:#245b94!important}</style>""",unsafe_allow_html=True)
    st.markdown("""<div style="background:#17365d;color:#fff;border:3px solid #f6b73c;border-radius:12px;padding:16px 20px;margin:18px 0 8px 0;font-size:22px;font-weight:800">🧪 ADMINISTRATION — TESTS IA DU HUB<br><span style="font-size:15px;font-weight:500">Outil réservé à l’administrateur • 5 ou 113 questions</span></div>""", unsafe_allow_html=True)
    with st.container(border=True, key="admin_retest_opaque"):
        st.info("⬇️ IMPORTER LE FICHIER CSV, PUIS LANCER LES TESTS CI-DESSOUS")
        st.warning("Les tests utilisent la clé IA du HUB et peuvent être facturés. "
                   "Les résultats restent dans cette session et sont à télécharger avant de la quitter.")
        uploaded = st.file_uploader("Fichier privé des 113 questions", type=["csv"], key="audit113_live_csv")
        if batch:
            st.write(f"Réponses obtenues : {len(batch['results'])}/{len(batch['rows'])}")
            if batch["results"]:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["n","mode","public","academie","nouvelle_reponse"], delimiter=";")
                writer.writeheader()
                writer.writerows(batch["results"])
                st.download_button("Télécharger les réponses obtenues", output.getvalue().encode("utf-8-sig"),
                                   file_name="retest_113_reponses_privees.csv", mime="text/csv")
            if st.button("🔄 Nouveau test — choisir 5 ou 113 questions", key="audit113_reset", type="primary"):
                state.pop("audit113_batch", None)
                state.pop("current_prompt", None)
                st.rerun()
            if st.button("Arrêter après la question en cours", key="audit113_stop"):
                batch["stopped"] = True
            if not batch["waiting"] and not batch.get("stopped") and batch["index"] < len(batch["rows"]):
                row = batch["rows"][batch["index"]]
                state["active_module"] = row["mode"].strip().lower()
                state["niveau_actif_form"] = row["public"]
                academy = (row.get("academie") or "").strip()
                state["academie_utilisateur"] = academy if academy and academy.lower() != "non précisée" else None
                state["current_prompt"] = row["question"]
                state["messages_hub"] = []
                batch["waiting"] = True
                # Le traitement normal s'exécute plus bas dans app.py, puis st.rerun().
            return
        if uploaded is None:
            return
        from admin_retest_113 import parse_csv
        try:
            rows = parse_csv(uploaded.getvalue())
        except ValueError as exc:
            st.error(str(exc))
            return
        n = st.radio("Nombre de questions", [5, 113], horizontal=True, key="audit113_live_n")
        st.caption("Les réponses ne sont pas évaluées automatiquement : téléchargement pour vérification humaine.")
        if st.button(f"Lancer {n} questions dans le moteur réel du HUB", type="primary", key="audit113_live_start"):
            state["audit113_batch"] = {"rows": rows[:n], "index": 0, "results": [],
                                       "waiting": False, "stopped": False}
            st.rerun()
