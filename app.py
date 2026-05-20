import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# ======================================================================
# 1. CONFIGURATION
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")

if "messages_hub" not in st.session_state: st.session_state.messages_hub = []
if "active_module" not in st.session_state: st.session_state.active_module = "general"

# Compteur factice (pour éviter l'écriture sur disque)
nb_visites = 1250 

# ======================================================================
# 2. DESIGN & STYLE
# ======================================================================
img_gauche, img_eps, img_droite, img_fond = "image_7.png", "image_6.png", "image_5.png", "image_8.png"
github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

st.markdown(f"""
    <style>
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover; }}
    .hub-header {{ background-color: #1E293B; display: flex; justify-content: space-between; align-items: center; padding: 15px; border-radius: 8px; }}
    .general-card {{ background-color: rgba(15, 23, 42, 0.9); padding: 15px; border-radius: 8px; border-left: 6px solid #10B981; margin-top: 10px; }}
    </style>
""", unsafe_allow_html=True)

# ======================================================================
# 3. CONFIGURATION IA
# ======================================================================
if st.secrets.get("OPENAI_API_KEY"):
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=st.secrets["OPENAI_API_KEY"])
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=st.secrets["OPENAI_API_KEY"])

# ======================================================================
# 4. BANDEAU & BOUTONS
# ======================================================================
st.markdown(f"""
    <div class="hub-header">
        <img src="{github_url}{img_gauche}" width="80">
        <h1 style="color:white;">Hub IA - EPS</h1>
        <div><img src="{github_url}{img_eps}" width="60"> <img src="{github_url}{img_droite}" width="50"></div>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
if col1.button("🛠️ iPackEPS"): st.session_state.active_module = "ipack"; st.rerun()
if col2.button("📊 Examens"): st.session_state.active_module = "examens"; st.rerun()
if col3.button("🔍 Général"): st.session_state.active_module = "general"; st.rerun()

# ======================================================================
# 5. ZONE DE CHAT & RECHERCHE
# ======================================================================
if st.button("🧹 Nettoyer"): st.session_state.messages_hub = []; st.rerun()
prompt = st.chat_input("Posez votre question...")

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": prompt})
    
    # Définition des domaines selon le module
    dom = ["ipackeps.ac-creteil.fr"] if st.session_state.active_module == "ipack" else \
          ["eduscol.education.gouv.fr", "pedagogie.ac-aix-marseille.fr", "siec.education.fr"] if st.session_state.active_module == "examens" else \
          ["eduscol.education.gouv.fr", "eps.ac-creteil.fr"]

    with st.spinner("Recherche dans les sources..."):
        try:
            res = requests.post("https://api.tavily.com/search", json={
                "api_key": st.secrets["TAVILY_API_KEY"], "query": prompt, "include_domains": dom
            })
            resp = Settings.llm.complete(f"Réponds à : {prompt} avec ces sources : {res.json()}")
            st.session_state.messages_hub.append({"role": "assistant", "content": f'<div class="general-card">{resp.text}</div>'})
        except Exception as e:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"Erreur : {e}"})
    st.rerun()

for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)
