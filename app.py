import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION (IDENTIQUE)
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR (IDENTIQUE)
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
# 3. INTERFACE GRAPHIQUE (IDENTIQUE)
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png" 
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

st.markdown(f"""
    <style>
    .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
        padding-left: 1.5rem !important; 
        padding-right: 1.5rem !important; 
        max-width: 920px !important; 
    }}
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
    div.element-container:has(.nettoyer-wrapper) + div.element-container button:hover {{ background-color: rgba(220, 38, 38, 0.65) !important; }}
    .santorin-card, .general-card, .securite-card {{ background-color: rgba(15, 23, 42, 0.45) !important; backdrop-filter: blur(12px) !important; padding: 18px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0px 6px 20px rgba(0,0,0,0.5); }}
    .santorin-card {{ border-left: 6px solid #38BDF8 !important; }} 
    .general-card {{ border-left: 6px solid #10B981 !important; }} 
    .securite-card {{ border-left: 6px solid #EF4444 !important; }} 
    .santorin-card p, .general-card p, .securite-card p, .santorin-card div, .general-card div, .securite-card div, .santorin-card span, .general-card span, .securite-card span, .santorin-card li, .general-card li, .securite-card li {{ color: #FFFFFF !important; font-size: 15px !important; line-height: 1.6 !important; font-weight: 400 !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.8); }}
    .santorin-card strong, .general-card strong, .securite-card strong {{ font-weight: 700 !important; color: #FFFFFF !important; }}
    .santorin-card a, .general-card a, .securite-card a {{ color: #FFB020 !important; text-decoration: underline !important; font-weight: 600 !important; }}
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {{ background-color: rgba(255, 255, 255, 0.15) !important; backdrop-filter: blur(6px) !important; border-radius: 14px 14px 0px 14px !important; margin-left: 15% !important; }}
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
    </style>
""", unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION IA (IDENTIQUE)
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

@st.cache_resource
def initialiser_base_santorin():
    docs_santorin = [
        Document(text="Correction partagée : Ajouter un correcteur via Arena > Lots > Détail > Correcteurs > Ajouter.", metadata={"title": "Correction Partagée"}),
        Document(text="Distribution lots : Utiliser le paramétrage des tailles de groupes dans l'onglet Distribution.", metadata={"title": "Distribution Lots"}),
        Document(text="Inaptitude : La saisie neutralise l'épreuve. Toute absence injustifiée est un 0/20.", metadata={"title": "Réglementation Note"})
    ]
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=2)

# ======================================================================
# 5. INITIALISER BASE IPACK "BÉTONNÉE" (LA SEULE MODIFICATION)
# ======================================================================
@st.cache_resource
def initialiser_base_ipack():
    docs_ipack = [
        Document(
            text="""PROTOCOLE DE DÉPANNAGE PRIORITAIRE iPackEPS :
            1. BOUTON GRISÉ : Si une action est impossible, c'est qu'une note existe. Aller en 'Saisie des notes', effacer la note (laisser la case vide, pas de 0), sauvegarder. Le bouton sera dégrisé.
            2. INAPTITUDES : Saisir UNIQUEMENT via 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude'. Ne jamais taper 'IN' ou 'DI' manuellement.
            3. ERREURS D'INTERFACE : iPackEPS est sensible au cache navigateur. En cas de bug persistant, vider le cache (Ctrl+F5) ou changer de navigateur (Chrome/Edge).
            4. CAS BLOCAGE : Si un dossier est bloqué (ex: note unique), ne pas forcer. Transmission obligatoire au Jury Académique via Cyclades.""",
            metadata={"title": "Dépannage Technique iPackEPS"}
        )
    ]
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=2)

retriever_santorin = initialiser_base_santorin()
retriever_ipack = initialiser_base_ipack()

# [RESTE DU CODE (AFFICHAGE ET CHAT) IDENTIQUE À TON ORIGINAL...]
# (Il suffit de remettre la suite de ton code d'origine ici, il fonctionnera parfaitement avec les nouveaux retrievers)
