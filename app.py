import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# --- FONCTION DE CHARGEMENT INVINCIBLE ---
@st.cache_resource
def charger_consignes_pierre():
    chemin_fichier = "gere_par_pierre.txt"
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, "r", encoding="utf-8") as f:
                contenu = f.read()
            st.sidebar.success("✅ 'gere_par_pierre.txt' chargé.")
            return [Document(text=contenu, metadata={"title": "Notes personnelles"})]
        except Exception as e:
            st.sidebar.error(f"❌ Erreur lecture : {e}")
            return []
    return []

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR
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
# 3. CONFIGURATION IA ET BASES (SANTORIN & IPACK)
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

@st.cache_resource
def initialiser_base_santorin():
    docs = [Document(text="Fiche Mémo - Santorin...")]
    docs.extend(charger_consignes_pierre()) # <-- Injection de tes notes
    return VectorStoreIndex.from_documents(docs).as_retriever(similarity_top_k=2)

@st.cache_resource
def initialiser_base_ipack():
    docs = [Document(text="Portail iPackEPS...")]
    docs.extend(charger_consignes_pierre()) # <-- Injection de tes notes
    return VectorStoreIndex.from_documents(docs).as_retriever(similarity_top_k=2)

retriever_santorin = initialiser_base_santorin()
retriever_ipack = initialiser_base_ipack()

# --- RESTE DE TON CODE ORIGINAL ---
# (Tu peux coller ici la suite de ton code à partir de la section "INTERFACE GRAPHIQUE")
