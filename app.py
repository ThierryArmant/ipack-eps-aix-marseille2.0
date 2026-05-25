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

# Utilisation d'une chaîne classique sans "f" pour utiliser des accolades CSS normales { }
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
    
    .hub-title h1 { 
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
    
    /* Boutons Inactifs */
    button[kind="secondary"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 12px !important; 
        padding: 0px 4px !important;
        height: 44px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        transition: all 0.3s ease;
    }

    /* Boutons Actifs */
    button[kind="primary"] {
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 12px !important; 
        padding: 0px 4px !important;
        height: 44px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important;
        font-weight: 700 !important;
    }
    
    /* BOUTON NETTOYER */
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {
        background-color: rgba(220, 38, 38, 0.45) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        padding: 7px 10px !important;
        width: 100% !important;
    }
    div.element-container:has(.nettoyer-wrapper) + div.element-container button:hover {
        background-color: rgba(220, 38, 38, 0.65) !important;
    }
    
    /* CARTES DE RÉPONSE */
    .santorin-card, .general-card, .securite-card { 
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
    
    .santorin-card p, .general-card p, .securite-card p, .santorin-card div, .general-card div, .securite-card div, .santorin-card span, .general-card span, .securite-card span, .santorin-card li, .general-card li, .securite-card li { 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
        font-weight: 400 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    .santorin-card strong, .general-card strong, .securite-card strong {
        font-weight: 700 !important; 
        color: #FFFFFF !important;
    }

    .santorin-card a, .general-card a, .securite-card a, .santorin-card a *, .general-card a *, .securite-card a * {
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9) !important;
    }
    .santorin-card a:hover, .general-card a:hover, .securite-card a:hover {
        color: #FCD34D !important;
    }
    
    /* Bulle Utilisateur */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { 
        background-color: rgba(255, 255, 255, 0.15) !important; 
        backdrop-filter: blur(6px) !important;
        border-radius: 14px 14px 0px 14px !important; 
        margin-left: 15% !important; 
    }
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
    
    /* FORCE LE BLANC DANS LE CHAT */
    div[data-testid="stChatMessage"] * { color: #FFFFFF !important; }
    
    div[data-testid="stChatMessage"] a, div[data-testid="stChatMessage"] a * {
        color: #FFB020 !important;
        text-decoration: underline !important;
        font-weight: 600 !important;
    }
    div[data-testid="stChatMessage"] a:hover {
        color: #FCD34D !important;
    }

    /* ======================================================================
        ANCRAGE MAGIQUE DE L'EXPANDER TOUT EN BAS À GAUCHE (PARQUET)
        ====================================================================== */
    div[data-testid="stExpander"] {
        position: fixed !important;
        bottom: 14px !important;
        left: 16px !important;
        width: auto !important;
        min-width: 260px !important;
        max-width: 380px !important;
        background-color: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 6px !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.6) !important;
        z-index: 999999 !important;
        margin: 0 !important;
    }
    /* En-tête de l'expander */
    div[data-testid="stExpander"] summary {
        padding: 6px 12px !important;
    }
    div[data-testid="stExpander"] summary p {
        color: #94A3B8 !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="stExpander"] summary:hover p {
        color: #38BDF8 !important;
    }
    /* Intérieur console technique */
    div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
        font-size: 11px !important;
        font-family: monospace !important;
        color: #38BDF8 !important;
    }
    
    </style>
""".replace('__URL_FOND__', f"{github_url}{img_fond}")

st.markdown(css_pur, unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'INTELLIGENCE ARTIFICIELLE & DU CERVEAU UNIQUE
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

def trouver_chemin_pierre():
    chemins_possibles = ["gere_par_pierre.txt", "data/gere_par_pierre.txt"]
    for ch in chemins_possibles:
        if os.path.exists(ch):
            return ch
    return None

def obtenir_cle_fichier():
    chemin = trouver_chemin_pierre()
    if chemin:
        return os.path.getmtime(chemin)
    return 0.0

# RADAR DE LECTURE FORCÉ HORS CACHE
chemin_detecte = trouver_chemin_pierre()
contenu_global_pierre = ""
status_radar = "❌ ERREUR : 'gere_par_pierre.txt' introuvable à la racine de GitHub !"

if chemin_detecte:
    for encodage in ["utf-8", "utf-8-sig", "latin-1", "utf-16", "cp1252"]:
        try:
            with open(chemin_detecte, "r", encoding=encodage) as f:
                texte_charge = f.read()
            if texte_charge.strip():
                contenu_global_pierre = texte_charge
                status_radar = f"📁 BASE CHARGÉE : {len(contenu_global_pierre)} caractères lus en [{encodage}]."
                break
        except:
            continue

# BASE DE CONNAISSANCES CENTRALISÉE (VECTORISATION)
@st.cache_resource
def initialiser_base_unique(cle_timestamp, texte_connaissances):
    if texte_connaissances.strip():
        doc = Document(text=texte_connaissances, metadata={"source": "Cerveau Unique de Pierre"})
        return VectorStoreIndex.from_documents([doc]).as_retriever(similarity_top_k=5)
    return None

timestamp_fichier = obtenir_cle_fichier()
retriever_unique = initialiser_base_unique(timestamp_fichier, contenu_global_pierre)

class RetrieverSecours:
    def retrieve(self, prompt): return []

if retriever_unique is None:
    retriever_unique = RetrieverSecours()

retriever_santorin = retriever_unique
retriever_ipack = retriever_unique
retriever_textes = retriever_unique
retriever_peda = retriever_unique

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
    "peda": "🔍 Mode Actif : Questions Pédagogiques, Didactiques & Pratiques de Terrain",
    "textes": "🔒 Mode Actif : Sécurité & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

if "active_module" not in st.session_state:
    st.session_state.active_module = "peda"

titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Questions Pédagogiques")

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
    if st.button("📊 Examens & Santorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"
        st.session_state.messages_hub = []
        st.rerun()

with col_b3:
    if st.button("🔍 Pédagogie & Didactique", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "peda" else "secondary"):
        st.session_state.active_module = "peda"
        st.session_state.messages_hub = []
        st.rerun()

with col_b4:
    if st.button("🔒 Sécurité & Réglementation", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
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
            ⚠️ <strong>Avertissement – Bien que basées sur les textes officiels, ces réponses ne remplacent pas les autorités académiques. En cas de doute juridique ou de sinistre, contactez impérativement : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.active_module == "peda":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            💡 <strong>Exemples de recherches dans cet onglet :</strong> Projets pédagogiques, compétences visées, fonctionnement de l'AS / UNSS, gestion de classe, ressources par APSA, projets transversaux (SRE, Savoir Rouler, etc.).
        </span>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Conseil Flux Mixtes :</strong> Certaines questions touchent à la fois à la technique (iPackEPS) et à la réglementation (Santorin). N'hésitez pas à tester votre recherche dans ces deux onglets pour croiser les sources.
        </span>
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
    prompt = st.chat_input("Posez votre question institutionnelle, technique ou juridique ici...", key="chat_main")

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA (CONSOLIDATION FINALE - PRIORITÉ DICTIONNAIRE)
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        if isinstance(m["content"], str) and m["content"].startswith("VIDEO_URL:"):
            url_video = m["content"].replace("VIDEO_URL:", "").strip()
            st.video(url_video)
        else:
            st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Liste globale des domaines académiques EPS
domaine_eps_france = [
    "eduscol.education.gouv.fr", "eps.ac-aix-marseille.fr", "eps.ac-amiens.fr", "eps.ac-besancon.fr", 
    "eps.ac-bordeaux.fr", "eps.ac-normandie.fr", "eps.ac-clermont.fr", "eps.ac-corse.fr", 
    "eps.ac-creteil.fr", "eps.ac-dijon.fr", "eps.ac-grenoble.fr", "eps.ac-lille.fr", 
    "eps.ac-limoges.fr", "eps.ac-lyon.fr", "eps.ac-montpellier.fr", "eps.ac-nancy-metz.fr", 
    "eps.ac-nantes.fr", "eps.ac-nice.fr", "eps.ac-orleans-tours.fr", "eps.ac-paris.fr", 
    "eps.ac-poitiers.fr", "eps.ac-reims.fr", "eps.ac-rennes.fr", "pedagogie.ac-strasbourg.fr", 
    "eps.ac-toulouse.fr", "eps.ac-versailles.fr", "eps.ac-guadeloupe.fr", "eps.ac-guyane.fr", 
    "eps.ac-martinique.fr", "eps.ac-mayotte.fr", "eps.ac-reunion.fr"
]

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white;'>{prompt}</span>"})
    
    with st.spinner("Je recherche les documents et ressources pédagogiques..."):
        extraits_doc = ""
        mode = st.session_state.active_module
        
        # 1. MOTEUR WEB (Tavily)
        if tavily_api_key:
            try:
                if mode == "textes":
                    requete_blindee = f"{prompt} jurisprudence administrative responsabilité commune EPS"
                    domains = ["legifrance.gouv.fr", "education.gouv.fr"] + domaine_eps_france
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
                else:
                    requete_blindee = f"{prompt} EPS programme officiel"
                    domains = ["eduscol.education.gouv.fr", "unss.org"]
                
                payload = {"api_key": tavily_api_key, "query": requete_blindee, "search_depth": "advanced", "include_domains": domains}
                if mode == "ipack": payload["exclude_domains"] = exclude
                
                res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                if res.status_code == 200:
                    for item in res.json().get("results", []): 
                        extraits_doc += f"Source Web ({item['title']}): {item['content']} - URL: {item['url']}\n\n"
            except: pass

        # 2. CONTEXTE LOCAL
        if openai_api_key:
            try:
                if mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): extraits_doc += f"Santorin/Examen: {n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): extraits_doc += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                elif mode == "textes":
                    for n in retriever_textes.retrieve(prompt): extraits_doc += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"
                elif mode == "peda":
                    for n in retriever_peda.retrieve(prompt): extraits_doc += f"Ma base pédagogique (Fiche/Éval) : {n.node.text}\n\n"
            except: pass

        # 3. IDENTITÉ ET RÈGLES DE PRIORITÉ
        règle_priorité = "DIRECTIVE ABSOLUE : Tu es l'expert technique EPS Aix-Marseille. Priorise EXCLUSIVEMENT les définitions et procédures contenues dans le 'Dictionnaire de Référence' fourni. Si l'information n'y est pas, réponds : 'Je ne dispose pas de la procédure officielle dans mon dictionnaire'."
        filtre_pierre = "\nMÉTHODE : 1. Analyse des risques. 2. Procédure technique fléchée (→). 3. Traçabilité."
        consigne_video = "\nVidéo : Si une vidéo spécifique est dans le contexte, affiche : '[Regarder le tutoriel](URL)'."

        # --- ROUTAGE ET PERSONAS (VERROUILLAGE) ---
        if mode == "examens":
            system_rules = "Expert EPS Aix-Marseille. DEC = Division des Examens et Concours. Santorin = saisie. Cyclades = gestion."
            p = prompt.lower()
            if any(x in p for x in ["indisponibilité", "gymnase", "inondé", "force majeure", "matériel"]):
                instruction = "PROCÉDURE FORCE MAJEURE : 1. NE JAMAIS SAISIR D'INAPTITUDE MÉDICALE. 2. NE RIEN SAISIR. 3. SIGNALEMENT ÉCRIT IMMÉDIAT À LA DEC."
            elif any(x in p for x in ["distribution", "distribuer", "lots"]):
                instruction = "PROCÉDURE DISTRIBUTION : 1. Onglet 'Distribution de l’épreuve'. 2. Sélectionner groupe. 3. Cliquer 'Distribuer'."
            elif "aucun lot" in p:
                instruction = "PROCÉDURE LOT ABSENT : 1. Vérifier affectation Cyclades. 2. Rejouer l'import Santorin. 3. Signalement DEC si KO."
            else:
                instruction = "PROCÉDURE SAISIE : 1. Bouton 'Choisir les AFLP' = Priorité n°1."
            
            consigne_ia = f"{règle_priorité}\n{system_rules}\nRÈGLE : {instruction}\n{consigne_video}\nContexte : {extraits_doc}\nQuestion : {prompt}"
            badge, color_card = "📊 RÉGLEMENTATION SANTORIN", "santorin-card"

        elif mode == "ipack":
            consigne_ia = f"{règle_priorité}\nTu es expert technique iPackEPS. INTERDICTION : Aucune interopérabilité avec Cyclades. Gestion exclusive via DEC.\nContexte : {extraits_doc}\nQuestion : {prompt}"
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
        
        elif mode == "textes":
            consigne_ia = f"{règle_priorité}\nTu es l'expert juridique EPS.\nCanva: 1. SITUATION, 2. ARBITRAGE, 3. RECOURS.\nContexte: {extraits_doc}\nQuestion: {prompt}"
            badge, color_card = "⚖️ CADRE JURIDIQUE", "securite-card"
            
        elif mode == "peda":
            consigne_ia = f"{règle_priorité}\nTu es un documentaliste EPS expert. Extrais les liens officiels ou génère une fiche technique complète.\nContexte : {extraits_doc}\nQuestion : {prompt}"
            badge, color_card = "🔍 CHASSEUR DE RESSOURCES", "general-card"
            
        else:
            consigne_ia = f"{règle_priorité}\nTu es l'Expert Pédagogique EPS.\nContexte: {extraits_doc}\nQuestion : {prompt}"
            badge, color_card = "🔍 CONSEILLER PÉDAGOGIQUE", "general-card"

        # 4. EXÉCUTION ET RENDU
        response = Settings.llm.complete(consigne_ia)
        texte_brut = response.text
        
        # Formatage liens/vidéos/tableaux
        texte_brut = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)
        
        # ... (Tableaux et rendu HTML identiques à la version précédente) ...
        texte_html = texte_brut.replace(chr(10), "<br>")
        formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_html}</div>'
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        for link in youtube_links: st.session_state.messages_hub.append({"role": "assistant", "content": f"VIDEO_URL:{link[0]}"})
        st.rerun()

# ======================================================================
# 10. ZONE TECHNIQUE GHOST
# ======================================================================
with st.expander("🛠️"):
    st.write(status_radar)
