import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET COMPTEUR
# ======================================================================
if "messages_hub" not in st.session_state: st.session_state.messages_hub = []
if "active_module" not in st.session_state: st.session_state.active_module = "general"

def incrementer_et_obtenir_visites():
    fichier_compteur = "compteur_visites.txt"
    if not os.path.exists(fichier_compteur):
        try:
            with open(fichier_compteur, "w") as f: f.write("1")
            return 1
        except: return 1
    try:
        with open(fichier_compteur, "r") as f: valeur = int(f.read().strip())
        if "visite_comptabilisee" not in st.session_state:
            valeur += 1
            with open(fichier_compteur, "w") as f: f.write(str(valeur))
            st.session_state.visite_comptabilisee = True
        return valeur
    except: return 1

nb_visites_reel = incrementer_et_obtenir_visites()

# ======================================================================
# 3. CSS ET INTERFACE GRAPHIQUE
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
    .hub-header {{ background-color: #1E293B; display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; height: 85px !important; margin-bottom: 15px !important; border-radius: 8px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); }}
    .hub-title {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; flex-grow: 1; padding-right: 35px; }}
    .title-row {{ display: flex; align-items: center; justify-content: center; gap: 15px; }}
    .hub-title h1 {{ color: white !important; margin: 0 !important; font-size: 28px !important; font-weight: 800 !important; line-height: 1.2 !important; letter-spacing: 0.5px; }}
    .badge-visiteur {{ background-color: rgba(16, 185, 129, 0.2) !important; color: #10B981 !important; border: 1px solid rgba(16, 185, 129, 0.45) !important; padding: 3px 12px !important; border-radius: 20px !important; font-size: 13px !important; font-weight: 800 !important; font-family: monospace !important; line-height: 1 !important; display: inline-block; box-shadow: 0px 0px 8px rgba(16, 185, 129, 0.2); }}
    .hub-title p {{ color: #94A3B8 !important; margin: 0 !important; margin-top: -1px !important; font-size: 13px !important; text-transform: uppercase; font-weight: bold !important; line-height: 1.1 !important; letter-spacing: 0.5px; }}
    .column-title-top {{ color: #FFFFFF; text-align: center; margin-bottom: 12px !important; background-color: #1E293B; border-radius: 6px !important; padding: 8px 10px; box-shadow: 0px 4px 8px rgba(0,0,0,0.2); line-height: 1.4; }}
    .column-title-top .instruction {{ font-size: 11px !important; font-weight: 500; text-transform: uppercase; color: #94A3B8 !important; letter-spacing: 0.5px; display: block; margin-bottom: 2px; }}
    .column-title-top .mode-actuel {{ font-size: 14px !important; font-weight: 700; color: #FFFFFF !important; display: block; }}
    .column-title-bottom {{ text-align: center; margin-top: 12px !important; margin-bottom: 15px !important; background-color: rgba(30, 41, 59, 0.8); border-radius: 6px !important; padding: 8px 12px; border: 1px solid rgba(255, 255, 255, 0.05); font-size: 11px !important; color: #FCD34D !important; font-weight: 500; box-shadow: 0px 2px 6px rgba(0,0,0,0.15); }}
    button[kind="secondary"] {{ background-color: rgba(15, 23, 42, 0.9) !important; color: #94A3B8 !important; border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 8px !important; font-size: 13px !important; padding: 12px 10px !important; transition: all 0.3s ease; }}
    button[kind="primary"] {{ background-color: rgba(16, 185, 129, 0.85) !important; color: #FFFFFF !important; border: 1px solid #10B981 !important; border-radius: 8px !important; font-size: 13px !important; padding: 12px 10px !important; box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important; font-weight: 700 !important; }}
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {{ background-color: rgba(220, 38, 38, 0.45) !important; color: #FFFFFF !important; border: 1px solid rgba(220, 38, 38, 0.6) !important; border-radius: 8px !important; padding: 7px 10px !important; width: 100% !important; }}
    .santorin-card, .general-card, .securite-card {{ background-color: rgba(15, 23, 42, 0.45) !important; backdrop-filter: blur(12px) !important; padding: 18px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0px 6px 20px rgba(0,0,0,0.5); }}
    .santorin-card {{ border-left: 6px solid #38BDF8 !important; }} .general-card {{ border-left: 6px solid #10B981 !important; }} .securite-card {{ border-left: 6px solid #EF4444 !important; }}
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {{ background-color: rgba(255, 255, 255, 0.15) !important; border-radius: 14px 14px 0px 14px !important; margin-left: 15% !important; }}
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
    </style>
""", unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION IA ET BASES DE DOCUMENTS
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

def charger_consignes_pierre():
    chemin = "gere_par_pierre.txt"
    if os.path.exists(chemin):
        try:
            with open(chemin, "r", encoding="utf-8") as f: return [Document(text=f.read(), metadata={"source": "Notes de Pierre"})]
        except: return []
    return []

# MOTEUR AUTOMATIQUE : Remplace les bases manuelles par la lecture du dossier /data/
@st.cache_resource
def get_retriever():
    if os.path.exists("./data"):
        return VectorStoreIndex.from_documents(SimpleDirectoryReader("./data").load_data()).as_retriever(similarity_top_k=3)
    return None

retriever = get_retriever()

# ======================================================================
# 5. BANDEAU HAUT
# ======================================================================
st.markdown(f"""
    <div class="hub-header">
        <div style="display: flex; align-items: center; width: 20%;"><img src="{github_url}{img_gauche}" height="60"></div>
        <div class="hub-title">
            <div class="title-row"><h1>HUB IA - EPS</h1><span class="badge-visiteur">👁️ {nb_visites_reel}</span></div>
            <p>ESPACE RESSOURCES &amp; ASSISTANCE NUMÉRIQUE</p>
        </div>
        <div style="display: flex; justify-content: flex-end; align-items: center; width: 25%; gap: 15px;"><img src="{github_url}{img_eps}" height="55"><img src="{github_url}{img_droite}" height="55"></div>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 6. ROUTAGE ET INTERFACE
# ======================================================================
label_titres = {"ipack": "🛠️ Mode Actif : iPackEPS", "examens": "📊 Mode Actif : Examens & Santorin", "general": "🔍 Mode Actif : Général", "securite": "🔒 Mode Actif : Sécurité"}
st.markdown(f'<div class="column-title-top"><span class="mode-actuel">{label_titres[st.session_state.active_module]}</span></div>', unsafe_allow_html=True)

col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")
if col_b1.button("🛠️ iPackEPS"): st.session_state.active_module = "ipack"; st.rerun()
if col_b2.button("📊 Examens"): st.session_state.active_module = "examens"; st.rerun()
if col_b3.button("🔍 Général"): st.session_state.active_module = "general"; st.rerun()
if col_b4.button("🔒 Sécurité"): st.session_state.active_module = "securite"; st.rerun()

# ======================================================================
# 7. CHAT ET TRAITEMENT IA
# ======================================================================
prompt = st.chat_input("Posez votre question...")
if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": prompt})
    extraits_doc = "\n".join([n.node.text for n in retriever.retrieve(prompt)]) if retriever else ""
    consigne = f"Module: {st.session_state.active_module}. Doc: {extraits_doc}. Question: {prompt}."
    response = Settings.llm.complete(consigne)
    st.session_state.messages_hub.append({"role": "assistant", "content": response.text})
    st.rerun()

for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): st.markdown(m["content"])
