import streamlit as st 
import os
import pandas as pd
import requests
import re
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION (IMPÉRATIVEMENT EN PREMIER)
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR DE VISITES FIABLE (PROTÉGÉ)
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state: 
    st.session_state.active_module = "peda"  

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
        
        # On incrémente uniquement au premier chargement de la session utilisateur
        if "visite_comptabilisee" not in st.session_state:
            valeur += 1
            with open(fichier_compteur, "w") as f:
                f.write(str(valeur))
            st.session_state.visite_comptabilisee = True
            
        return valeur
    except:
        return 1

# Récupération du score réel sans risque de plantage
nb_visites_reel = incrementer_et_obtenir_visites()

# ======================================================================
# 3. INTERFACE GRAPHIQUE ET CONFIGURATION DES LIENS IMAGES
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png" 
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

css_pur = """
    <style>
    /* Règle de sécurité : Force le blanc sur tout le texte des cartes */
    .santorin-card *, .general-card *, .securite-card * { 
        color: #FFFFFF !important; 
    }

    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
        padding-left: 1.5rem !important; 
        padding-right: 1.5rem !important; 
        max-width: 920px !important; 
    }
    
    .stApp { background-image: url('__URL_FOND__') !important; background-size: cover !important; background-attachment: fixed !important; }
    header[data-testid="stHeader"] { display: none !important; }
    
    /* Structure du Bandeau Supérieur Principal Réorganisé et Optimisé */
    .hub-header { 
        background-color: #1E293B; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 10px 20px; 
        height: 85px !important; 
        margin-bottom: 15px !important; 
        border-radius: 8px; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3); 
    }
    
    /* Bloc titre équilibré avec décalage de sécurité pour éviter le collage à droite */
    .hub-title {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        flex-grow: 1;
        padding-right: 35px; 
    }
    
    /* Ligne du titre principal */
    .title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }
    
    .title-row h1 { 
        color: white !important; 
        margin: 0 !important; 
        font-size: 28px !important; 
        font-weight: 800 !important; 
        line-height: 1.2 !important;
        letter-spacing: 0.5px;
    }
    
    /* Badge vert émeraude agrandi et bien visible */
    .badge-visiteur { 
        background-color: rgba(16, 185, 129, 0.2) !important; 
        color: #10B981 !important; 
        border: 1px solid rgba(16, 185, 129, 0.45) !important; 
        padding: 3px 12px !important; 
        border-radius: 20px !important; 
        font-size: 13px !important; 
        font-weight: 800 !important; 
        font-family: monospace !important;
        line-height: 1 !important;
        display: inline-block;
        box-shadow: 0px 0px 8px rgba(16, 185, 129, 0.2);
    }
    
    /* Style du Sous-titre nettoyé */
    .hub-title p { 
        color: #94A3B8 !important; 
        margin: 0 !important;
        margin-top: -1px !important; 
        font-size: 13px !important; 
        text-transform: uppercase; 
        font-weight: bold !important;
        line-height: 1.1 !important; 
        letter-spacing: 0.5px;
    }

    /* Barres d'informations Supérieures et Inférieures */
    .column-title-top { 
        color: #FFFFFF; 
        text-align: center; 
        margin-bottom: 12px !important; 
        background-color: #1E293B; 
        border-radius: 6px !important; 
        padding: 8px 10px; 
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
        line-height: 1.4;
    }
    .column-title-top .instruction {
        font-size: 11px !important;
        font-weight: 500;
        text-transform: uppercase;
        color: #94A3B8 !important;
        letter-spacing: 0.5px;
        display: block;
        margin-bottom: 2px;
    }
    .column-title-top .mode-actuel {
        font-size: 14px !important; 
        font-weight: 700;
        color: #FFFFFF !important;
        display: block;
    }

    .column-title-bottom { 
        text-align: center; 
        margin-top: 12px !important;
        margin-bottom: 15px !important; 
        background-color: rgba(30, 41, 59, 0.8); 
        border-radius: 6px !important; 
        padding: 8px 12px; 
        border: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 11px !important; 
        color: #FCD34D !important; 
        font-weight: 500;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
    }
    
    /* Boutons Inactifs - Alignement et hauteur forcés */
    button[kind="secondary"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 2px 10px !important;
        transition: all 0.3s ease;
        height: 60px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: normal !important;
    }

    /* Boutons Actifs - Alignement et hauteur forcés */
    button[kind="primary"] {
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 2px 10px !important;
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important;
        font-weight: 700 !important;
        height: 60px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: normal !important;
    }
    
    /* BOUTON NETTOYER */
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {
        background-color: rgba(220, 38, 38, 0.45) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        padding: 7px 10px !important;
        width: 100% !important;
        height: 38px !important;
    }
    div.element-container:has(.nettoyer-wrapper) + div.element-container button:hover {
        background-color: rgba(220, 38, 38, 0.65) !important;
    }
    
    /* CARTES DE RÉPONSE - ARCHITECTURE DES COULEURS DES ONGLETS */
    .santorin-card, .general-card, .securite-card, .peda-card { 
        background-color: rgba(15, 23, 42, 0.45) !important; 
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 18px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
        box-shadow: 0px 6px 20px rgba(0,0,0,0.5);
    }
    .santorin-card { border-left: 6px solid #38BDF8 !important; } 
    .general-card { border-left: 6px solid #10B981 !important; } 
    .securite-card { border-left: 6px solid #FF9F43 !important; } 
    .peda-card { border-left: 6px solid #FFA502 !important; } 
    
    .santorin-card p, .general-card p, .securite-card p, .santorin-card div, .general-card div, .securite-card div, .santorin-card span, .general-card span, .securite-card span, .santorin-card li, .general-card li, .securite-card li { 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
        font-weight: 400 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    
    .santorin-card h3, .general-card h3, .securite-card h3, .peda-card h3 {
        color: #38BDF8 !important; 
        font-size: 16px !important; 
        margin-top: 16px !important; 
        margin-bottom: 6px !important; 
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9);
    }
    
    .peda-card ul {
        margin-top: 2px !important;
        margin-bottom: 6px !important;
        padding-left: 20px !important;
    }
    .peda-card li, .peda-card div, .peda-card span, .peda-card p {
        font-size: 14px !important; 
        line-height: 1.4 !important; 
        color: #F8FAFC !important; 
        margin-bottom: 3px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }

    .santorin-card strong, .general-card strong, .securite-card strong, .peda-card strong {
        font-weight: 700 !important; 
    }

    .law-highlight {
        background-color: rgba(255, 176, 32, 0.12) !important; 
        color: #FFB020 !important; 
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid rgba(255, 176, 32, 0.4) !important;
        font-weight: 700 !important;
        display: inline-block;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.5) !important;
    }

    div.santorin-card a, div.general-card a, div.securite-card a, div.peda-card a,
    div.santorin-card a *, div.general-card a *, div.securite-card a *, div.peda-card a * {
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9) !important;
        display: inline !important;
    }
    div.santorin-card a:hover, div.general-card a:hover, div.securite-card a:hover, div.peda-card a:hover {
        color: #FCD34D !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { 
        background-color: rgba(255, 255, 255, 0.15) !important; 
        backdrop-filter: blur(6px) !important;
        border-radius: 14px 14px 0px 14px !important; 
        margin-left: 15% !important; 
    }
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
    
    div[data-testid="stChatMessage"] * { color: #FFFFFF !important; }
    
    div[data-testid="stChatMessage"] a, div[data-testid="stChatMessage"] a * {
        color: #FFB020 !important;
        text-decoration: underline !important;
        font-weight: 600 !important;
    }
    div[data-testid="stChatMessage"] a:hover {
        color: #FCD34D !important;
    }
    
    </style> 
""".replace('__URL_FOND__', f"{github_url}{img_fond}")
st.markdown(css_pur, unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'INTELLIGENCE ARTIFICIELLE & DES BASES DE DOCUMENTS
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

def obtenir_cle_fichier():
    mtimes = []
    for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
        if os.path.exists(fp):
            try: mtimes.append(os.path.getmtime(fp))
            except: pass
    chemin_textes = "data/textes/base_textes_officiels.txt"
    if os.path.exists(chemin_textes):
        try: mtimes.append(os.path.getmtime(chemin_textes))
        except: pass
    for f_peda in ["base_pedagogique_edubase.txt", "matrice_AFL_lycee.txt"]:
        if os.path.exists(f_peda):
            try: mtimes.append(os.path.getmtime(f_peda))
            except: pass
    if os.path.exists("data/peda") and os.path.isdir("data/peda"):
        try:
            for f in os.listdir("data/peda"): mtimes.append(os.path.getmtime(os.path.join("data/peda", f)))
        except: pass
    if os.path.exists("data/examens") and os.path.isdir("data/examens"):
        try:
            for f in os.listdir("data/examens"): mtimes.append(os.path.getmtime(os.path.join("data/examens", f)))
        except: pass
    return max(mtimes) if mtimes else 0.0

def charger_consignes_pierre():
    documents_charges = []
    for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f: documents_charges.append(Document(text=f.read(), metadata={"source": f"Règles de Pierre ({fp})"}))
            except: pass
    return documents_charges

@st.cache_resource
def initialiser_base_santorin(cle_fremt):
    docs_santorin = [Document(text="Fiche Mémo - Correction Partagée Santorin (DEC). Spécifications techniques sur la correction multiple.", metadata={"title": "Correction Partagée", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf"})]
    if os.path.exists("data/examens") and os.path.isdir("data/examens"):
        try: docs_santorin.extend(SimpleDirectoryReader(input_dir="data/examens").load_data())
        except: pass
    docs_santorin.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_ipack(cle_fremt):
    docs_ipack = [Document(text="Guide Pratique iPackEPS - Saisie des structures trimestrielles et imports XML.", metadata={"title": "Guide iPackEPS", "url": "https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf"})]
    docs_ipack.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_textes(cle_fremt):
    docs_textes = [Document(text="Base de données réglementaire globale pour les textes de lois du second degré.", metadata={"title": "Légifrance", "url": "https://www.legifrance.gouv.fr/"})]
    if os.path.exists("data/textes/base_textes_officiels.txt"):
        try:
            with open("data/textes/base_textes_officiels.txt", "r", encoding="utf-8") as f: docs_textes.append(Document(text=f.read(), metadata={"title": "Textes EPS"}))
        except: pass
    docs_textes.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_textes).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_peda(cle_fremt):
    docs_peda = []
    if os.path.exists("data/peda") and os.path.isdir("data/peda"):
        try: docs_peda.extend(SimpleDirectoryReader(input_dir="data/peda").load_data())
        except: pass
    if not docs_peda: docs_peda.append(Document(text="Base pédagogique vide", metadata={"source": "system"}))
    return VectorStoreIndex.from_documents(docs_peda).as_retriever(similarity_top_k=5)

timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)
retriever_peda = initialiser_base_peda(timestamp_fichier)

# ======================================================================
# 5. BANDEAU SUPERIEUR REHAUSSÉ AVEC COMPTEUR
# ======================================================================
st.markdown(f"""
    <div class="hub-header">
        <div style="display: flex; align-items: center; width: 20%;">
            <img src="{github_url}{img_gauche}" height="60">
        </div>
        <div class="hub-title">
            <div class="title-row">
                <h1>HUB IA - EPS</h1>
                <span class="badge-visiteur">👁️ {nb_visites_reel}</span>
            </div>
            <p>ESPACE RESSOURCES &amp; ASSISTANCE NUMÉRIQUE</p>
        </div>
        <div style="display: flex; justify-content: flex-end; align-items: center; width: 25%; gap: 15px;">
            <img src="{github_url}{img_eps}" height="55">
            <img src="{github_url}{img_droite}" height="55">
        </div>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 6. EN-TÊTE DU TABLEAU DE BORD
# ======================================================================
label_titres = {
    "ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF & Inaptitudes)",
    "examens": "📊 Mode Actif : Réglementation Examens & Santorin (Copies Numérisées & Jurys)",
    "peda": "🔍 Mode Actif : Référentiels Institutionnels, APSA & Textes de Cadrage BO",
    "textes": "🔒 Mode Actif : SÉCURITÉ & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Référentiels Institutionnels")
st.markdown(f'<div class="column-title-top"><span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessous</span><span class="mode-actuel">{titre_affiche}</span></div>', unsafe_allow_html=True)

# ======================================================================
# 7. BOUTONS DE CONTEXTE
# ======================================================================
col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")
with col_b1:
    if st.button("🛠️ iPackEPS", use_container_width=True, key="btn_ip", type="primary" if st.session_state.active_module == "ipack" else "secondary"):
        st.session_state.active_module = "ipack"; st.session_state.messages_hub = []; st.rerun()
with col_b2:
    if st.button("📊 Examens &\nSantorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"; st.session_state.messages_hub = []; st.rerun()
with col_b3:
    if st.button("🔍 Cadrage &\nRéférentiels", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "peda" else "secondary"):
        st.session_state.active_module = "peda"; st.session_state.messages_hub = []; st.rerun()
with col_b4:
    if st.button("🔒 Sécurité &\nCadres Règl.", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
        st.session_state.active_module = "textes"; st.session_state.messages_hub = []; st.rerun()

# ======================================================================
# 7B. MESSAGES D'AVERTISSEMENT (VERSION OPTIMISÉE POIDS PLUME)
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement –</strong> Bien que basées sur les textes officiels, ces réponses ne remplacent pas les autorités académiques. En cas de doute juridique ou de sinistre, contactez impérativement : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)
elif st.session_state.active_module == "peda":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            💡 <strong>Rappel Institutionnel :</strong> Cet onglet extrait exclusivement les Champs d'Apprentissage (CA), compétences et Attendus des Bulletins Officiels (BO). La liberté pédagogique reste sous l'entière responsabilité des équipes d'établissement.
        </span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; line-height: 1.5;">
        <div style="color: #38BDF8; font-weight: 800; font-size: 14px; text-align: center; margin-bottom: 12px; letter-spacing: 0.5px;">🎯 OÙ POSER VOTRE QUESTION ?</div>
        <div style="display: flex; gap: 20px; color: #FCD34D; font-size: 13px;">
            <div style="flex: 1; border-right: 1px solid #334155; padding-right: 20px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">🛠️ Menu iPackEPS (Toute l'année)</strong><br>
                <span style="color: #FCD34D !important;">Technique de terrain : configuration, groupes, Saisie des notes brutes.</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(248, 113, 113, 0.15); border-left: 3px solid #F87171; border-radius: 4px;">
                    <span style="color: #F87171 !important; font-weight: 800;">⚠️ IMPORTANT INAPTITUDES :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Toutes les questions sur les certificats médicaux, dispenses et saisies d'inaptitude se posent TOUJOURS ici !</span>
                </div>
            </div>
            <div style="flex: 1; padding-left: 5px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">📊 Menu Examens & Santorin (Fin d'année)</strong><br>
                <span style="color: #FCD34D !important;">Administration des examens : remontée officielle du Bac/DNB, correction numérique sur Arena, arbitrages de la CAHPN.</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(56, 189, 248, 0.15); border-left: 3px solid #38BDF8; border-radius: 4px;">
                    <span style="color: #38BDF8 !important; font-weight: 800;">🚨 UN BUG ? (Cases grisées, blocage AFLP...) :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Posez directement votre question dans le chat ci-dessous, le Hub devrait vous dépanner!</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
# ======================================================================
# 8. ZONE D'ACTION
# ======================================================================
col_action_clear, col_action_input = st.columns([1, 4.5], gap="small")
with col_action_clear:
    st.markdown('<div class="nettoyer-wrapper"></div>', unsafe_allow_html=True)
    if st.button("🧹 Nettoyer", key="clear_all"): st.cache_resource.clear(); st.session_state.messages_hub = []; st.rerun()

with col_action_input: prompt = st.chat_input("Posez votre question institutionnelle, technique ou juridique ici...", key="chat_main")

st.markdown('<div style="background-color: #1E293B; padding: 12px 20px; border-radius: 6px; box-shadow: 0px 4px 8px rgba(0,0,0,0.2); margin-top: 10px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; line-height: 1.4;"><span style="color: #FCD34D; font-weight: 700; font-size: 13px;">⚠️ 💡 ATTENTION :</span><span style="color: #FFFFFF; font-weight: 500; font-size: 13px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);"> Pour des raisons pratiques, votre assistant ne mémorise pas le fil de la conversation. Posez vos questions une par une.</span></div>', unsafe_allow_html=True)

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        if m.get("type") == "video": st.video(m["content"])
        else: st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if prompt:
    st.session_state.messages_hub.append({"role": "user", "type": "text", "content": f"<span style='color: white;'>{prompt}</span>"})
    with st.spinner("Je recherche les documents..."):
        mode = st.session_state.active_module
        activer_web = False
        
        verites_terrain_pierre = ""
        try:
            for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
                if os.path.exists(fp):
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f: verites_terrain_pierre += f"\n--- REGLES DIRECTES DE PIERRE ---\n" + f.read() + "\n"
        except: pass

        # ======================================================================
        # 🧠 LE SUPER CERVEAU ANTI-PIÈGES : ROUTAGE SÉMANTIQUE ÉTANCHE PAR ONGLET
        # ======================================================================
        if mode == "examens":
            choix_autorises = """
            - CALENDRIER : Dates butoirs, dates limites, échéances, fermeture des serveurs, clôture des saisies.
            - SANTORIN_ERREUR_VALIDATION : Le prof a validé/déposé son lot trop vite, s'est trompé, lot clos/verrouillé, plus la main.
            - SANTORIN_INAPTE_SIMPLE : Saisie normale d'une dispense, inaptitude (IN), absent (AB) ou certificat médical (CM) sans bug d'interface.
            - SANTORIN_GRISE : Problèmes d'interface en lecture seule, boutons grisés, cases blanches, cadenas, absence de l'icône "crayon", conflit de correction partagée.
            - SANTORIN_BRICOLAGE : NOTE UNIQUE au Bac GT/Pro, moyenne impossible, formules (ex: "DI+DI+note", "1 note + 2 CM", "DI+note", "AB+DI+note"), arbitrage CAHPN, faire un prorata.
            - JURY_REMPLACEMENT : Problèmes de convocations, ordres de mission (OM), indemnités, réunions de sous-commissions, harmonisation ou prof remplaçant bloqué.
            - SANTORIN_CM_POSTERIEUR : Certificat médical ou dispense remis APRÈS l'évaluation, le lendemain ou rétroactif (ex: "gamin apporte une dispense après l'épreuve").
            - SANTORIN_BLESSURE_CHOC : Élève qui se blesse EN PLEIN MILIEU de l'évaluation ou pendant l'examen (ex: "blessé au 2ème passage").
            - EXAMENS_UNSS_ABSENCE : Élève absent car il est en compétition officielle UNSS, Championnat de France ou convocation fédérale.
            - AUCUN_BLINDAGE : Questions générales ou recherche documentaire classique dans les textes d'examens.
            """
        elif mode == "ipack":
            choix_autorises = """
            - CALENDRIER : Date limite de validation des notes trimestrielles sur iPackEPS.
            - IPACK_SSS : Un dossier ou bilan annuel est verrouillé par le chef d'établissement dans iPackEPS.
            - IPACK_GROUPES : Créer un groupe, configurer, associer un protocole/séquence d'APSA.
            - IPACK_NOUVEL_ELEVE : Ajouter un élève arrivant en cours d'année, synchronisation Pronote / SIECLE, fichier XML/CSV.
            - IPACK_TRANSFERT_DOUBLON : Élève qui change d'établissement avec des notes déjà acquises dans son ancien bahut, ou fiche en doublon.
            - AUCUN_BLINDAGE : Questions techniques générales sur l'interface iPackEPS.
            """
        elif mode == "textes":
            choix_autorises = """
            - SECURITE_TASA : La question concerne spécifiquement la taxe, la responsabilité liée au transport ou les déclarations TASA.
            - AUCUN_BLINDAGE : Textes juridiques généraux (Loi 1937, responsabilité APPN).
            """
        else:
            choix_autorises = "- AUCUN_BLINDAGE : Recherche pédagogique institutionnelle classique (APSA, fiches de cycle, CA)."

        intent_prompt = f"""
        Tu es l'aiguilleur master du Hub IA-EPS. Détermine l'INTENTION exacte.
        Question : "{prompt}" | Onglet : {mode}
        ⚠️ LINGUISTIQUE TERRAIN :
        - "DI" = Dispensé/Inapte, "AB" = Absent, "CM" = Certificat Médical, "OM" = Ordre de Mission.
        - "DI+DI+note" ou formule à une seule note = SANTORIN_BRICOLAGE (Note unique / CAHPN).
        - Si un justificatif arrive APRÈS l'épreuve = SANTORIN_CM_POSTERIEUR.
        - Si la blessure a lieu PENDANT l'épreuve = SANTORIN_BLESSURE_CHOC.
        - Si l'absence est due à l'UNSS/AS = EXAMENS_UNSS_ABSENCE.
        Réponds STRICTEMENT par le mot-clé exact choisi dans cette liste restrictive :
        {choix_autorises}
        """
        try: intention = Settings.llm.complete(intent_prompt).text.strip()
        except: intention = "AUCUN_BLINDAGE"

        # Association des drapeaux d'intention
        est_date_notes_direct = (intention == "CALENDRIER")
        est_erreur_validation_santorin = (intention == "SANTORIN_ERREUR_VALIDATION")
        est_inapte_santorin_direct = (intention == "SANTORIN_INAPTE_SIMPLE")
        est_grise_direct = (intention == "SANTORIN_GRISE")
        est_bricolage_note = (intention == "SANTORIN_BRICOLAGE")
        est_sss_direct = (intention == "IPACK_SSS")
        est_groupes_direct = (intention == "IPACK_GROUPES")
        est_nouvel_eleve_direct = (intention == "IPACK_NOUVEL_ELEVE")
        est_remplacement_reunion_direct = (intention == "JURY_REMPLACEMENT")
        est_cm_posterieur_direct = (intention == "SANTORIN_CM_POSTERIEUR")
        est_blessure_choc_direct = (intention == "SANTORIN_BLESSURE_CHOC")
        est_unss_absence_direct = (intention == "EXAMENS_UNSS_ABSENCE")
        est_transfert_doublon_direct = (intention == "IPACK_TRANSFERT_DOUBLON")
        est_tasa_direct = (intention == "SECURITE_TASA") or (mode == "textes" and "tasa" in prompt.lower())
        
        est_santorin_direct = mode == "examens" and intention == "AUCUN_BLINDAGE" and any(x in prompt.lower() for x in ["appréciation", "appreciation", "commentaire", "aucun lot"])
        est_cas_blindé_racine = (est_date_notes_direct or est_erreur_validation_santorin or est_groupes_direct or est_nouvel_eleve_direct or est_bricolage_note or est_grise_direct or est_inapte_santorin_direct or est_remplacement_reunion_direct or est_santorin_direct or est_tasa_direct or est_cm_posterieur_direct or est_blessure_choc_direct or est_unss_absence_direct or est_transfert_doublon_direct)

        # Moteur local (Coût 0)
        extraits_locaux = ""
        if openai_api_key and not est_cas_blindé_racine:
            try:
                if mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): extraits_locaux += f"Santorin/Examen: {n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): extraits_locaux += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                elif mode == "textes":
                    mot_cle_local = prompt.lower()
                    for exp in expressions_inutiles: mot_cle_local = mot_cle_local.replace(exp, "")
                    for n in retriever_textes.retrieve(mot_cle_local.strip() if len(mot_cle_local.strip()) > 2 else prompt): extraits_locaux += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"
                elif mode == "peda":
                    for n in retriever_peda.retrieve(prompt): extraits_locaux += f"Ressource Pédagogique Locale : {n.node.text}\n\n"
            except: pass

        extraits_doc = extraits_locaux
        badge, color_card = "INFORMATION", "general-card"

        # --- 🛠️ BLOC MASTER DES CAS BLINDÉS CONFIGURÉS ---
        if est_tasa_direct:
            texte_brut = extraits_doc; badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"
            
        elif est_date_notes_direct:
            texte_brut = "<h3>📊 CALENDRIER & DATES DE REMISE DES NOTES</h3><strong>Statut administratif : Spécificités académiques locales.</strong><br>Les dates limites de saisie étant différentes pour chaque académie, rapprochez-vous de vos coordonnateurs ou de votre secrétariat de direction. Seuls les calendriers émis par la Division des Examens et Concours (DEC) font foi."
            badge, color_card = ("📊 EXAMENS & SANTORIN" if mode == "examens" else "🛠️ PROTOCOLE IPACK"), ("santorin-card" if mode == "examens" else "general-card")
            
        elif est_erreur_validation_santorin:
            texte_brut = """<h3>📊 EXAMENS & SANTORIN : ERREUR DE SAISIE APRÈS VALIDATION</h3><strong>Statut administratif : Clôture définitive du lot par le correcteur.</strong><br><ul><li><strong>Étape 1 :</strong> Ne tentez pas de manipuler l'interface. Prévenez immédiatement le secrétariat de direction de votre établissement (Chef d'établissement).</li><li><strong>Étape 2 :</strong> Le chef d'établissement ou le coordonnateur doit contacter sans délai le gestionnaire de la Division des Examens et Concours (DEC) pour demander un <strong>[Renvoi en modification]</strong>.</li><li><strong>Étape 3 :</strong> Une fois le dossier libéré, l'icône "crayon" redevient active dans Santorin. Vous pouvez écraser la note et valider à nouveau.</li><li>⚠️ En cas de fermeture définitive des serveurs académiques, transmettez le dossier papier pour arbitrage à la <strong>CAHPN</strong>. Au retour de la commission, le chef d'établissement déverrouillera informatiquement le lot afin que vous puissiez saisir vous-même la note définitive validée par la commission.</li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_sss_direct:
            texte_brut = "<h3>🛠️ IPACKEPS : DOSSIER SSS OU BILAN VERROUILLÉ</h3><strong>Statut : Lecture seule absolue.</strong><br>Contactez immédiatement votre Correspondant iPackEPS de bassin ou l'équipe des IA-IPR. Seuls ces profils possèdent les droits master pour appliquer la commande <strong>[Renvoyer en modification]</strong> dans leur console d'administration."
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif est_groupes_direct:
            texte_brut = "<h3>🛠️ IPACKEPS : CONFIGURATION DES CLASSES ET GROUPES</h3>➔ Étape 1 : Accédez au menu supérieur **[Dossiers]**.<br>➔ Étape 2 : Allez dans **[Dossier EPS]** > **[Classes]** > **[Configuration des Classes]** pour associer chaque division à son cycle.<br>➔ Étape 3 : Allez dans **[Organisation des Classes]** pour valider la répartition (Générale, Technologique ou Pro).<br>➔ Étape 4 : Rendez-vous dans le module **[Mes Élèves]** pour injecter le fichier d'extraction Pronote."
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_nouvel_eleve_direct:
            texte_brut = """<h3>🛠️ IPACKEPS : AJOUTER UN ÉLÈVE ARRIVANT</h3><strong>Nomenclature officielle : Interdiction de création manuelle isolée.</strong><br><ul><li><strong>Étape 1 :</strong> Assurez-vous auprès du secrétariat que le nouvel élève est enregistré dans la base nationale <strong>SIÈCLE</strong>.</li><li><strong>Étape 2 :</strong> Générez ou demandez une nouvelle extraction des élèves (XML/CSV) depuis Pronote.</li><li><strong>Étape 3 :</strong> Dans iPackEPS, ouvrez le module **[Mes Élèves]** et cliquez sur **[Importer un fichier d'élèves]**.</li><li><strong>Étape 4 :</strong> Téléversez le fichier. L'application fusionne les bases et ajoute l'arrivant sans altérer les notes existantes.</li></ul>"""
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif est_transfert_doublon_direct:
            texte_brut = """<h3>🛠️ IPACK_TRANSFERT : ÉLÈVE MUTÉ D'UN AUTRE ÉTABLISSEMENT</h3><strong>Réglementation CCF : Reprise obligatoire des notes certifiées.</strong><br><ul><li><strong>Étape 1 :</strong> Ne recréez pas l'élève manuellement. Demandez au secrétariat de valider son intégration pédagogique via <strong>SIÈCLE</strong> pour qu'il descende dans ton Pronote.</li><li><strong>Étape 2 :</strong> Exigez le livret officiel de CCF (Bordereau de notes) visé et signé par le chef d'établissement d'origine.</li><li><strong>Étape 3 :</strong> Procédez à l'import XML de ta classe dans iPackEPS pour faire apparaître l'élève.</li><li><strong>Étape 4 :</strong> Saisissez manuellement dans iPackEPS les notes brutes d'épreuves déjà passées dans l'ancien établissement. En cas de blocage informatique ou d'APSA non concordante, transmettez le dossier papier à la <strong>CAHPN</strong>. Au retour de la commission, le chef d'établissement déverrouillera le lot pour saisie par l'enseignant.</li></ul>"""
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_bricolage_note:
            texte_brut = """<h3>🛑 RÉGLEMENTATION CCF : CANDIDAT AVEC UNE SEULE NOTE VALIDE (NOTE UNIQUE)</h3><strong>Cadre réglementaire national (Bac GT) : Impossibilité administrative de calcul automatique.</strong><br><ul><li><strong>Règle d'or :</strong> Au Bac GT, l'évaluation repose sur un ensemble d'APSA. Si un élève se blesse ou accumule des incidents et ne dispose au final que d'une **seule note valide** à l'année (comme dans ton cas de figure AB+DI+14), l'application bloque le calcul automatique de la moyenne.</li><li><strong>Interdiction absolue de forcer :</strong> Il est strictement interdit d'effectuer un calcul manuel, un prorata artificiel ou d'entrer une fausse note pour tenter de débloquer le système.</li><li><strong>Saisie impérative dans Santorin :</strong> Ne laissez JAMAIS de case vide. Dans Santorin, une case vide signifie "non évalué" et interdira la clôture de votre lot. Cliquez sur le **[Crayon]** d'édition de l'élève et sélectionnez scrupuleusement les statuts réglementaires (ex: **[DI]** pour la dispense en gym, et **[AB]** pour l'absence injustifiée) dans le menu déroulant des **[Notes particulières]**.</li><li><strong>Arbitrage et circuit final (CAHPN) :</strong> Une fois les lignes complétées, validez votre lot. Le dossier sera transmis à la <strong>CAHPN</strong> (Commission Académique d'Harmonisation des Protocoles et des Notes). ⚠️ La CAHPN ne saisit pas directement les modifications informatiques. C'est au retour de la commission que le chef d'établissement déverrouille le lot dans l'établissement, permettant ainsi au professeur de saisir manuellement la note définitive validée par la commission.</li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_grise_direct:
            texte_brut = """<h3>📊 EXAMENS & SANTORIN : CASES OU CRAYONS GRISÉS</h3><strong>Statut technique : Conflit d'édition ou défaut de déploiement.</strong><br><ul><li><strong>Cas 1 (Correction partagée) :</strong> Si plusieurs correcteurs sont affectés au même lot, dès qu'un collègue ouvre ou édite la copie d'un élève, l'interface bascule en lecture seule (boutons grisés) pour tous les autres afin d'éviter les doublons d'écriture. <strong>Solution : Attendez que le collègue ferme la copie ou se déconnecte d'Arena.</strong></li><li><strong>Cas 2 :</strong> Les cases de saisie restent bloquées tant que le lot d'examen n'est pas déplié. <strong>Solution : Allez dans l'onglet [Lots], cliquez sur [Voir le détail], puis sélectionnez le nom du candidat pour activer la grille.</strong></li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_inapte_santorin_direct:
            texte_brut = """<h3>📊 EXAMENS & SANTORIN : ÉLÈVES INAPTES ET ABSENTS AU CCF</h3><strong>Cadre réglementaire : Saisie obligatoire des notes particulières dans Santorin.</strong><br>➔ Étape 1 : Ouvrez Arena > **[Portail d'accès aux missions]** > **[Notation EPS CCF]**.<br>➔ Étape 2 : Dans votre lot, cliquez sur l'icône "crayon" en bout de ligne du candidat.<br>➔ Étape 3 : Ouvrez le menu déroulant des **[Notes particulières]** :<br><ul><li>🔹 <strong>Dispense (DI) :</strong> Si l'élève présente un certificat médical valide. Neutralise l'APSA (sort de la moyenne sans pénaliser).</li><li>🔹 <strong>Absent (AB) :</strong> En cas d'absence non justifiée (vaut note de zéro).</li><li>🔹 <strong>Épreuve de substitution :</strong> Si l'élève est renvoyé à la session de rattrapage.</li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_remplacement_reunion_direct:
            texte_brut = """<h3>📊 EXAMENS : REMPLACEMENT EN JURY OU SOUS-COMMISSION</h3><strong>Statut juridique : Ordre de mission nominatif impératif avant tout déplacement.</strong><br>➔ Étape 1 : Le secrétariat doit contacter le gestionnaire d'examen à la Division des Examens et Concours (DEC).<br>➔ Étape 2 : Demander l'émission urgente d'un modificatif officiel de convocation au nom du remplaçant pour assurer sa couverture juridique (accident de trajet) et ses frais Chorus DT.<br>➔ Étape 3 : Le secrétariat doit valider la suppléance sur l'application nationale **Imag'in** et éditer la fiche PDF pour basculer informatiquement les accès vers Santorin."""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_cm_posterieur_direct:
            texte_brut = """<h3>📊 EXAMENS & CCF : CERTIFICAT MÉDICAL REMIS APRÈS L'ÉVALUATION</h3><strong>Statut juridique : Non-rétroactivité des dispenses médicales.</strong><br><ul><li><strong>Cas 1 : L'élève a réalisé l'épreuve (Candidat présent) :</strong> Un certificat médical produit ou déposé *après* avoir passé l'évaluation ne peut en aucun cas annuler ou effacer la note obtenue. Tout protocole de CCF débuté et mené à son terme est définitivement dû. L'évaluation est validée, la dispense n'est pas rétroactive.</li><li><strong>Cas 2 : L'élève était absent le jour de l'épreuve :</strong> Le candidat dispose d'un délai rigoureux de <strong>48 heures</strong> pour déposer son certificat médical original au secrétariat de l'établissement.</li><li>➔ Si le délai de 48h est respecté : L'absence est justifiée, cochez <strong>[Épreuve de substitution]</strong> (Rattrapage).</li><li>➔ Si le délai de 48h est dépassé : L'absence est injustifiée, la réglementation impose la saisie de la note particulière <strong>[AB]</strong> (équivaut à un zéro informatique).</li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_blessure_choc_direct:
            texte_brut = """<h3>📊 EXAMENS & CCF : ÉLÈVE BLESSÉ EN PLEIN MILIEU DE L'ÉPREUVE</h3><strong>Réglementation Examens : Interdiction absolue d'inventer ou de proratiser des points.</strong><br><ul><li><strong>Étape 1 :</strong> Interrompez immédiatement l'épreuve et faites raccompagner l'élève à l'infirmerie (déclaration d'accident scolaire obligatoire).</li><li><strong>Étape 2 (Règle d'or) :</strong> Ne tentez pas de "bricoler" une note finale en multipliant les points des premiers passages ou en faisant une moyenne imaginaire.</li><li><strong>Étape 3 (Arbitrage réglementaire) :</strong> </li><li>➔ <strong>Si l'élève a complété une partie significative notée autonome :</strong> L'équipe pédagogique peut décider de noter uniquement ce qui a été produit si la grille certificative le permet. En cas de note unique finale restante, le dossier sera transmis à la <strong>CAHPN</strong> ; au retour de la commission, le chef d'établissement déverrouillera le lot pour saisie par le professeur.</li><li>➔ <strong>Si l'épreuve est tronquée et illisible :</strong> Neutralisez l'épreuve informatiquement en saisissant **[Épreuve de substitution]** (Rattrapage). L'élève sera reconvoqué sur une épreuve de remplacement.</li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_unss_absence_direct:
            texte_brut = """<h3>📊 EXAMENS & CCF : ABSENCE POUR CAUSE DE COMPÉTITION UNSS</h3><strong>Statut administratif : Absence institutionnelle justifiée (Ordre de mission AS).</strong><br><ul><li><strong>Règle réglementaire :</strong> Un élève absent à une épreuve de CCF car il représente l'établissement ou l'académie à un Championnat de France UNSS is considéré comme **justifié institutionnellement**.</li><li><strong>Interdiction :</strong> Ne saisissez jamais la note particulière **[AB]** (Absent), ce qui lui vaudrait un zéro éliminatoire.</li><li><strong>Procédure technique :</strong> Dans l'interface Santorin, cochez la case **[Épreuve de substitution]**. L'élève est réglementairement basculé sur la session de rattrapage de l'établissement pour passer son épreuve ultérieurement. L'enseignant doit exiger la copie de la convocation officielle UNSS pour le dossier d'examen.</li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        else:
            response = Settings.llm.complete(consigne_ia) 
            texte_brut = response.text
            if mode == "ipack" and 'bloc_liens_dynamique' in locals():
                texte_brut += f"\n\n<h3>📁 SOURCES, ARTICLES ET TUTORIELS ÉDITEUR</h3>\n{bloc_liens_dynamique}"
            elif mode == "examens" and 'bloc_liens_dynamique' in locals():
                texte_brut += f"\n\n<h3>📁 CADRE OFFICIEL ET RECOMMANDATIONS</h3>\n{bloc_liens_dynamique}"
        # --- FIN DU BLOC DES COMPOSANTS EN DUR ---
        
        # Filtre Regex de sécurité pour forcer l'affichage orange des textes de loi (CORRIGÉ AU SCALPEL ICI : texte_brut partout)
        texte_brut = re.sub(r'(Article\s+\d+[-–\w]*|Loi\s+du\s+\d+\s+\w+\s+\d+|RGPD|Code\s+de\s+l\'éducation)', r'<span class="law-highlight">\1</span>', texte_brut)
        texte_brut = texte_brut.replace('<span class="law-highlight"><span class="law-highlight">', '<span class="law-highlight">').replace('</span></span>', '</span>')
        re_links = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        texte_brut = re_links
        
        # SÉCURISATION DU RENDU (Remplacement des retours chariots)
        texte_final = texte_brut.replace("\n", "").replace("\r", "").replace("<p>", "").replace("</p>", "<br>").replace(chr(10), "<br>")
        formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br>{texte_final}</div>'
        st.session_state.messages_hub.append({"role": "assistant", "type": "text", "content": formatted_answer})
        
        # GESTION SÉCURISÉE DES LIENS VIDÉOS
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)
        for link in youtube_links:
            clean_link = link[0].split('"')[0].split("'")[0].strip()
            st.session_state.messages_hub.append({"role": "assistant", "type": "video", "content": clean_link})
            
        st.rerun()
