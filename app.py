import streamlit as st
import os
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# ======================================================================
# 1. CONFIGURATION
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")

if "messages_hub" not in st.session_state: st.session_state.messages_hub = []
if "active_module" not in st.session_state: st.session_state.active_module = "general"

# ======================================================================
# 2. CONFIGURATION IA & BASES (LE CŒUR DU BÉTONNAGE)
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

# BASE SANTORIN (Stable)
@st.cache_resource
def initialiser_base_santorin():
    docs = [
        Document(text="Correction partagée : Ajouter un correcteur via Arena > Lots > Détail > Correcteurs > Ajouter.", metadata={"title": "Correction Partagée"}),
        Document(text="Distribution lots : Utiliser le paramétrage des tailles de groupes dans l'onglet Distribution.", metadata={"title": "Distribution Lots"}),
        Document(text="Inaptitude : La saisie neutralise l'épreuve. Toute absence injustifiée est un 0/20.", metadata={"title": "Réglementation Note"})
    ]
    return VectorStoreIndex.from_documents(docs).as_retriever(similarity_top_k=2)

# BASE IPACKEPS RENFORCÉE (Le protocole de diagnostic)
@st.cache_resource
def initialiser_base_ipack():
    docs = [
        Document(
            text="""PROTOCOLE DE DÉPANNAGE PRIORITAIRE iPackEPS :
            1. BOUTON GRISÉ : Si une action est impossible, c'est qu'une note existe. Aller en 'Saisie des notes', effacer la note (laisser la case vide, pas de 0), sauvegarder, le bouton sera dégrisé.
            2. INAPTITUDES : Saisir UNIQUEMENT via 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude'. Ne JAMAIS taper 'IN' ou 'DI' manuellement.
            3. ERREURS D'INTERFACE : iPackEPS est sensible au cache navigateur. En cas de bug persistant, vider le cache (Ctrl+F5) ou changer de navigateur (Chrome/Edge).
            4. CAS BLOCAGE : Si un dossier est bloqué (ex: note unique), ne pas forcer. Transmission obligatoire au Jury Académique via Cyclades.""",
            metadata={"title": "Dépannage Technique iPackEPS"}
        )
    ]
    return VectorStoreIndex.from_documents(docs).as_retriever(similarity_top_k=2)

retriever_santorin = initialiser_base_santorin()
retriever_ipack = initialiser_base_ipack()

# ======================================================================
# 3. CONSIGNES IA (LE BÉTONNAGE LOGIQUE)
# ======================================================================
def get_system_prompt(module, prompt, extraits):
    base = f"""Tu es l'assistant expert du Hub IA EPS. Utilise les extraits suivants pour répondre : {extraits}.
    RÈGLES STRICTES :
    1. Si l'info n'est pas dans les documents, dis que tu ne sais pas. N'invente jamais de procédure.
    2. Pour iPackEPS : Priorise le protocole de dépannage technique avant toute réponse théorique.
    3. Pour la sécurité : Rappelle la loi de 1937 et la protection fonctionnelle.
    4. Réponds de façon concise et opérationnelle."""
    
    if module == "ipack":
        return f"{base} Tu es l'expert technique iPackEPS. Si l'utilisateur est bloqué, diagnostique d'abord l'état des notes (vides ou non) avant de proposer une solution."
    return base

# ======================================================================
# 4. LOGIQUE D'AFFICHAGE ET CHAT (Simplifié pour le déploiement)
# ======================================================================
st.title("HUB IA - EPS")
module = st.radio("Mode :", ["general", "ipack", "examens", "securite"], horizontal=True)

prompt = st.chat_input("Votre question :")

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": prompt})
    
    # Récupération contextuelle
    extraits = ""
    if module == "ipack":
        noeuds = retriever_ipack.retrieve(prompt)
        extraits = "\n".join([n.node.text for n in noeuds])
    elif module == "examens":
        noeuds = retriever_santorin.retrieve(prompt)
        extraits = "\n".join([n.node.text for n in noeuds])
        
    system_consigne = get_system_prompt(module, prompt, extraits)
    
    # Appel IA
    response = Settings.llm.complete(f"{system_consigne}\nQuestion : {prompt}")
    st.session_state.messages_hub.append({"role": "assistant", "content": response.text})

for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): st.write(m["content"])
