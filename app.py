import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core import Document

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE (Compteur supprimé pour la stabilité)
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state:
    st.session_state.active_module = "general"  

# Valeur fixe pour le badge visuel, sans écriture sur disque
nb_visites = 1250 

# ======================================================================
# 3. INTERFACE GRAPHIQUE ET FEUILLES DE STYLE 
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png" 
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 2rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; max-width: 920px !important; }}
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover !important; background-attachment: fixed !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    .hub-header {{ background-color: #1E293B; display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; margin-bottom: 15px !important; border-radius: 8px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); }}
    .hub-title h1 {{ color: white !important; margin: 0; font-size: 20px !important; font-weight: bold; }}
    .hub-title p {{ color: #94A3B8 !important; margin: 0; font-size: 10px !important; text-transform: uppercase; }}
    .visitor-badge {{ background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 12px; border-radius: 20px; font-size: 10px !important; font-weight: bold; font-family: monospace; margin-top: 5px; display: inline-block; }}
    .column-title {{ color: #FFFFFF; text-align: center; margin-bottom: 15px !important; background-color: #1E293B; border-radius: 6px !important; padding: 8px 10px; box-shadow: 0px 4px 8px rgba(0,0,0,0.2); line-height: 1.4; }}
    .column-title .instruction {{ font-size: 11px !important; font-weight: 500; text-transform: uppercase; color: #94A3B8 !important; display: block; margin-bottom: 2px; }}
    .column-title .mode-actuel {{ font-size: 14px !important; font-weight: 700; color: #FFFFFF !important; display: block; }}
    button[kind="secondary"] {{ background-color: rgba(15, 23, 42, 0.9) !important; color: #94A3B8 !important; border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 8px !important; padding: 12px 10px !important; }}
    button[kind="primary"] {{ background-color: rgba(16, 185, 129, 0.85) !important; color: #FFFFFF !important; border: 1px solid #10B981 !important; border-radius: 8px !important; padding: 12px 10px !important; box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important; font-weight: 700 !important; }}
    .santorin-card, .general-card {{ background-color: rgba(15, 23, 42, 0.8) !important; backdrop-filter: blur(10px) !important; padding: 18px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0px 4px 15px rgba(0,0,0,0.4); }}
    .santorin-card {{ border-left: 6px solid #38BDF8 !important; }} 
    .general-card {{ border-left: 6px solid #10B981 !important; }} 
    .santorin-card *, .general-card * {{ color: #FFFFFF !important; font-size: 15px !important; line-height: 1.6 !important; }}
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {{ background-color: rgba(255, 255, 255, 0.15) !important; backdrop-filter: blur(6px) !important; border-radius: 14px 14px 0px 14px !important; margin-left: 15% !important; }}
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
    </style>
""", unsafe_allow_html=True)

# 4. CONFIGURATION IA
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

# 5. BANDEAU SUPERIEUR
st.markdown(f"""
    <div class="hub-header">
        <div style="text-align: left; width: 25%;"> <img src="{github_url}{img_gauche}" width="95"> </div>
        <div class="hub-title" style="text-align: center; width: 50%;">
            <h1>Hub IA - EPS</h1>
            <p>Espace Ressources &amp; Assistance Numérique</p>
            <div class="visitor-badge">👁️ {nb_visites:05d} visites</div>
        </div>
        <div style="display: flex; justify-content: flex-end; align-items: center; width: 25%; gap: 15px;">
            <img src="{github_url}{img_eps}" width="70"> <img src="{github_url}{img_droite}" width="60">
        </div>
    </div>
""", unsafe_allow_html=True)

# 6. BOUTONS DE CONTEXTE
col_b1, col_b2, col_b3 = st.columns(3, gap="small")
if col_b1.button("🛠️ iPackEPS", use_container_width=True, type="primary" if st.session_state.active_module == "ipack" else "secondary"):
    st.session_state.active_module = "ipack"; st.session_state.messages_hub = []; st.rerun()
if col_b2.button("📊 Examens & Santorin", use_container_width=True, type="primary" if st.session_state.active_module == "examens" else "secondary"):
    st.session_state.active_module = "examens"; st.session_state.messages_hub = []; st.rerun()
if col_b3.button("🔍 Recherches Générales", use_container_width=True, type="primary" if st.session_state.active_module == "general" else "secondary"):
    st.session_state.active_module = "general"; st.session_state.messages_hub = []; st.rerun()

# 7. TITRE ET ACTION
label_titres = {"ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS", "examens": "📊 Mode Actif : Réglementation Examens & Dispenses", "general": "🔍 Mode Actif : Recherche Transversale Globale"}
st.markdown(f'<div class="column-title"><span class="instruction">⚙️ Choisissez le contexte</span><span class="mode-actuel">{label_titres[st.session_state.active_module]}</span></div>', unsafe_allow_html=True)

col_action_clear, col_action_input = st.columns([1, 4.5], gap="small")
if col_action_clear.button("🧹 Nettoyer"): st.session_state.messages_hub = []; st.rerun()
prompt = col_action_input.chat_input("Posez votre question institutionnelle ou technique ici...")

# 8. FLUX DE MESSAGES
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"**Vous** : {prompt}"})
    with st.spinner("Analyse en cours..."):
        # Logique de recherche
        try:
            res = requests.post("https://api.tavily.com/search", json={
                "api_key": tavily_api_key, "query": f"{prompt} EPS", "search_depth": "advanced"
            })
            response_web = Settings.llm.complete(f"Synthétise : {res.json()}")
            badge = "🔍 RÉSULTATS"
            formatted_answer = f'<div class="general-card"><strong>{badge} :</strong><br><br>{response_web.text}</div>'
            st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        except Exception as e: st.session_state.messages_hub.append({"role": "assistant", "content": f"Erreur : {e}"})
    st.rerun()
