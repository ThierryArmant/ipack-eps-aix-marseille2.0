"""Retest privé par lots, utilisant le traitement normal du HUB via current_prompt."""
import csv
import io
import json

def render(st):
    if not st.session_state.get("is_admin", False):
        return
    state = st.session_state
    batch = state.get("audit113_batch")
    if batch and batch.get("waiting"):
        messages = state.get("messages_hub", [])
        message = next((m for m in reversed(messages)
                        if m.get("role") == "assistant" and m.get("type") == "text"), {})
        answer = message.get("content", "")
        if answer:
            row = batch["rows"][batch["index"]]
            batch["results"].append({"n": row["n"], "mode": row["mode"],
                                     "public": row["public"], "academie": row.get("academie", ""),
                                     "question": row["question"], "nouvelle_reponse": answer,
                                     "version": message.get("version", ""),
                                     "usage_ia": message.get("usage_ia") or {},
                                     "diagnostic_ia": message.get("diagnostic_ia") or {}})
            batch["index"] += 1
            batch["waiting"] = False
    st.markdown("""<style>.st-key-admin_retest_opaque{background:#fff!important;color:#14263d!important;border:2px solid #17365d!important;border-radius:14px;padding:20px!important}.st-key-admin_retest_opaque p,.st-key-admin_retest_opaque label{color:#14263d!important}.st-key-admin_retest_opaque [data-testid="stAlert"]{background:#eaf2fc!important;opacity:1!important}.st-key-admin_retest_opaque [data-testid="stFileUploader"]{background:#f1f5fb!important;opacity:1!important}.st-key-admin_retest_opaque button{background:#17365d!important;color:#fff!important;border:2px solid #17365d!important;opacity:1!important}.st-key-admin_retest_opaque button p,.st-key-admin_retest_opaque button span{color:#fff!important;font-weight:700!important}.st-key-admin_retest_opaque button:hover{background:#245b94!important}</style>""",unsafe_allow_html=True)
    st.markdown("""<div style="background:#17365d;color:#fff;border:3px solid #f6b73c;border-radius:12px;padding:16px 20px;margin:18px 0 8px 0;font-size:22px;font-weight:800">🧪 ADMINISTRATION — TESTS IA DU HUB<br><span style="font-size:15px;font-weight:500">Outil réservé à l’administrateur • nombre de questions au choix</span></div>""", unsafe_allow_html=True)
    with st.container(border=True, key="admin_retest_opaque"):
        st.info("⬇️ IMPORTER LE FICHIER CSV, PUIS LANCER LES TESTS CI-DESSOUS")
        st.warning("Les tests utilisent la clé IA du HUB et peuvent être facturés. "
                   "Les résultats restent dans cette session et sont à télécharger avant de la quitter.")
        uploaded = st.file_uploader("Tableau CSV privé des questions", type=["csv"], key="audit113_live_csv")
        if batch:
            st.write(f"Réponses obtenues : {len(batch['results'])}/{len(batch['rows'])}")
            if batch["results"]:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["n","mode","public","academie","question","nouvelle_reponse","version","usage_ia","diagnostic_ia"], delimiter=";")
                writer.writeheader()
                for result in batch["results"]:
                    writer.writerow({**result, "usage_ia": json.dumps(result.get("usage_ia", {}), ensure_ascii=False),
                                     "diagnostic_ia": json.dumps(result.get("diagnostic_ia", {}), ensure_ascii=False)})
                st.download_button("Télécharger les réponses obtenues", output.getvalue().encode("utf-8-sig"),
                                   file_name="retest_113_reponses_privees.csv", mime="text/csv")
            if st.button("🔄 Nouveau test — choisir nombre de questions au choix", key="audit113_reset", type="primary"):
                state.pop("audit113_batch", None)
                state.pop("current_prompt", None)
                st.rerun()
            if st.button("Arrêter après la question en cours", key="audit113_stop"):
                batch["stopped"] = True
            if not batch["waiting"] and not batch.get("stopped") and batch["index"] < len(batch["rows"]):
                row = batch["rows"][batch["index"]]
                if batch["results"] and batch["results"][-1].get("usage_ia", {}).get("fallback_used"):
                    batch["stopped"] = True
                    st.warning("Secours payant utilisé : lot suspendu pour conserver la mesure du fournisseur principal. Téléchargez les réponses obtenues.")
                    return
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
        from admin_retest_113 import parse_csv, import_defaults
        defaults = import_defaults(st, "audit_live_defaults")
        try:
            rows = parse_csv(uploaded.getvalue(), *defaults)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success(f"{len(rows)} questions reconnues. Vous choisissez combien en rejouer.")
        start = int(st.number_input("Commencer à la question", min_value=1, max_value=len(rows), value=1, step=1))
        remaining = len(rows) - start + 1
        n = int(st.number_input("Nombre de questions à rejouer", min_value=1, max_value=remaining,
                                value=min(5, remaining), step=1))
        st.caption(f"Questions {start} à {start + n - 1} sur {len(rows)} ; aucune autre ligne ne sera rejouée.")
        st.caption("Les réponses ne sont pas évaluées automatiquement : téléchargement pour vérification humaine.")
        if st.button(f"Lancer {n} questions dans le moteur réel du HUB", type="primary", key="audit113_live_start"):
            state["audit113_batch"] = {"rows": rows[start-1:start-1+n], "index": 0, "results": [],
                                       "waiting": False, "stopped": False}
            st.rerun()
