import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# --- FONCTION DE SÉCURITÉ POUR LIRE TON FICHIER ---
@st.cache_resource
def charger_consignes_pierre():
    if os.path.exists("Géré par pierre.txt"):
        try:
            return SimpleDirectoryReader(input_files=["Géré par pierre.txt"]).load_data()
        except:
            return []
    return []

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ======================================================================
# 2. GESTION MÉMOIRE ET COMPTEUR
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state:
    st.session_state.active_module = "general"  

def incrementer_et_obtenir_visites():
    fichier_compteur = "compteur_visites.txt"
    if not os.path.exists(fichier_compteur):
        try:
            with open(fichier_compteur, "w") as f:
                f.write("1")
            return 1
        except:
            return 1
    
    try:
        with open(fichier_compteur, "r") as f:
            valeur = int(f.read().strip())
        
        if "visite_comptabilisee" not in st.session_state:
            valeur += 1
            with open(fichier_compteur, "w") as f:
                f.write(str(valeur))
            st.session_state.visite_comptabilisee = True
        return valeur
    except:
        return 1

nb_visites_reel = incrementer_et_obtenir_visites()

# ======================================================================
# 3. INTERFACE GRAPHIQUE (INCHANGÉ)
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png" 
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

st.markdown(f"""
    <style>
    /* ... (Ton CSS inchangé) ... */
    .block-container {{ padding-top: 0.5rem; padding-bottom: 2rem; padding-left: 1.5rem; padding-right: 1.5rem; max-width: 920px; }}
    .stApp {{ background-image: url('{github_url}{img_fond}'); background-size: cover; background-attachment: fixed; }}
    </style>
""", unsafe_allow_html=True)

# ======================================================================
# 4. IA ET BASES DE CONNAISSANCES (MODIFIÉ AVEC TES DONNÉES)
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

@st.cache_resource
def initialiser_base_santorin():
    docs_santorin = [
        Document(text="""Fiche Mémo - Correction Partagée Santorin...""", metadata={"title": "Fiche Mémo - Correction Partagée Santorin"}),
        # ... (Garde bien TOUS tes documents ici comme dans ton fichier original)
    ]
    docs_santorin.extend(charger_consignes_pierre()) # <--- TON FICHIER EST ICI
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=2)

@st.cache_resource
def initialiser_base_ipack():
    docs_ipack = [
        Document(text="""Portail Pilote iPackEPS...""", metadata={"title": "Portail Officiel iPackEPS"}),
        # ... (Garde bien TOUS tes documents ici comme dans ton fichier original)
    ]
    docs_ipack.extend(charger_consignes_pierre()) # <--- TON FICHIER EST ICI
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=2)

retriever_santorin = initialiser_base_santorin()
retriever_ipack = initialiser_base_ipack()

# ======================================================================
# 5. RESTE DU CODE (INCHANGÉ)
# ======================================================================
# ... (Tout le reste de ton code original ici)
