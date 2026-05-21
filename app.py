import streamlit as st
import os

st.title("🤖 Assistant iPackEPS")

def chercher_reponse(question):
    try:
        with open("Géré par pierre.txt", "r", encoding="utf-8") as f:
            contenu = f.read()
            # On cherche si la question ou des mots-clés sont dans le texte
            if question.lower() in contenu.lower():
                return "Voici les éléments trouvés dans mes consignes : \n\n" + contenu[contenu.find(question)-50 : contenu.find(question)+300]
            else:
                return "Je n'ai pas trouvé de réponse précise dans mes documents pour cette question."
    except Exception as e:
        return f"Erreur lors de la lecture du fichier : {e}"

if question_prof := st.chat_input("Pose ta question :"):
    st.write(f"Tu as demandé : {question_prof}")
    reponse = chercher_reponse(question_prof)
    st.write(reponse)