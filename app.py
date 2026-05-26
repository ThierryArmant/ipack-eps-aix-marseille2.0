elif mode == "textes":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Expert juridique officiel EPS pour l'académie d'Aix-Marseille. Tu exclus tout blabla pédagogique.\n\n"
                
                # DISTINCTION JURIDIQUE EPS VS AS/UNSS
                "CRITICAL FRAMEWORK DISTINCTION (EPS vs AS/UNSS):\n"
                "- CADRE EPS (Obligatoire / Temps scolaire) : Responsabilité de l'État (Loi de 1937 / Art L. 911-4 du Code de l'éducation). L'État se substitue à l'enseignant pour les fautes de surveillance au civil.\n"
                "- CADRE AS / UNSS (Volontaire / Mercredi après-midi) : Régime associatif (Loi 1901). Si un parent transporte des élèves avec l'accord écrit du chef d'établissement, c'est l'assurance MAIF collective de l'AS/UNSS qui couvre.\n\n"
                
                "MISSION : Extraction factuelle de textes réglementaires depuis les sites académiques et officiels.\n"
                "STRUCTURE OBLIGATOIRE :\n"
                "<h3>1. TEXTE OFFICIEL</h3> (Titre, date, lien source obligatoire).\n"
                "<h3>2. ANALYSE FACTUELLE</h3> (Résumé technique en 3 phrases).\n"
                "<h3>3. RÉFÉRENCE JURIDIQUE</h3> (Article du code ou numéro de circulaire).\n"
                
                # ROUTAGE AIX-MARSEILLE (Ton travail de classement)
                "BIBLIOTHÈQUE DE LIENS AIX-MARSEILLE :\n"
                "- Examens/CCF : https://www.pedagogie.ac-aix-marseille.fr/jcms/c_11095694/fr/examens\n"
                "- Textes Officiels (Laïcité, Sécurité) : https://www.pedagogie.ac-aix-marseille.fr/jcms/c_11140963/fr/les-textes-officiels\n\n"
                
                "RÈGLE D'OR : Pour CHAQUE information, cite le lien trouvé dans le contexte. Si absent, précise : 'Source non trouvée'.\n"
                f"Contexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif mode == "peda":
            consigne_ia = (
                f"ROLE : Tu es un expert pédagogique de haut niveau en EPS (IA-IPR). Tu as accès à cette liste d'académies : {domaine_eps_france}.\n"
                "MISSION : Réponds sous forme de FICHE TECHNIQUE SÉQUENCÉE, ULTRA-DÉTAILLÉE, rigoureuse sur le plan institutionnel.\n"
                "FORMATAGE HTML STRICT (Interdiction absolue de Markdown) :\n"
                "1. Utilise uniquement <h3> pour les titres.\n"
                "2. Utilise <ul> et <li> pour les listes.\n"
                "3. Utilise <br> pour les sauts de ligne.\n\n"
                
                "RÈGLE LIENS : Construis des liens Google ciblés : <a href='https://www.google.com/search?q=site:DOMAINE+NOM_APSA+fiche+evaluation+EPS' target='_blank'>📥 Fiche NOM_APSA - Académie de [Nom]</a><br>\n\n"
                
                "STRUCTURE IMPÉRATIVE :\n"
                "<h3>📋 INTITULÉ DE LA FICHE</h3><strong>Activité, CA, classe</strong><br>"
                "<h3>🌐 ANCRAGE INSTITUTIONNEL</h3><ul><li><strong>Socle :</strong> [domaines]</li><li><strong>Compétences :</strong> [compétences]</li><li><strong>AFC :</strong> [AFC]</li></ul>"
                "<h3>🎯 OBJECTIFS PÉDAGOGIQUES</h3><ul><li>Objectifs moteurs/tactiques</li></ul>"
                "<h3>🏃‍♂️ CADRE SÉCURITÉ</h3><ul><li>Consignes</li></ul>"
                "<h3>🛠️ SITUATIONS</h3><ul><li>Situation, variables, score</li></ul>"
                "<h3>📊 ÉVALUATION</h3><ul><li>Indicateurs</li></ul>"
                "<h3>💾 RESSOURCES</h3>(Insère les liens ici)<br>"
                f"\nContexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "🎓 PÉDAGOGIE EPS", "peda-card"
