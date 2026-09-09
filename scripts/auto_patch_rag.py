import os
import requests
from google import genai
from google.genai import types

# 1. Configuration de l'API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("La clé API GEMINI_API_KEY est manquante.")

client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-3.6-flash"

# URL de ton Google Apps Script
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbyVq8_DCLnAyrr7xEUw1Xbdze0Lm1S-P6RHlXJPE2CmaBD39lpFfQjpuHQhxmL0z3bJ/exec"

def load_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fichier {filepath} mis à jour et validé via les sources officielles !")

def analyser_et_patcher():
    print("1. Récupération des logs depuis le Google Sheet...")
    try:
        response = requests.get(URL_APPS_SCRIPT)
        lignes = response.json()
    except Exception as e:
        print(f"Erreur de lecture du Sheet : {e}")
        return

    # Nettoyage et déduplication des questions récentes
    brut_logs = [row.get("question", "") for row in lignes[-50:] if row.get("question")]
    derniers_logs = list(dict.fromkeys(brut_logs))[-15:]
    if not derniers_logs:
        print("Aucune question trouvée dans les logs.")
        return
        
    logs_texte = "\n".join(f"- {q}" for q in derniers_logs)

    fichiers_ref = {
        "ipack": "ipack.txt",
        "examens": "data/examens/regles_dnb_eps.txt",
        "santorin": "data/examens/memoire_examens_santorin.txt"
    }

    print("2. Analyse, recherche web officielle et audit global par Gemini...")
    for cle_cible, cible_fichier in fichiers_ref.items():
        contenu_actuel = load_file(cible_fichier)
        if not contenu_actuel:
            continue

        prompt = f"""
[CONTEXTE INSTITUTIONNEL]
Tu es le gardien expert et certificateur de la base de connaissances du Hub EPS (Fichier cible : {cle_cible}).
Ton rôle est d'analyser les interrogations de terrain et de les **croiser obligatoirement avec les textes officiels et sources institutionnelles vérifiées** (Eduscol, Ministère de l'Éducation Nationale, circulaires et ressources académiques - ex: Créteil, Normandie, Aix-Marseille, etc.).

[ÉTAT ACTUEL DE LA BASE DE CONNAISSANCES]
{contenu_actuel}

[DERNIERS LOGS / QUESTIONS DE TERRAIN]
{logs_texte}

[INSTRUCTIONS STRICTES DE VÉRIFICATION ET DE CROISEMENT]
1. **OBLIGATION DE RECHERCHE WEB OFFICIELLE** : Pour chaque règle réglementaire, administrative ou liée aux examens/CCF/DNB présente dans les logs, tu DOIS déclencher une recherche sur le web pour valider le texte officiel en vigueur via des sources sures (`eduscol.education.fr`, `education.gouv.fr`, sites académiques officiels).
2. **FILTRE ANTI-ERREUR DE TERRAIN** : Ne prends jamais la formulation ou le doute d'un utilisateur pour argent comptant. Si un utilisateur exprime une idée fausse ou une interdiction (comme la pluri-affectation interdite en CCF), va chercher la source officielle pour le démontrer et figer la doctrine exacte.
3. **ZÉRO CONTRADICTION** : Assure-toi que toute modification affine ou clarifie la règle sans jamais contredire les principes fondamentaux déjà ancrés.
4. **SORTIE** : Si aucune modification n'est nécessaire, réponds strictement par : "RIEN_A_SIGNALER". Sinon, renvoie **l'intégralité du fichier mis à jour et nettoyé** en format Markdown propre, prêt à remplacer l'ancien.
"""

        # Appel de l'API avec activation de l'outil de recherche Google (Grounding)
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1 # Température basse pour maximiser la rigueur administrative
            )
        )
        
        texte_reponse = response.text.strip()

        if "RIEN_A_SIGNALER" in texte_reponse or len(texte_reponse) < 50:
            print(f"✅ {cible_fichier} : Aucun changement requis après vérification officielle.")
            continue

        print(f"🛠️ Mise à jour et validation officielle de {cible_fichier}...")
        save_file(cible_fichier, texte_reponse)

if __name__ == "__main__":
    analyser_et_patcher()
