import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# ======================================================================
# 1. CONFIGURATION & CSS (Ton design original)
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")

# [Insère ici ton bloc de CSS st.markdown(f""" <style> ... """) complet]

# ======================================================================
# 4. INITIALISATION DES BASES (Tes 2 bases validées + structure 4 contextes)
# ======================================================================
@st.cache_resource
def initialiser_bases():
    # Base Santorin
    docs_santorin = [
        Document(text="Fiche Mémo - Correction Partagée Santorin...", metadata={"title": "Santorin"}),
        # ... (Tes autres documents Santorin)
    ]
    retriever_santorin = VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=2)

    # Base iPack
    docs_ipack = [
        Document(text="Portail Pilote iPackEPS...", metadata={"title": "iPack"}),
        # ... (Tes autres documents iPack)
    ]
    retriever_ipack = VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=2)

    return retriever_ipack, retriever_santorin

retriever_ipack, retriever_santorin = initialiser_bases()

# ======================================================================
# 6. BANDEAU & BOUTONS (Les 4 contextes)
# ======================================================================
# ... (Tes boutons col_b1, col_b2, col_b3, et le nouveau col_b4)
# avec la logique st.session_state.active_module

# ======================================================================
# 9. ROUTAGE INTELLIGENT (Fusion des 4 contextes)
# ======================================================================
if prompt:
    extraits_doc = ""
    
    if st.session_state.active_module == "ipack":
        res = retriever_ipack.retrieve(prompt)
        extraits_doc = "\n".join([n.node.text for n in res])
        
    elif st.session_state.active_module == "examens":
        res = retriever_santorin.retrieve(prompt)
        extraits_doc = "\n".join([n.node.text for n in res])
        
    elif st.session_state.active_module == "securite":
        extraits_doc = "Recherche réglementaire en cours via le Web..."
        
    elif st.session_state.active_module == "general":
        extraits_doc = "" # Recherche purement Web via Tavily

    # ... (Ton bloc Tavily et LLM inchangé)
