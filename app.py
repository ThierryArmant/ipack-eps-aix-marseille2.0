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
# 1. CONFIGURATION DE L'APPLICATION (IMPÉRATIVEMENT EN PREMIER)
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR DE VISITES
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state:
    st.session_state.active_module = "general"  

def incrementer_et_recuperer_compteur():
    fichier_compteur = "compteur.txt"
    if not os.path.exists(fichier_compteur):
        with open(fichier_compteur, "w", encoding="utf-8") as f: 
            f.write("0")
            
    with open(fichier_compteur, "r", encoding="utf-8") as f:
        try: 
            total_visites = int(f.read().strip())
        except ValueError: 
            total_visites = 0
            
    if "visite_comptabilisee" not in st.session_state:
        total_visites += 1
        st.session_state.visite_comptabilisee = True
        with open(fichier_compteur, "w", encoding="utf-8") as f: 
            f.write(str(total_visites))
            
    return total_visites

nb_visites = incrementer_et_recuperer_compteur()

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
    .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
        padding-left: 1.5rem !important; 
        padding-right: 1.5rem !important; 
        max-width: 920px !important; 
    }}
    
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover !important; background-attachment: fixed !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    
    /* Structure du Bandeau Supérieur Principal */
    .hub-header {{ 
        background-color: #1E293B; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 10px 20px; 
        margin-bottom: 15px !important; 
        border-radius: 8px; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3); 
    }}
    .hub-title h1 {{ color: white !important; margin: 0; font-size: 20px !important; font-weight: bold; }}
    .hub-title p {{ color: #94A3B8 !important; margin: 0; font-size: 10px !important; text-transform: uppercase; }}
    .visitor-badge {{ background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 12px; border-radius: 20px; font-size: 10px !important; font-weight: bold; font-family: monospace; margin-top: 5px; display: inline-block; }}
    
    /* Encadré Sélection du Contexte */
    .context-container {{
        background-color: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 14px 18px 18px 18px !important; 
        border-radius: 12px !important;
        margin-bottom: 18px !important;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.4);
    }}

    /* Barre Bleue Centrale Enrichie */
    .column-title {{ 
        color: #FFFFFF; 
        text-align: center; 
        margin-bottom: 15px !important; 
        background-color: #1E293B; 
        border-radius: 6px !important; 
        padding: 8px 10px; 
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
        line-height: 1.4;
    }}
    .column-title .instruction {{
        font-size: 11px !important;
        font-weight: 500;
        text-transform: uppercase;
        color: #94A3B8 !important;
        letter-spacing: 0.5px;
        display: block;
        margin-bottom: 2px;
    }}
    .column-title .mode-actuel {{
        font-size: 14px !important; 
        font-weight: 700;
        color: #FFFFFF !important;
        display: block;
    }}
    
    /* Boutons Inactifs */
    button[kind="secondary"] {{ 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 12px 10px !important;
        transition: all 0.3s ease;
    }}

    /* Boutons Actifs (Vert Émeraude) */
    button[kind="primary"] {{
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 12px 10px !important;
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important;
        font-weight: 700 !important;
        transition: all 0.3s ease;
    }}
    
    /* BOUTON NETTOYER : Opacité augmentée et texte blanc */
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {{
        background-color: rgba(220, 38, 38, 0.45) !important; /* Opacité à 45% */
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        padding: 7px 10px !important;
        width: 100% !important;
        box-shadow: none !important;
        font-weight: 500 !important;
    }}
    div.element-container:has(.nettoyer-wrapper) + div.element-container button:hover {{
        background-color: rgba(220, 38, 38, 0.65) !important; /* Opacité à 65% au survol */
        color: #FFFFFF !important;
    }}
    
    /* Cartes de réponse de l'IA */
    .santorin-card, .general-card {{ 
        background-color: rgba(15, 23, 42, 0.8) !important; 
        backdrop-filter: blur(10px) !important;
        padding: 18px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    }}
    .santorin-card {{ border-left: 6px solid #38BDF8 !important; }} 
    .general-card {{ border-left: 6px solid #10B981 !important; }} 
    
    .santorin-card *, .general-card * {{ 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
    }}
    
    /* Bulle Utilisateur */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {{ 
        background-color: rgba(255, 255, 255, 0.15) !important; 
        backdrop-filter: blur(6px) !important;
        border-radius: 14px 14px 0px 14px !important; 
        margin-left: 15% !important; 
    }}
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
    </style>
""", unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'INTELLIGENCE ARTIFICIELLE
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

# ======================================================================
# 5. BANDEAU SUPERIEUR
# ======================================================================
st.markdown(f"""
    <div class="hub-header">
        <div style="text-align: left; width: 25%;">
            <img src="{github_url}{img_gauche}" width="95">
        </div>
        <div class="hub-title" style="text-align: center; width: 50%;">
            <h1>Hub IA - EPS</h1>
            <p>Espace Ressources &amp; Assistance Numérique</p>
            <div class="visitor-badge">👁️ {nb_visites:05d} visites</div>
        </div>
        <div style="display: flex; justify-content: flex-end; align-items: center; width: 25%; gap: 15px;">
            <img src="{github_url}{img_eps}" width="70">
            <img src="{github_url}{img_droite}" width="60">
        </div>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 6. BOUTONS DE CONTEXTE
# ======================================================================
col_b1, col_b2, col_b3 = st.columns(3, gap="small")

with col_b1:
    if st.button("🛠️ iPackEPS", use_container_width=True, key="btn_ip", type="primary" if st.session_state.active_module == "ipack" else "secondary"):
        st.session_state.active_module = "ipack"
        st.session_state.messages_hub = []
        st.rerun()

with col_b2:
    if st.button("📊 Examens & Santorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"
        st.session_state.messages_hub = []
        st.rerun()

with col_b3:
    if st.button("🔍 Recherches Générales", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "general" else "secondary"):
        st.session_state.active_module = "general"
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 7. BARRE DE TITRE CENTRALE
# ======================================================================
label_titres = {
    "ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS",
    "examens": "📊 Mode Actif : Réglementation Examens & Dispenses",
    "general": "🔍 Mode Actif : Recherche Transversale Globale"
}

st.markdown(f"""
    <div class="column-title">
        <span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessus</span>
        <span class="mode-actuel">{label_titres[st.session_state.active_module]}</span>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 8. ZONE D'ACTION (NETTOYER + SAISIE)
# ======================================================================
col_action_clear, col_action_input = st.columns([1, 4.5], gap="small")

with col_action_clear:
    st.markdown('<div class="nettoyer-wrapper"></div>', unsafe_allow_html=True)
    if st.button("🧹 Nettoyer", key="clear_all"):
        st.session_state.messages_hub = []
        st.rerun()

with col_action_input:
    prompt = st.chat_input("Posez votre question institutionnelle ou technique ici...", key="chat_main")

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"**Vous** : {prompt}"})
    
    if st.session_state.active_module == "ipack":
        domaines_recherche = ["ipackeps.ac-creteil.fr"]
        texte_spinner = "Fouille de la base technique..."
        color_card = "general-card"
    elif st.session_state.active_module == "examens":
        domaines_recherche = ["pedagogie.ac-aix-marseille.fr", "eduscol.education.gouv.fr"]
        texte_spinner = "Analyse réglementaire..."
        color_card = "santorin-card"
    else:
        domaines_recherche = ["pedagogie.ac-aix-marseille.fr", "eduscol.education.gouv.fr", "eps.enseigne.ac-lyon.fr", "eps.ac-creteil.fr"]
        texte_spinner = "Recherche multi-académies..."
        color_card = "general-card"

    with st.spinner(texte_spinner):
        extraits_doc = ""
        if tavily_api_key:
            try:
                payload = {
                    "api_key": tavily_api_key,
                    "query": f"{prompt} EPS",
                    "search_depth": "advanced",
                    "include_domains": domaines_recherche
                }
                res = requests.post("https://api.tavily.com/search", json=payload, timeout=10)
                if res.status_code == 200:
                    data_web = res.json()
                    for item in data_web.get("results", []):
                        extraits_doc += f"Source: {item['title']} ({item['url']})\nContenu: {item['content']}\n\n"
            except: pass

        if st.session_state.active_module == "ipack":
            consigne_ia = f"Tu es l'assistant technique iPackEPS. Crée un tuto précis basé sur : {extraits_doc}. Ajoute l'URL. Pas de menus imaginaires."
            badge_title = "🛠️ PROTOCOLE TECHNIQUE"
        elif st.session_state.active_module == "examens":
            consigne_ia = f"Tu es l'assistant officiel. Réponds sur les textes ou dispenses à partir de : {extraits_doc}. Pas de clics logiciels. Ajoute les liens URL exacts."
            badge_title = "📊 REGLEMENTATION & EXAMENS"
        else:
            consigne_ia = f"Tu es l'assistant de recherche globale EPS. Synthétise clairement : {extraits_doc}. Donne la liste des URL."
            badge_title = "🔍 RÉSULTATS DE RECHERCHE"

        response_web = Settings.llm.complete(consigne_ia)
        formatted_answer = f'<div class="{color_card}"><strong>{badge_title} :</strong><br><br>{response_web.text}</div>'

    st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
    st.rerun()
