import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# ======================================================================
# 1. CONFIGURATION (CSS & PAGE - INTACT)
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")
# [INSÈRE ICI TON BLOC ST.MARKDOWN CSS ORIGINAL]

# ======================================================================
# 4. INITIALISATION DES 4 CONTEXTES (NOUVELLE STRUCTURE FUSIONNÉE)
# ======================================================================
@st.cache_resource
def init_all_retrievers():
    # Base iPack
    docs_ipack = [...] # (Ta base actuelle avec tes docs iPack)
    retriever_ipack = VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=2)
    
    # Base Santorin
    docs_santorin = [...] # (Ta base actuelle avec tes docs Santorin)
    retriever_santorin = VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=2)
    
    # Base Sécurité/Réglementaire
    if os.path.exists("reglementaire.txt"):
        with open("reglementaire.txt", "r", encoding="utf-8") as f:
            docs_reg = [Document(text=f.read(), metadata={"title": "Textes Officiels"})]
            retriever_securite = VectorStoreIndex.from_documents(docs_reg).as_retriever(similarity_top_k=3)
    else:
        retriever_securite = None
        
    return retriever_ipack, retriever_santorin, retriever_securite

retriever_ipack, retriever_santorin, retriever_securite = init_all_retrievers()

# ======================================================================
# 9. ROUTAGE INTELLIGENT (MODIFIÉ POUR LES 4 CONTEXTES)
# ======================================================================
if prompt:
    extraits_doc = ""
    # Logique de routage étendue
    if st.session_state.active_module == "ipack":
        res = retriever_ipack.retrieve(prompt)
        extraits_doc = "\n".join([n.node.text for n in res])
    elif st.session_state.active_module == "examens":
        res = retriever_santorin.retrieve(prompt)
        extraits_doc = "\n".join([n.node.text for n in res])
    elif st.session_state.active_module == "securite":
        if retriever_securite:
            res = retriever_securite.retrieve(prompt)
            extraits_doc = "\n".join([n.node.text for n in res])
        else:
            extraits_doc = "Le fichier reglementaire.txt est introuvable."
            
    # ... (le reste de ton code avec Tavily et l'appel LLM)
