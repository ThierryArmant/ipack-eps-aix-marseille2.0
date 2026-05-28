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

    .santorin-card h3, .general-card h3, .securite-card h3, .peda-card h3 {
        font-size: 15px !important; 
        margin-top: 14px !important; 
        margin-bottom: 6px !important; 
        color: #FCD34D !important; 
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
            text="""Fiche Mémo - Correction Partagée Santorin (DEC / Assistance). 
            La correction partagée ou multiple permet à plusieurs évaluateurs/correcteurs d'intervenir sur un même lot de copies. 
            Dans Santorin, un chef d'établissement peut ajouter manuellement un deuxième évaluateur ou correcteur à un lot via le portail Arena / Cyclades. 
            Procédure : Aller dans l'onglet 'Lots', cliquer sur 'Voir le détail', aller sur l'onglet 'Correcteurs' puis cliquer sur le bouton 'Ajouter'.
            Verrouillage : Lorsqu'un correcteur édite une copie, l'autre bascule temporairement en lecture seule.""",
            metadata={"title": "Fiche Mémo - Correction Partagée Santorin", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf"}
        ),
        Document(
            text="""Fiche Mémo - Processus de Distribution de Lots Santorin en Établissement. 
            Gestion, paramétrage des tailles de groupes et distribution automatique ou manuelle des lots de copies numérisées vers les correcteurs par les coordonnateurs de l'établissement.""",
            metadata={"title": "Fiche Mémo - Processus de Distribution de Lots", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fic18-fichememo-etablissement-distribuer.pdf"}
        ),
        Document(
            text="""Guide Utilisateur Santorin - Ouvrir, annoter et corriger une copie numérisée. 
            Tutoriel pas-à-pas : liste des candidats anonymisés, outils d'annotation intégrés (surlignage, stylo, commentaires), saisie des notes par question ou globale, validation du lot. Utilisation de la messagerie interne (icône enveloppe) pour contacter les coordonnateurs.""",
            metadata={"title": "Guide Utilisateur - Ouvrir et corriger une copie avec Santorin", "url": "https://pedagogie.ac-orleans-tours.fr/documents/pdf/lettres_tutoriels_ouvrir_et_corriger_une_copie_avec_santorin__2_.pdf"}
        ),
        Document(
            text="""Portail d'assistance et ressources Dématérialisation Académie de Bordeaux. 
            Accès à la Base École de Santorin (environnement de test/formation), fiches d'aide à la connexion, procedures d'urgence en cas de page manquante ou copie mal numérisée.""",
            metadata={"title": "Portail Dématérialisation - Académie de Bordeaux", "url": "https://www.ac-bordeaux.fr/dematerialisation-126581"}
        ),
        Document(
            text="""Espace d'aide et tutoriels Santorin - Académie de Lille. 
            Guides d'utilisation pour le DNB, le Baccalauréat et les BTS. Procédures pour s'enregistrer, traiter les lots et demander des corrections d'affectation via l'enveloppe de communication.""",
            metadata={"title": "Espace d'Aide Santorin - Académie de Lille", "url": "https://pedagogie.ac-lille.fr/lettres/aide-santorin/"}
        ),
        Document(
            text="""Guide technique d'installation de Santorin Scan. 
            Documentation sur l'installation, le paramétrage des scanners physiques en établissement, les protocoles réseaux et la configuration des serveurs d'échange sécurisés.""",
            metadata={"title": "Guide d'Installation Santorin Scan", "url": "https://www.toutatice.fr/toutatice-portail-cms-nuxeo/binary/Guide_Installation+scanner_v2.0.4.pdf"}
        )
    ]
    docs_santorin.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_ipack(cle_fremt):
    docs_ipack = [
        Document(
            text="""Portail Pilote iPackEPS - Académie de Créteil. 
            iPackEPS est l'application officielle pour gérer les évaluations d'EPS et le CCF.""",
            metadata={"title": "Portail Officiel iPackEPS - Académie de Créteil", "url": "https://eps.ac-creteil.fr/"}
        ),
        Document(
            text="""Guide Pratique Utilisateur de l'interface Professeur iPackEPS - Académie de Normandie.
            SAISIE DES CERTIFICATS MÉDICAUX & DISPENSES : La saisie des inaptitudes se fait UNIQUEMENT dans le menu 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude'. RÈGLE IMPÉRATIVE : On ne peut jamais taper directement 'IN' ou 'DI' à la main dans la case d'une note brute, le statut est généré automatiquement par l'application.
            RÈGLE DU CERTIFICAT MIXTE ET ABSENCE AU BAC : Pour valider le CCF de l'épreuve d'EPS au Baccalauréat, la réglementation nationale impose que l'élève dispose d'au moins DEUX notes valides dans deux épreuves de familles différentes.""",
            metadata={"title": "Guide Utilisateur Interface Professeur iPackEPS (PDF)", "url": "https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf"}
        ),
        Document(
            text="""Note Technique de Liaison Examens / Cyclades / Santorin - Académie de Versailles.
            Rappelle qu'une absence injustifiée équivaut à 0/20 et compte réglementairement comme une note prise en compte, alors qu'une inaptitude médicale validée neutralise l'épreuve.""",
            metadata={"title": "Note d'Information iPackEPS - Session Examens (PDF)", "url": "https://eps.ac-versailles.fr/IMG/pdf/2025_10_08_info_ipackeps_octobre_2025_-_lyc_cfa.pdf"}
        ),
        Document(
            text="""SITUATIONS RÉGLEMENTAIRES COMPLEXES ET CAS PARTICULIERS (SÉCURITÉ ET INTERFACES) :
            1. CONFLIT MÉDICAL (ANNULATION DE DISPENSE) : Si un certificat d'inaptitude totale annuelle est invalidé en cours d'année, la seule procédure est de MODIFIER LA DATE DE FIN du certificat dans l'onglet Inaptitudes pour l'arrêter juste avant le début du trimestre de reprise.
            2. NOTE UNIQUE À L'ANNÉE : Si un élève se blesse et n'a qu'une seule note au lieu de deux au CCF, iPackEPS bloque le calcul automatique. Le dossier est transmis au Jury Académique via Cyclades.
            3. BOUTON CHANGEMENT D'ACTIVITÉ GRISÉ : Si l'interface refuse de modifier l'activité ou l'option d'un élève pour le trimestre, c'est qu'une note a déjà été saisie. Pour débloquer informatiquement le bouton, l'enseignant doit obligatoirement se rendre dans le menu 'Saisie des notes' de l'activité actuelle, effacer manuellement la note saisie pour rendre la case totalement vide (pas de zéro, juste du vide), puis enregistrer. Le bouton de modification dans la fiche élève sera alors instantanément dégrisé.""",
            metadata={"title": "Fiche des Cas Complexes et Arbitrages Jurys", "url": "https://eps.ac-creteil.fr/"}
        )
    ]
    docs_ipack.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_textes(cle_fremt):
    docs_textes = [
        Document(
            text="""Base de données réglementaire globale pour les textes de lois, décrets officiels et circulaires de sécurité d'un établissement scolaire du second degré.""",
            metadata={"title": "Référentiel National Textes et Lois", "url": "https://www.legifrance.gouv.fr/"}
        )
    ]
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
                    <span style="color: #FFFFFF !important; font-size: 12px;">Toutes les questions sur les certificats médicaux, dispenses et saisies d'inaptitude se posent TOUJOURS ici, dans le menu iPackEPS !</span>
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
        
        mots_terrain = ["fiche", "evaluation", "évaluation", "grille", "bareme", "barème", "cycle", "seance", "séance", "apsa", "volley", "hand", "basket", "badminton", "relais", "natation", "escalade", "gym", "college", "collège"]
        est_demande_fiche = any(mot in prompt_lower for mot in mots_terrain)
        
        verites_terrain_pierre = ""
        try:
            for fichier in os.listdir("."):
                if fichier.endswith((".txt", ".md")) and "pierre" in fichier.lower():
                    with open(fichier, "r", encoding="utf-8") as f:
                        verites_terrain_pierre += f"\n--- REGLES DIRECTES ({fichier}) ---\n" + f.read() + "\n"
        except:
            pass
        
        # ------------------------------------------------------------------
        # 1. MOTEUR WEB (Tavily) - CASCADE HARMONISÉE (LÉGIFRANCE RETIRÉ)
        # ------------------------------------------------------------------
        if tavily_api_key:
            try:
                domains = domaine_eps_france
                requete_blindee = prompt
                exclude = []
                tavily_deja_execute = False

                if mode == "textes":
                    phrase_brute = prompt.lower()
                    scories = [
                        "je cherche un texte officiel pour savoir si", "je cherche un texte sur le", 
                        "je cherche un texte sur la", "je cherche un texte sur", "pour savoir si j'ai le droit de",
                        "est-ce que j'ai le droit de", "ai-je le droit de", "est-ce qu'il existe un texte",
                        "trouve moi le texte sur", "trouve moi une circulaire sur", "trouve moi", 
                        "recherche le texte sur", "texte officiel sur", "circulaire concernant", "circulaire sur",
                        "savoir si", "refuser une", "refuser un", "concerne le", "concerne la"
                    ]
                    for mot in scories:
                        phrase_brute = phrase_brute.replace(mot, "")
                    
                    concept_cible = phrase_brute.strip() if phrase_brute.strip() else prompt

                    requete_blindee = (
                        f"EPS {concept_cible} "
                        f"\"loi\" OR \"code de l'éducation\" OR \"circulaire\" OR \"décret\" "
                        f"OR \"arrêté\" OR \"BO\" OR \"bulletin officiel\" OR \"jurisprudence\" "
                        f"OR \"journal officiel\" OR \"responsabilité\""
                    )
                    
                    # 🎯 RETRAIT DE LEGIFRANCE DES RECHERCHES WEB POUR ÉVITER LES LIENS MORTS
                    domains = [
                        "conseil-etat.fr", 
                        "courdecassation.fr", 
                        "education.gouv.fr", 
                        "eduscol.education.gouv.fr", 
                        "eps.ac-creteil.fr",
                        "eps.ac-aix-marseille.fr",
                        "unss.org"
                    ]

                elif mode == "examens":
                    requete_blindee = f"{prompt} réglementation examen Santorin Cyclades"
                    domains = ["education.gouv.fr"] + domaine_eps_france
                
                elif mode == "ipack":
                    requete_blindee = f"rubrique4 {prompt}"
                    domains = ["ipackeps.ac-creteil.fr"]
                    exclude = ["youtube.com"]
                
                elif mode == "peda":
                    requete_blindee = f"EPS {prompt} référentiel compétences officielles"
                    domains = ["eps.ac-aix-marseille.fr", "pedagogie.ac-aix-marseille.fr", "edubase.eduscol.education.fr", "eps.ac-creteil.fr", "eduscol.education.gouv.fr"]

                # Exécuteur global Tavily (Exécution unique harmonisée)
                if not tavily_deja_execute:
                    payload = {
                        "api_key": tavily_api_key, 
                        "query": requete_blindee, 
                        "search_depth": "advanced", 
                        "include_domains": domains
                    }
                    if exclude:
                        payload["exclude_domains"] = exclude
                    
                    res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                    if res.status_code == 200:
                        for item in res.json().get("results", []): 
                            extraits_doc += f"Source ({item['url']}): {item['content']}\n\n"
            except Exception as e:
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
                    mot_cle_local = prompt_lower
                    for n in retriever_textes.retrieve(mot_cle_local.strip()): extraits_doc += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"
                elif mode == "peda":
                    est_lycee = any(x in prompt_lower for x in ["lycée", "lycee", "bac", "terminale", "première", "premiere", "seconde", "cap", "bac pro"])
                    if est_lycee:
                        for n in retriever_peda.retrieve(prompt + " AFL Lycée"): extraits_doc += f"Référentiel Lycée (AFL) : {n.node.text}\n\n"
                    else:
                        for n in retriever_peda.retrieve(prompt + " Collège programmes"): extraits_doc += f"Base collège (Programmes) : {n.node.text}\n\n"
            except: 
                pass

        # ------------------------------------------------------------------
        # 3. IDENTITÉ ET CONFIGURATION DES CONSIGNES IA
        # ------------------------------------------------------------------
        règles_or = "RÈGLES D'OR : 1. Loi 1937 (Substitution État). 2. Règle 11 (Structure=Mairie/EPI=Prof). 3. Examens = Mission impérative."
        filtre_pierre = (
            "\n\nMÉTHODE DE RÉPONSE OBLIGATOIRE (Le 'Filtre Pierre') :\n"
            "1. ANALYSE DES RISQUES : Identifie l'impact sur les outils ou la responsabilité.\n"
            "2. PROCÉDURE TECHNIQUE : Utilise des étapes fléchées (→).\n"
            "3. PROTECTION FONCTIONNELLE : Indique la traçabilité et les recours."
        )

        if mode == "ipack":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Expert technique officiel de l'application iPackEPS.\n"
                "MISSION : Résolution de pannes, saisie de notes CCF, et protocole de gestion des certificats médicaux d'inaptitude.\n"
                "STRUCTURE TECHNIQUE OBLIGATOIRE :\n"
                "### 1. DIAGNOSTIC TECHNIQUE\n"
                "### 2. PROCÉDURE DE RÉSOLUTION\n"
                "### 3. ALERTES & SUIVI CCF\n\n"
                f"Contexte applicatif : {extraits_doc}\n"
                f"Question de l'enseignant : {prompt}"
            )
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif mode == "examens":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Expert officiel de la réglementation des examens EPS (DNB, Baccalauréat) et de la plateforme Santorin/Cyclades. Session 2026 (Date limite impérative : 30 mai 2026).\n"
                "MISSION : Encadrer la notation numérique, la distribution des lots de copies et la gestion des absences ou dysfonctionnements.\n"
                "STRUCTURE ADMINISTRATIVE OBLIGATOIRE :\n"
                "### 1. CADRAGE RÉGLEMENTAIRE EXAMEN\n"
                "### 2. MANIPULATION PLATAFORME (SANTORIN/CYCLADES)\n"
                "### 3. ACTIONS JURY ACADÉMIQUE\n\n"
                f"Contexte d'examen : {extraits_doc}\n"
                f"Question : {prompt}"
            )
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif mode == "textes":
            consigne_ia = (
                "ROLE : Tu es un inspecteur de l'Éducation Nationale, expert en contentieux juridique EPS. Ton ton est froid, neutre et purement factuel.\n"
                "MISSION : Tu analyses la question en t'appuyant sur les textes officiels présents dans le contexte. Tu explores méticuleusement le contexte pour en extraire le plus d'informations possibles.\n"
                "RÈGLE DE DROIT IMPÉRATIVE : La responsabilité civile d'un enseignant public devant les tribunaux civils est impossible (Loi de 1937 / Art. L. 911-4 du Code de l'éducation). Seule la responsabilité pénale personnelle s'applique en cas de faute caractérisée.\n\n"
                "CONSIGNE DE FORMATAGE IMPÉRATIVE (MARKDOWN BRUT) :\n"
                "Rédige exclusivement en Markdown standard. N'utilise AUCUNE balise HTML (Pas de <h3>, pas de <ul>, pas de <a>). Utilise des titres de section commençant uniquement par '### '.\n"
                "Pour CHAQUE texte, loi, ou circulaire évoqué, tu as l'obligation absolue de l'insérer sous forme de lien Markdown standard : [Nom précis du texte](URL).\n"
                "🎯 SÉCURITÉ DES ENTRÉES : N'utilise jamais le site racine général de Légifrance. Si l'URL spécifique n'apparaît pas clairement, redirige de force vers l'arborescence officielle du Code de l'Éducation (https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006071191/), ou vers Aix-Marseille (http://www.eps.ac-aix-marseille.fr), ou Créteil (https://eps.ac-creteil.fr).\n\n"
                "STRUCTURE ATTENDUE :\n"
                "### 1. TEXTES OFFICIELS ET CADRE JURIDIQUE\n"
                "### 2. ANALYSE ET JURISPRUDENCE ACADÉMIQUE\n"
                "### 3. PROTECTION ET RECOURS\n"
                "### 4. RÉFÉRENCES ET LIENS DE RECHERCHE\n"
                "Dresse la liste des textes cités sous forme de puces avec leurs liens Markdown obligatoires.\n\n"
                f"Contexte juridique extrait : {extraits_doc}\n"
                f"Question de l'agent : {prompt}"
            )
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif mode == "peda":
            est_lycee = any(x in prompt_lower for x in ["lycée", "lycee", "bac", "terminale", "première", "premiere", "seconde", "cap", "bac pro"])
            niveau_affiche = "Lycée (Baccalauréat / CAP)" if est_lycee else "Cycle 4 (Collège)"
            label_attendu = "Attendus de Fin de Lycée (AFL 1, 2, 3)" if est_lycee else "Attendus de Fin de Cycle 4 (AFC)"
            label_competence = "Axe des compétences visées"

            ca_nom, ca_attendus, ca_competences = "CA1 (Performance optimale)", "Performance optimale à une échéance donnée.", "Gérer ses ressources."
            if any(x in prompt_lower for x in ["volley", "basket", "hand", "foot", "rugby", "badminton", "tennis", "ping", "boxe", "lutte", "combat"]):
                ca_nom, ca_attendus, ca_competences = "CA4 (Affrontement)", "En situation d'opposition réelle, faire basculer le rapport de force.", "Construire un choix tactique."
            elif any(x in prompt_lower for x in ["gym", "acro", "danse", "step", "cirque"]):
                ca_nom, ca_attendus, ca_competences = "CA3 (Prestation)", "Composer et interpréter une séquence corporelle devant un public.", "Maîtriser les risques."
            elif any(x in prompt_lower for x in ["muscu", "step", "fitness", "entretien", "ca5"]):
                ca_nom, ca_attendus, ca_competences = "CA5 (Santé)", "Produire des formes de travail adaptées à un mobile personnel.", "Réguler sa charge d'effort."
            elif any(x in prompt_lower for x in ["escalade", "orientation", "vtt", "kayak"]):
                ca_nom, ca_attendus, ca_competences = "CA2 (APPN)", "Conduire un déplacement fluide dans un milieu à incertitude.", "Gérer la sécurité active."

            mots_apsa = ["volley", "basket", "hand", "foot", "rugby", "badminton", "tennis", "ping", "boxe", "lutte", "gym", "acro", "danse", "step", "muscu", "fitness", "escalade", "orientation", "vtt", "kayak", "relais", "natation"]
            apsa_trouvee = "eps"
            for m in mots_apsa:
                if m in prompt_lower:
                    apsa_trouvee = m
                    break

            consigne_ia = (
                f"ROLE : Assistant technique d'extraction institutionnelle EPS. Interdiction absolue de concevoir des fiches locales.\n"
                f"STRUCTURE FINALE EXCLUSIVEMENT EN BALISES HTML (Pas de Markdown) :\n"
                f"<h3>📊 CADRAGE INSTITUTIONNEL ET RÉGLEMENTAIRE - {apsa_trouvee.upper()}</h3>"
                f"<strong>Niveau ciblé : {niveau_affiche} | Champ d'Apprentissage : {ca_nom}</strong><br><br>"
                f"<h3>🌐 TEXTES OFFICIELS & REPERES DU BULLETIN OFFICIEL (BO)</h3>"
                f"<ul><li><strong>{label_attendu} :</strong> {ca_attendus}</li><li><strong>{label_competence} :</strong> {ca_competences}</li></ul>"
                f"<h3>🔍 RESPONSABILITÉ ET CADRE ACADÉMIQUE D'ÉVALUATION</h3>"
                f"<ul><li>La conception des fiches de cycle et les critères observables appartiennent souverainement à l'équipe pédagogique locale sous la supervision des IA-IPR.</li></ul>"
                f"<h3><h3>💾 RESSOURCES EMBARQUÉES ET OUTILS NUMÉRIQUES HOMOLOGUÉS</h3>"
                f"<ul>"
                f"<li><a href='https://edubase.eduscol.education.fr/recherche?q={apsa_trouvee}' target='_blank'>📥 Ressources {apsa_trouvee.upper()} - Base Nationale ÉDUBASE EPS</a></li>"
                f"<li><a href='http://www.eps.ac-aix-marseille.fr/webphp2/mediawiki/index.php?title=Accueil' target='_blank'>🎥 Ouvrir le Conservatoire EPS Aix-Marseille (Cherchez : '{apsa_trouvee.upper()}')</a></li>"
                f"</ul>"
            )
            badge, color_card = "🎓 CADRAGE EPS", "peda-card"
            
        # ------------------------------------------------------------------
        # 4. EXÉCUTION ET RENDU DE LA CARTE DE SORTIE
        # ------------------------------------------------------------------
        response = Settings.llm.complete(consigne_ia)
        texte_brut = response.text
        
        # Interception et conversion automatique et sécurisée de TOUS les liens Markdown (Couleur forcée Orange)
        texte_brut = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)', 
            r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: 700;">\1</a>', 
            texte_brut
        )
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)

        if mode == "peda" or mode == "textes":
            texte_final = texte_brut.strip()
            texte_final = re.sub(r'^###\s+(.*)$', r'<h3>\1</h3>', texte_final, flags=re.MULTILINE)
            texte_final = texte_final.replace("\r\n", "<br>").replace("\n", "<br>")
            texte_final = re.sub(r'(<br>\s*){2,}', '<br>', texte_final)
            
            # Sécurité d'injection : Pointage direct vers le Code de l'Éducation en Section 5 permanente
            if mode == "textes":
                liens_fixes_publics = """
                <br><h3>5. RECOURS & LIENS INSTITUTIONNELS PERMANENTS</h3>
                <ul>
                <li><a href='https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006071191/' target='_blank' style='color: #FFB020 !important; text-decoration: underline; font-weight: 700;'>Accès direct : Code de l'Éducation Intégral (Légifrance)</a></li>
                <li><a href='https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006525615/' target='_blank' style='color: #FFB020 !important; text-decoration: underline; font-weight: 700;'>Article L. 911-4 : Substitution de la responsabilité de l'État (Loi de 1937)</a></li>
                <li><a href='http://www.eps.ac-aix-marseille.fr/' target='_blank' style='color: #FFB020 !important; text-decoration: underline; font-weight: 700;'>Portail Réglementaire EPS – Académie d'Aix-Marseille</a></li>
                </ul>
                """
                texte_final = texte_final.strip() + liens_fixes_publics
                
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
        else:
            texte_final = texte_brut.replace(chr(10), "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
            
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        for link in youtube_links:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"st.video('{link[0]}')"})
        st.rerun()
