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

    print("2. Analyse des questions par Gemini...")
    prompt = f"""
    Voici les dernières questions posées par des enseignants d'EPS dans le Hub IA :
    {logs_texte}
    
    Analyse ces questions. Identifie s'il y a des zones d'ombre, des incompréhensions récurrentes ou des règles réglementaires qui manquent dans notre base de connaissances.
    Si une correction ou un complément précis est nécessaire, rédige un court paragraphe au format Markdown (style bloc RAG) prêt à être ajouté dans un fichier de règles institutionnelles (`regles_dnb_eps.txt`). 
    Si tout est déjà parfaitement couvert et qu'aucun ajout n'est nécessaire, réponds strictement par : "RIEN_A_SIGNALER".
    """
    
    response = model.generate_content(prompt)
    texte_corrige = response.text.strip()
    
    if "RIEN_A_SIGNALER" in texte_corrige or len(texte_corrige) < 20:
        print("Aucun nouveau patch nécessaire. Tout est carré !")
        return

    print("3. Écriture de la correction dans le fichier RAG...")
    rag_path = "data/examens/regles_dnb_eps.txt"
    
    with open(rag_path, "r", encoding="utf-8") as f:
        contenu_actuel = f.read()

    # Ajout de la nouvelle règle générée par l'IA à la fin du fichier
    nouveau_contenu = contenu_actuel + f"\n\n======================================================================\nAJOUT AUTOMATIQUE (ANALYSE DES LOGS)\n======================================================================\n{texte_corrige}\n"

    with open(rag_path, "w", encoding="utf-8") as f:
        f.write(nouveau_contenu)
    
    print("Fichier RAG mis à jour avec succès !")

if __name__ == "__main__":
    analyser_et_patcher()
