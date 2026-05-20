import streamlit as st
import os
import requests
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# ======================================================================
# 1. CONFIGURATION
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")

# ======================================================================
# 2. GESTION DE LA MÉMOIRE (Compteur supprimé pour la stabilité)
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state:
    st.session_state.active_module = "general"  

# ======================================================================
# 3. STYLE ET BANDEAU (Maintien de ton design)
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png" 
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover !important; }}
    .hub-header {{ background-color: #1E293B; display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; border-radius: 8px; }}
    .hub-title h1 {{ color: white !important; font-size: 20px; }}
    </style>
""", unsafe_allow_html=True)

# 4. CONFIGURATION IA
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

# 5. AFFICHAGE BANDEAU
st.markdown(f"""
    <div class="hub-header">
        <div class="hub-title"><h1>Hub IA - EPS</h1></div>
        <div><img src="{github_url}{img_eps}" width="70"></div>
    </div>
""", unsafe_allow_html=True)

# ... (Garde le reste de ton code original ici, à partir de la section 6 "BOUTONS DE CONTEXTE")
