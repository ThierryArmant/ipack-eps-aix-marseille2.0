import streamlit as st
import requests
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

# 1. CONFIGURATION
st.set_page_config(page_title="Expert iPackEPS", layout="wide")

# 2. DESIGN
st.markdown("""
    <style>
    .hub-header { background-color: #1E293B; padding: 20px; border-radius: 12px; color: white; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="hub-header"><h1>Expert Support iPackEPS</h1></div>', unsafe_allow_html=True)

if "messages_hub" not in st.session_state: st.session_state.messages_hub = []

# 3. LOGIQUE "EXÉCUTEUR STRICT"
prompt = st.chat_input("Quelle procédure cherchez-vous ?")

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": prompt})
    
    with st.spinner("Extraction des étapes..."):
        try:
            # Query ultra-ciblée sur les étapes techniques
            query_technique = f"{prompt} mode d'emploi clic bouton étape par étape site:ipackeps.ac-creteil.fr"
            
            res = requests.post("https://api.tavily.com/search", json={
                "api_key": st.secrets["TAVILY_API_KEY"],
                "query": query_technique,
                "include_domains": ["ipackeps.ac-creteil.fr"],
                "search_depth": "advanced",
                "include_raw_content": True 
            })
            
            raw_data = "\n".join([r.get('raw_content', r.get('content', '')) for r in res.json().get("results", [])])
            
            # SYSTEM EXPERT "EXÉCUTEUR"
            # C'est ici que l'on empêche le résumé
            system_expert = """
            Tu es l'expert technique d'iPackEPS.
            MISSION : Guider l'utilisateur pour réaliser UNE action spécifique sans aucune fioriture.
            
            RÈGLES D'OR :
            1. AUCUN RÉSUMÉ : Interdiction formelle de faire des phrases d'introduction ou de conclure.
            2. FOCUS ACTIONS : Si l'utilisateur demande une procédure, liste les clics et menus uniquement.
            3. FORMATAGE STRICT : 
               - Étape 1 : [Chemin dans le menu]
               - Étape 2 : [Clic bouton/onglet précis]
               - Étape 3 : [Action finale de validation]
            4. LIENS : Si la procédure est dans un sous-tutoriel, écris : "Consultez le lien : [URL] pour les étapes détaillées."
            5. EXCLUSION : Ne mentionne jamais le Bac, l'UNSS, ou les circulaires administratives.
            """
            
            Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0, max_tokens=1500, api_key=st.secrets["OPENAI_API_KEY"])
            
            response = Settings.llm.complete(system_expert + "\n\nContenu technique extrait : " + raw_data + "\n\nQuestion utilisateur : " + prompt)
            
            st.session_state.messages_hub.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"Erreur : {str(e)}"})
    st.rerun()

# 4. AFFICHAGE
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        st.markdown(m["content"])
