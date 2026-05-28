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
# 3. INTERFACE GRAPHIQUE ET CONFIGURATION DES LIENS IMAGES
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png" 
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

css_pur = """
    <style>
    /* Règle de sécurité : Force le blanc uniquement sur le texte brut et les listes (libère les liens) */
    .santorin-card, .general-card, .securite-card, .peda-card,
    .santorin-card p, .general-card p, .securite-card p, .peda-card p,
    .santorin-card li, .general-card li, .securite-card li, .peda-card li { 
        color: #FFFFFF !important; 
    }

    /* Règle impérative : Force le Jaune/Orange sur tous les liens hypertextes */
    .santorin-card a, .general-card a, .securite-card a, .peda-card a { 
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 700 !important;
    }
    .santorin-card a:hover, .general-card a:hover, .securite-card a:hover, .peda-card a:hover {
        color: #FCD34D !important; 
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
    
    .hub-title {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        flex-grow: 1;
        padding-right: 35px; 
    }
    
    .title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }
    
    .hub-title h1 { 
        color: white !important; 
        margin: 0 !important; 
        font-size: 28px !important; 
        font-weight: 800 !important; 
        line-height: 1.2 !important;
        letter-spacing: 0.5px;
    }
    
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
    
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {
        background-color: rgba(220, 38, 38, 0.45) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        padding: 7px 10px !important;
        width: 100% !important;
        height: 38px !important;
    }
    
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
    .securite-card { border-left: 6px solid #EF4444 !important; } 
    .peda-card { border-left: 6px solid #8B5CF6 !important; } 

    /* RE-CALIBRAGE COMPACT DU MODE PÉDAGOGIE EXCLUSIF */
    .peda-card h3 {
        font-size: 15px !important;
        margin-top: 14px !important;
        margin-bottom: 4px !important;
        color: #C084FC !important;
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
        color: #FFFFFF !important;
        margin-bottom: 3px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }
    .peda-card strong {
        color: #FCD34D !important;
        font-weight: 700 !important;
    }
    .santorin-card strong, .general-card strong, .securite-card strong {
        font-weight: 700 !important; 
        color: #FFFFFF !important;
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
    chemin_dossier = "pierre"
    if os.path.exists(chemin_dossier) and os.path.isdir(chemin_dossier):
        try:
            mtimes = [os.path.getmtime(os.path.join(chemin_dossier, f)) for f in os.listdir(chemin_dossier) if f.endswith((".txt", ".md"))]
            return max(mtimes) if mtimes else 0.0
        except Exception:
            return 0.0
    return 0.0

def charger_consignes_pierre():
    chemin_dossier = "pierre"
    documents_charges = []
    if os.path.exists(chemin_dossier) and os.path.isdir(chemin_dossier):
        try:
            for fichier in os.listdir(chemin_dossier):
                if fichier.endswith((".txt", ".md")):
                    with open(os.path.join(chemin_dossier, fichier), "r", encoding="utf-8") as f:
                        contenu_fichier = f.read()
                    documents_charges.append(Document(text=contenu_fichier, metadata={"source": f"Notes de Pierre - {fichier}"}))
            return documents_charges
        except Exception:
            return []
    return []

@st.cache_resource
def initialiser_base_santorin(cle_fremt):
    docs_santorin = [
        Document(
            text="""Fiche Mémo - Correction Partagée Santorin (DEC / Assistance). La correction partagée ou multiple permet à plusieurs évaluateurs/correcteurs d'intervenir sur un même lot de copies.""",
            metadata={"title": "Fiche Mémo - Correction Partagée Santorin", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf"}
        )
    ]
    docs_santorin.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_ipack(cle_fremt):
    docs_ipack = [
        Document(
            text="""Portail Pilote iPackEPS - Gérer le CCF et les inaptitudes d'EPS.""",
            metadata={"title": "Portail Officiel iPackEPS - Académie de Créteil", "url": "https://eps.ac-creteil.fr/"}
        )
    ]
    docs_ipack.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_textes(cle_fremt):
    docs_textes = []
    fichier_cible = "data/textes/base_textes_officiels.txt"
    if os.path.exists(fichier_cible):
        try:
            docs_textes = SimpleDirectoryReader(input_files=[fichier_cible]).load_data()
        except Exception:
            pass
    
    if not docs_textes:
        docs_textes = [Document(text="Base de données textuelle locale vide ou inaccessible. Vérifiez le chemin data/textes/base_textes_officiels.txt", metadata={"source": "System"})]
        
    docs_textes.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_textes).as_retriever(similarity_top_k=5)

timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)
retriever_peda = retriever_ipack

# ======================================================================
# 5. BANDEAU SUPERIEUR REHAUSSÉ AVEC VRAI COMPTEUR COMPLET
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
# 6. EN-TÊTE DU TABLEAU DE BORD (SYNCHRONISÉ AVEC LES CLÉS)
# ======================================================================
label_titres = {
    "ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF & Inaptitudes)",
    "examens": "📊 Mode Actif : Réglementation Examens & Santorin (Copies Numérisées & Jurys)",
    "peda": "🔍 Mode Actif : Référentiels Institutionnels, APSA & Textes de Cadrage BO",
    "textes": "🔒 Mode Actif : Sécurité & Responsabilité Juridique (Jurisprudences & Textes de Lois)"
}

if "active_module" not in st.session_state:
    st.session_state.active_module = "peda"

titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Référentiels Institutionnels")

st.markdown(f"""
    <div class="column-title-top">
        <span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessous</span>
        <span class="mode-actuel">{titre_affiche}</span>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 7. BOUTONS DE CONTEXTE ALIGNÉS SUR 4 COLONNES
# ======================================================================
col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")

with col_b1:
    if st.button("🛠️ iPackEPS", use_container_width=True, key="btn_ip", type="primary" if st.session_state.active_module == "ipack" else "secondary"):
        st.session_state.active_module = "ipack"
        st.session_state.messages_hub = []
        st.rerun()

with col_b2:
    if st.button("📊 Examens &\nSantorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"
        st.session_state.messages_hub = []
        st.rerun()

with col_b3:
    if st.button("🔍 Cadrage &\nRéférentiels", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "peda" else "secondary"):
        st.session_state.active_module = "peda"
        st.session_state.messages_hub = []
        st.rerun()

with col_b4:
    if st.button("🔒 Sécurité &\nCadres Règl.", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
        st.session_state.active_module = "textes"
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 7B. MESSAGES D'AVERTISSEMENT DYNAMIQUES 
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement Juridique – Les réponses s'appuient sur le Code de l'Éducation, la législation nationale et la jurisprudence des tribunaux (Cadrage Aix-Marseille ciblé en priorité absolue). Elles ne se substituent pas aux circulaires rectorales en cas de contentieux.<strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.active_module == "peda":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            💡 <strong>Rappel Institutionnel :</strong> Cet haut-parleur extrait les repères des Bulletins Officiels (BO) en ciblant prioritairement Édubase et le Conservatoire d'Aix-Marseille. La liberté pédagogique reste sous l'entière responsabilité des équipes locales.
        </span>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; line-height: 1.5;">
        <div style="color: #38BDF8; font-weight: 800; font-size: 14px; text-align: center; margin-bottom: 12px; letter-spacing: 0.5px;">
            🎯 OÙ POSER VOTRE QUESTION ?
        </div>
        <div style="display: flex; gap: 20px; color: #FCD34D; font-size: 13px;">
            <div style="flex: 1; border-right: 1px solid #334155; padding-right: 20px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">🛠️ Menu iPackEPS (Toute l'année)</strong><br>
                <span style="color: #FCD34D !important;">Technique de terrain : configuration de l'application, création des groupes, saisie des notes brutes.</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(248, 113, 113, 0.15); border-left: 3px solid #F87171; border-radius: 4px;">
                    <span style="color: #F87171 !important; font-weight: 800;">⚠️ IMPORTANT INAPTITUDES :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Toutes les questions sur les certificats médicaux, dispenses and saisies d'inaptitude se posent TOUJOURS ici, dans le menu iPackEPS !</span>
                </div>
            </div>
            <div style="flex: 1; padding-left: 5px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">📊 Menu Examens & Santorin (Fin d'année)</strong><br>
                <span style="color: #FCD34D !important;">Administration des examens : remontée officielle des notes du Bac/DNB, correction des lots de copies numériques sur Arena, arbitrages des Jurys Académiques.</span>
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
    if st.button("🧹 Nettoyer", key="clear_all"):
        st.session_state.messages_hub = []
        st.rerun()

with col_action_input:
    prompt = st.chat_input("Posez votre question institutionnelle, technique ou juridique ici...", key="chat_main")

st.markdown("""
    <div style="background-color: #1E293B; padding: 12px 20px; border-radius: 6px; box-shadow: 0px 4px 8px rgba(0,0,0,0.2); margin-top: 10px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; line-height: 1.4;">
        <span style="color: #FCD34D; font-weight: 700; font-size: 13px;">
            ⚠️ 💡 ATTENTION :
        </span>
        <span style="color: #FFFFFF; font-weight: 500; font-size: 13px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
            Pour des raisons pratiques et de mise à jour, votre assistant ne mémorise pas le fil de la conversation. Posez vos questions une par une après les avoir nettoyées.
        </span>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA 
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        if isinstance(m["content"], str) and m["content"].startswith("st.video("):
            exec(m["content"])
        else:
            st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

domaine_eps_france = [
    "eps.ac-aix-marseille.fr", "pedagogie.ac-aix-marseille.fr", "edubase.eduscol.education.fr", "eps.ac-creteil.fr", "eduscol.education.gouv.fr", "eps.ac-amiens.fr", "eps.ac-besancon.fr", 
    "eps.ac-bordeaux.fr", "eps.ac-normandie.fr", "eps.ac-clermont.fr", "eps.ac-corse.fr", 
    "eps.ac-dijon.fr", "eps.ac-grenoble.fr", "eps.ac-lille.fr", "eps.ac-limoges.fr", 
    "eps.ac-lyon.fr", "eps.ac-montpellier.fr", "eps.ac-nancy-metz.fr", "eps.ac-nantes.fr", 
    "eps.ac-nice.fr", "eps.ac-orleans-tours.fr", "eps.ac-paris.fr", "eps.ac-poitiers.fr", 
    "eps.ac-reims.fr", "eps.ac-rennes.fr", "pedagogie.ac-strasbourg.fr", "eps.ac-toulouse.fr", 
    "eps.ac-versailles.fr", "eps.ac-guadeloupe.fr", "eps.ac-guyane.fr", "eps.ac-martinique.fr", 
    "eps.ac-mayotte.fr", "eps.ac-reunion.fr"
]

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white;'>{prompt}</span>"})
    
    with st.spinner("Je recherche les documents et ressources..."):
        extraits_doc = ""
        mode = st.session_state.active_module
        prompt_lower = prompt.lower()
        
        # ------------------------------------------------------------------
        # 1. MOTEUR WEB (Tavily) - AVEC NETTOYAGE DES SCORIES SÉMANTIQUES RÉINJECTÉ
        # ------------------------------------------------------------------
        if tavily_api_key:
            try:
                domains = domaine_eps_france
                requete_blindee = prompt
                exclude = []
                tavily_deja_execute = False

                if mode == "textes":
                    mot_cle = prompt.lower()
                    expressions_inutiles = [
                        "je cherche un texte officiel pour savoir si", "je cherche un texte sur le", 
                        "je cherche un texte sur la", "je cherche un texte sur", "pour savoir si j'ai le droit de",
                        "est-ce que j'ai le droit de", "ai-je le droit de", "est-ce qu'il existe un texte",
                        "trouve moi le texte sur", "trouve moi une circulaire sur", "trouve moi", 
                        "recherche le texte sur", "texte officiel sur", "circulaire concernant", "circulaire sur"
                    ]
                    for exp in expressions_inutiles:
                        mot_cle = mot_cle.replace(exp, "")
                    for verbe in ["savoir si", "refuser une", "refuser un", "concerne le", "concerne la"]:
                        mot_cle = mot_cle.replace(verbe, "")
                        
                    mot_cle = mot_cle.strip() if mot_cle.strip() else prompt
                    domains_prioritaires = ["pedagogie.ac-aix-marseille.fr", "education.gouv.fr", "eduscol.education.gouv.fr", "eps.ac-creteil.fr"]
                    requete_blindee = f"EPS {mot_cle} loi laïcité code de l'éducation circulaire décret arrêté BO"
                    
                    payload = {
                        "api_key": tavily_api_key, 
                        "query": requete_blindee, 
                        "search_depth": "advanced", 
                        "include_domains": domains_prioritaires
                    }
                    res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                    results = res.json().get("results", []) if res.status_code == 200 else []
                    
                    for item in results: 
                        extraits_doc += f"Source Web ({item['title']}): {item['content']} - URL: {item['url']}\n\n"
                    tavily_deja_execute = True

                elif mode == "examens":
                    requete_blindee = f"{prompt} réglementation examen Santorin Cyclades"
                    domains = ["education.gouv.fr"] + domaine_eps_france
                elif mode == "ipack":
                    requete_blindee = f"site:ipackeps.ac-creteil.fr/spip.php?rubrique4 {prompt}"
                    domains = ["ipackeps.ac-creteil.fr"]
                    exclude = ["youtube.com"]
                elif mode == "peda":
                    requete_blindee = f"{prompt} évaluation fiche filetype:pdf"
                    domains = domaine_eps_france

                if not tavily_deja_execute:
                    payload = {"api_key": tavily_api_key, "query": requete_blindee, "search_depth": "advanced", "include_domains": domains}
                    if exclude:
                        payload["exclude_domains"] = exclude
                    res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                    if res.status_code == 200:
                        for item in res.json().get("results", []): 
                            extraits_doc += f"Source Web ({item['title']}): {item['content']} - URL: {item['url']}\n\n"
            except:
                pass

        # ------------------------------------------------------------------
        # 2. CONTEXTE LOCAL (RAG LlamaIndex)
        # ------------------------------------------------------------------
        if openai_api_key:
            try:
                if mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): extraits_doc += f"Santorin/Examen: {n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): extraits_doc += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                elif mode == "textes":
                    for n in retriever_textes.retrieve(prompt): extraits_doc += f"Base Locale Textes Officiels : {n.node.text}\n\n"
                elif mode == "peda":
                    for n in retriever_peda.retrieve(prompt): extraits_doc += f"Base Pédagogique : {n.node.text}\n\n"
            except: 
                pass

        # ------------------------------------------------------------------
        # 3. IDENTITÉ ET CONFIGURATION DES CONSIGNES IA
        # ------------------------------------------------------------------
        règles_or = "RÈGLES D'OR : 1. Loi 1937 (Substitution État). 2. Règle 11 (Structure=Mairie/EPI=Prof). 3. Examens = Mission impérative."
        filtre_pierre = (
            "\n\nMÉTHODE DE RÉPONSE EN 3 PARTIES OBLIGATOIRE (Le 'Filtre Pierre' Ultra-Scannable) :\n"
            "Tu dois STRICTEMENT structurer ta réponse finale selon le plan et les titres exacts suivants. "
            "Interdiction absolue de faire des paragraphes denses. Utilise un format aéré, percutant et très visuel :\n\n"
            "### 1. ANALYSE DES RISQUES\n"
            "- Utilise des listes à puces avec un émoji d'alerte (🛑, ⚠️ ou ⚖️) suivi d'un ancrage en gras qualifiant le risque (ex: 🛑 **Absence non justifiée** : explications).\n\n"
            "### 2. PROCÉDURE TECHNIQUE\n"
            "- Déroule les actions de terrain de manière chronologique.\n"
            "- Commence impérativement CHAQUE étape par une flèche '➔ Étape X (Titre court) : '.\n"
            "- Mets TOUJOURS en gras et entre crochets les boutons ou modules réels de l'interface logicielle s'ils s'appliquent (ex: **[Mes Élèves]**, **[Saisir une inaptitude]**).\n"
            "- S'il y a une interdiction absolue ou un point de sécurité critique, isole-le avec un émoji visible (ex: ⚠️ **ALERTE SÉCURITÉ** : ...).\n\n"
            "### 3. PROTECTION FONCTIONNELLE\n"
            "- Utilise des listes à puces avec des émojis de dossiers/sécurité (📁, 🔓) suivis d'une notion forte en gras (ex: 📁 **Traçabilité** : rappel de la couverture juridique).\n\n"
            "Priorité maximale à la scannabilité graphique immédiate pour un professeur d'EPS."
        )

        if mode == "ipack":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Tu es l'expert informatique et technique iPackEPS pour l'académie d'Aix-Marseille. Tu exclus tout blabla pédagogique.\n"
                f"CONSIGNES INTERNES PRIORITAIRES :\n{verites_terrain_pierre}\n\n"
                "CRITICAL IPACK RULES:\n"
                "- SAISIE INAPTITUDE : Interdiction absolue de taper 'IN' ou 'DI' dans les cases de notes. Passage obligatoire par 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude'.\n"
                "- DEMI-FOND BAC GT : Distinction obligatoire entre l'épreuve nationale 'Courses' et l'activité d'établissement 'Course de demi-fond'. Interdiction stricte de créer des protocoles à 2 épreuves.\n"
                "- SUPPRESSION DE PROTOCOLE : Le bouton 'Supprimer' direct n'existe pas dans l'onglet Protocoles. Il faut désaffecter les Groupes et séquences rattachés en amont.\n"
                "- NOTE UNIQUE CCF : iPackEPS bloque le calcul automatique. Transmission au Jury via Cyclades.\n\n"
                f"Contexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif mode == "examens":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Tu es l'expert administratif et technique Santorin, Cyclades et Imag'in pour l'académie d'Aix-Marseille.\n"
                f"CONSIGNES INTERNES PRIORITAIRES :\n{verites_terrain_pierre}\n\n"
                "CRITICAL EPS EXAM RULES (AIX-MARSEILLE):\n"
                "- DATE LIMITE : La date butoir impérative de saisie pour Aix-Marseille est le 30 mai 2026 au soir.\n"
                "- AFLP GRISÉS / INACTIFS : Cliquer sur le bouton spécifique 'Choisir les AFLP' pour activer la grille.\n"
                "- BOUTON AJOUTER GRISÉ / REMPLAÇANT : Le bouton [Ajouter] est en panne. Procédure de contournement : 1. Aller dans le détail du lot du 1er correcteur. 2. Ouvrir [Candidats]. 3. Tout sélectionner. 4. Cliquer sur **[Déplacer vers un nouveau lot]**. 5. Choisir le remplaçant.\n\n"
                f"Contexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "📊 RÉGLEMENTATION SANTORIN", "santorin-card"

        elif mode == "textes":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Expert juridique officiel EPS. Rédige de façon froide et factuelle, sans pédagogie.\n"
                "CRITICAL FRAMEWORK DISTINCTION (EPS vs AS/UNSS):\n"
                "- CADRE EPS (Obligatoire / Temps scolaire) : Responsabilité de l'État (Loi de 1937 / Art L. 911-4 du Code de l'éducation).\n"
                "- CADRE AS / UNSS (Volontaire / Mercredi après-midi) : Régime associatif (Loi 1901). Si un parent transporte des élèves avec accord écrit, c'est l'assurance MAIF collective de l'AS/UNSS qui couvre au civil.\n\n"
                "RÈGLE IMPÉRATIVE SUR LES LIENS ET ERREURS 404 :\n"
                "Génère obligatoirement au moins un lien de requête dynamique basé sur les mots-clés de la question sous l'une de ces formes exactes au cours de ton analyse :\n"
                "- 🔗 [Consulter les textes mis à jour sur Légifrance](https://www.legifrance.gouv.fr/search/all?tab_selection=all&searchField=ALL&query=MOTS_CLÉS&page=1)\n"
                "- 🔗 [Vérifier la réglementation en vigueur sur Service-Public.fr](https://www.service-public.fr/recherche?keyword=MOTS_CLÉS)\n"
                "- 🔗 [Consulter les fiches de sécurité de la CNIL](https://www.cnil.fr/fr/recherche?search_api_fulltext=MOTS_CLÉS)\n"
                "⚠️ OBLIGATION : Remplace 'MOTS_CLÉS' par les termes juridiques de la demande en minuscules séparés par des '+' (ex: droit+image+mineur+ecole).\n\n"
                f"Contexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif mode == "peda":
            consigne_ia = (
                f"ROLE : Tu es un expert pédagogique de haut niveau en EPS (IA-IPR). Tu as accès à cette liste d'académies : {domaine_eps_france}.\n"
                "MISSION : Réponds sous forme de FICHE TECHNIQUE SÉQUENCÉE, ULTRA-DÉTAILLÉE et directement exploitable sur le terrain.\n"
                "FORMATAGE HTML STRICT (Interdiction absolue de Markdown) :\n"
                "1. Utilise uniquement <h3> pour les titres.\n"
                "2. Utilise <ul> and <li> pour toutes les listes.\n"
                "3. Utilise <br> pour les sauts de ligne.\n"
                "RÈGLE LIENS : Détermine l'APSA principale de la demande (ex: gymnastique). Construis obligatoirement 3 liens Google ultra-ciblés au format exact suivant :\n"
                "1. <a href='https://edubase.eduscol.education.fr/recherche?q=NOM_APSA' target='_blank' rel='noopener noreferrer'>📥 Fiche NOM_APSA - Base Nationale ÉDUBASE EPS</a><br>\n"
                "2. <a href='https://www.google.com/search?q=site:pedagogie.ac-aix-marseille.fr+NOM_APSA+fiche+evaluation+EPS' target='_blank' rel='noopener noreferrer'>📥 Fiche NOM_APSA - Académie d'Aix-Marseille</a><br>\n"
                "3. <a href='https://www.google.com/search?q=site:eps.ac-creteil.fr+NOM_APSA+fiche+evaluation+EPS' target='_blank' rel='noopener noreferrer'>📥 Fiche NOM_APSA - Académie de Créteil</a><br>\n\n"
                "STRUCTURE IMPÉRATIVE À REMPLIR :\n"
                "<h3>📋 INTITULÉ DE LA FICHE</h3><strong>Activité exacte, Champ d'Apprentissage (CA) et niveau</strong><br>"
                "<h3>🌐 ANCRAGE INSTITUTIONNEL</h3><ul><li><strong>Domaines du Socle Commun :</strong> [domaines]</li><li><strong>Compétences Générales EPS :</strong> [compétences]</li><li><strong>Attendus de Fin de Cycle (AFC) :</strong> [AFC]</li></ul>"
                "<h3>🎯 OBJECTIFS PÉDAGOGIQUES</h3>"
                "<h3>🏃‍♂️ CADRE SÉCURITÉ & AMÉNAGEMENT</h3>"
                "<h3>🛠️ SITUATIONS D'APPRENTISSAGE</h3>"
                "<h3>📊 CRITÈRES D'ÉVALUATION</h3>"
                "<h3><h3>💾 RESSOURCES ACADÉMIQUES</h3>(Liens ici)"
                f"\nContexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "🎓 PÉDAGOGIE EPS", "peda-card"

        # ------------------------------------------------------------------
        # 4. RENDU ET PARSING SECURISE (CONVERTISSEUR SÉMANTIQUE DE BLINDAGE DU DOM)
        # ------------------------------------------------------------------
        response = Settings.llm.complete(consigne_ia)
        texte_brut = response.text
        
        # Interception des vidéos YouTube
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)

        if mode == "peda":
            # Injection automatique des attributs de sécurité et styles sur tous les liens Markdown détectés
            texte_brut = re.sub(
                r'\[([^\]]+)\]\((https?://[^\)]+)\)', 
                r'<a href="\2" target="_blank" rel="noopener noreferrer" style="color: #FFB020 !important; text-decoration: underline; font-weight: 700;">\1</a>', 
                texte_brut
            )
            texte_final = texte_brut.replace("\n", "").replace("\r", "").replace("<p>", "").replace("</p>", "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br>{texte_final}</div>'
        
        else:
            # CONVERTISSEUR SÉMANTIQUE INTERNE POUR TOUS LES AUTRES MODES (Évite de casser le DOM et libère les clics)
            # 1. Parsing propre des liens Markdown
            texte_brut = re.sub(
                r'\[([^\]]+)\]\((https?://[^\)]+)\)', 
                r'<a href="\2" target="_blank" rel="noopener noreferrer" style="color: #FFB020 !important; text-decoration: underline; font-weight: 700;">\1</a>', 
                texte_brut
            )
            
            # 2. Traduction des titres Markdown en HTML sémantique
            lignes = texte_brut.split("\n")
            html_lignes = []
            dans_liste = False
            
            for index, ligne in enumerate(lignes):
                ligne_strip = ligne.strip()
                if not ligne_strip:
                    if dans_liste:
                        html_lignes.append("</ul>")
                        dans_liste = False
                    continue
                
                if ligne_strip.startswith("###"):
                    if dans_liste:
                        html_lignes.append("</ul>")
                        dans_liste = False
                    titre = ligne_strip.replace("###", "").strip()
                    html_lignes.append(f"<h3>{titre}</h3>")
                elif ligne_strip.startswith("-") or ligne_strip.startswith("*"):
                    if not dans_liste:
                        html_lignes.append("<ul>")
                        dans_liste = True
                    puce = ligne_strip[1:].strip()
                    html_lignes.append(f"<li>{puce}</li>")
                else:
                    if dans_liste:
                        html_lignes.append("</ul>")
                        dans_liste = False
                    html_lignes.append(f"<p>{ligne_strip}</p>")
            
            if dans_liste:
                html_lignes.append("</ul>")
            
            texte_final = "".join(html_lignes)

            # Injection Python stricte des liens profonds selon le contexte
            if mode == "textes":
                liens_fixes_publics = """
                <br><h3>4. RECOURS &amp; LIENS INSTITUTIONNELS RECOMMANDÉS</h3>
                <ul>
                <li><a href="https://www.pedagogie.ac-aix-marseille.fr/jcms/c_11140963/fr/les-textes-officiels" target="_blank" rel="noopener noreferrer">Recueil Pédagogique et Réglementaire – Académie d'Aix-Marseille</a></li>
                <li><a href="https://eps.ac-creteil.fr/spip.php?rubrique7" target="_blank" rel="noopener noreferrer">Dossiers Contentieux &amp; FAQ Sécurité – Académie de Créteil</a></li>
                <li><a href="https://eduscol.education.gouv.fr/" target="_blank" rel="noopener noreferrer">Portail Sécurité et Protection de l'Élève – Éduscol</a></li>
                </ul>
                """
                texte_final = texte_final + liens_fixes_publics
            elif mode == "examens":
                liens_fixes_publics = """
                <br><h3>4. RÉFÉRENCES ET LIENS DE RECHERCHE</h3>
                <ul>
                <li><a href="https://www.pedagogie.ac-aix-marseille.fr/jcms/c_11140964/fr/examens" target="_blank" rel="noopener noreferrer">Cadrage Officiel et Règlements des Examens – Académie d'Aix-Marseille</a></li>
                </ul>
                <h3>5. RECOURS &amp; LIENS INSTITUTIONNELS DIRECTS</h3>
                <ul>
                <li><a href="https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf" target="_blank" rel="noopener noreferrer">Manuel Numérique Santorin : Correction Partagée (PDF)</a></li>
                </ul>
                """
                texte_final = texte_final + liens_fixes_publics
            elif mode == "ipack":
                liens_fixes_publics = """
                <br><h3>4. RÉFÉRENCES ET LIENS DE RECHERCHE</h3>
                <ul>
                <li><a href="https://eps.ac-creteil.fr/" target="_blank" rel="noopener noreferrer">Serveur National Pilote de l'Application – Académie de Créteil</a></li>
                </ul>
                <h3>5. RECOURS &amp; LIENS INSTITUTIONNELS DIRECTS</h3>
                <ul>
                <li><a href="https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf" target="_blank" rel="noopener noreferrer">Guide Technique d'Utilisation Interface Enseignant (PDF)</a></li>
                </ul>
                """
                texte_final = texte_final + liens_fixes_publics

            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
            
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        
        # Exécution automatique des modules vidéo YouTube trouvés
        for link in youtube_links:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"st.video('{link[0]}')"})
        st.rerun()
