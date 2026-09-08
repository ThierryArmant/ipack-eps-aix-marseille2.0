import os
import requests
import google.generativeai as genai

# Configuration de l'API Gemini
genai.api_key = os.environ["GEMINI_API_KEY"]
model = genai.GenerativeModel("gemini-3.6-flash")

# Ton URL Google Apps Script
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbyVq8_DCLnAyrr7xEUw1Xbdze0Lm1S-P6RHlXJPE2CmaBD39lpFfQjpuHQhxmL0z3bJ/exec"

def analyser_et_patcher():
    print("1. Récupération des logs depuis Google Sheets...")
    try:
        response = requests.get(URL_APPS_SCRIPT)
        lignes = response.json()
    except Exception as e:
        print(f"Erreur de lecture du Sheet : {e}")
        return

    # Extraire les 30 dernières questions posées
    dernier_logs = [row.get("question", "") for row in lignes[-30:] if row.get("question")]
    if not dernier_logs:
        print("Aucune question trouvée dans les logs.")
        return
        
    logs_texte = "\n".join(f"- {q}" for q in dernier_logs)

    print("2. Analyse intelligente et routage par Gemini (Multi-RAG à 3 branches)...")
    prompt = f"""
    Voici les dernières questions posées par des enseignants d'EPS dans le Hub IA :
    {logs_texte}
    
    Analyse ces questions. Tu dois déterminer si elles nécessitent de mettre à jour l'une de nos bases de connaissances (RAG). 
    Nous avons trois fichiers cibles possibles :
    1. `ipack` -> Concerne le fonctionnement de l'application iPackEPS, ses outils, ses tableaux, ses scripts ou son utilisation pratique.
    2. `examens` -> Concerne la réglementation, les textes officiels, les épreuves ou les règles du DNB EPS.
    3. `santorin` -> Concerne la gestion des examens, des copies, des notes et l'utilisation des plateformes Santorin ou Cyclades.

    Si une correction ou un complément est nécessaire, réponds STRICTEMENT selon ce format précis :
    CIBLE: [ipack, examens ou santorin]
    CONTENU:
    [Le paragraphe au format Markdown prêt à être ajouté]

    Si tout est déjà couvert ou que les questions ne nécessitent pas de modification, réponds strictement par : "RIEN_A_SIGNALER".
    """
    
    response = model.generate_content(prompt)
    texte_reponse = response.text.strip()
    
    if "RIEN_A_SIGNALER" in texte_reponse or len(texte_reponse) < 20:
        print("Aucun nouveau patch nécessaire. Tout est carré !")
        return

    # Identification de la cible parmi les 3 modules
    cible = None
    if "CIBLE: ipack" in texte_reponse:
        cible = "ipack.txt"
    elif "CIBLE: examens" in texte_reponse:
        cible = "data/examens/regles_dnb_eps.txt"
    elif "CIBLE: santorin" in texte_reponse:
        cible = "data/examens/memoire_examens_santorin.txt"
    else:
        print("Format de routage non reconnu par l'IA.")
        return

    # Extraction du contenu du patch
    if "CONTENU:" in texte_reponse:
        contenu_patch = texte_reponse.split("CONTENU:")[1].strip()
    else:
        print("Balise CONTENU introuvable.")
        return

    if not contenu_patch:
        print("Le patch généré est vide.")
        return

    print(f"3. Écriture de la correction dans le fichier cible : {cible}...")
    
    with open(cible, "r", encoding="utf-8") as f:
        contenu_actuel = f.read()

    nouveau_contenu = contenu_actuel + f"\n\n======================================================================\nAJOUT AUTOMATIQUE (MULTIRAG - {cible})\n======================================================================\n{contenu_patch}\n"

    with open(cible, "w", encoding="utf-8") as f:
        f.write(nouveau_contenu)
    
    print(f"Fichier {cible} mis à jour avec succès !")

if __name__ == "__main__":
    analyser_et_patcher()
