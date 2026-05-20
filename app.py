import streamlit as st
import requests
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

# 1. CONFIGURATION
st.set_page_config(page_title="Hub IA - iPackEPS", layout="wide")

# 2. DESIGN
st.markdown("""
    <style>
    .hub-header { background-color: #1E293B; padding: 20px; border-radius: 12px; color: white; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="hub-header"><h1>Expert Support iPackEPS</h1></div>', unsafe_allow_html=True)

if "messages_hub" not in st.session_state: st.session_state.messages_hub = []

# 3. MOTEUR DE RECHERCHE & ROUTAGE
prompt = st.chat_input("Quelle procédure cherchez-vous ? (ex: certificat médical, CAHPN, SSS...)")

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": prompt})
    
    with st.spinner("Analyse du module concerné et extraction..."):
        try:
            # Recherche ciblée sur le domaine
            query_technique = f"{prompt} site:ipackeps.ac-creteil.fr/spip.php?rubrique2 procédure tutoriel"
            
            res = requests.post("https://api.tavily.com/search", json={
                "api_key": st.secrets["TAVILY_API_KEY"],
                "query": query_technique,
                "include_domains": ["ipackeps.ac-creteil.fr"],
                "search_depth": "advanced",
                "include_raw_content": True 
            })
            
            raw_data = "\n".join([r.get('raw_content', r.get('content', '')) for r in res.json().get("results", [])])
            
            # SYSTEM EXPERT "ROUTEUR D'EXPERT"
            system_expert = """
            Tu es l'expert support technique d'iPackEPS.
            MISSION : Identifier le module de la question parmi la liste ci-dessous et extraire la procédure pas-à-pas.

            MATRICE DE ROUTAGE :
            1. Accès : Connexion ARENA, Fiche Professeur.
            2. Gestion annuelle : Archivage, Fiche Établissement, Équipes.
            3. Projets & Dossiers : Projets EPS/SSS, APSAs, Emplois du temps.
            4. Gestion Élèves : Import Pronote, Groupes, Inaptitudes, Visualisation.
            5. Dossier Certificatif : Protocoles, Référentiels, CAHPN, Certificats Médicaux.
            6. Dossier Natation : ASNS, Enquête Natation.
            7. Sections Sportives (SSS) : Ouverture, Projet, Bilan.
            8. Documents & Outils : Impression, Publipostage, Bibliothèque, Export.
            9. Cyclades/Santorin : Transfert données, Saisie notes, Lots correction, Verrouillage.

            RÈGLES DE NAVIGATION :
            1. IDENTIFICATION : Associe la question de l'utilisateur à l'un des 9 modules ci-dessus.
            2. EXTRACTION : Cherche dans les données fournies le lien ou le titre correspondant à la procédure demandée.
            3. PAS-À-PAS : Donne le chemin complet : "Tableau de bord => Dossier X => Module Y".
            4. ACTIONNABLE : Décris les étapes (clics, menus, boutons) sans blabla administratif.
            5. FORMAT : Markdown pur, numéroté, concis.
            """
            
            Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0, max_tokens=1500, api_key=st.secrets["OPENAI_API_KEY"])
            
            response = Settings.llm.complete(system_expert + "\n\nContenu technique extrait : " + raw_data + "\n\nQuestion utilisateur : " + prompt)
            
            st.session_state.messages_hub.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"Erreur technique : {str(e)}"})
    st.rerun()

# 4. AFFICHAGE
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        st.markdown(m["content"])
