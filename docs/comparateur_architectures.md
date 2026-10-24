# Comparateur documentaire A/B

## Variante E — proposition Gemini : isoler les procédures

Choisir « E — Proposition Gemini : isoler les procédures » face à A. Cette variante reprend la proposition fournie par l'utilisateur : identifier l'action, l'objet et la phase, rattacher les conditions à leur opération, distinguer les procédures voisines et vérifier acteur et chemin dans les passages cités. Elle conserve les vrais préalables documentés. Elle ne déduit pas « aucune condition » d'une absence de preuve et n'invente pas un rôle générique de responsable habilité.

A et E partagent exactement les documents récupérés une seule fois, le modèle, la température, la question originale, le contexte et les contrôles. E ajoute seulement la consigne expérimentale aux instructions de rédaction existantes. Aucun appel à Gemini ou Albert, ni analyse IA supplémentaire. Chaque colonne peut avoir sa réparation habituelle, comptée séparément. Si la recherche A échoue, E n'en lance pas une autre. Les parcours communs sans IA restent prioritaires.

La consigne exacte est consultable dans le panneau et exportée avec son identifiant et son empreinte dans la trace E. C'est une adaptation prudente, pas la copie littérale de toute la proposition ; ce test n'effectue pas sa réécriture suggérée des fiches et n'ajoute pas de raisonnement détaillé à afficher. Il ne reproduit pas tout le pipeline de sélection du Hub public et ne prouve pas qu'une consigne empêche les erreurs. Aucun effet sur la réponse publique, aucun lancement automatique. Reprendre une même question dans A/E, examiner les deux réponses et télécharger le JSON avant de quitter la session.

Accès : administration du hub, panneau « Comparateur des architectures A / B ».
Saisir une question, un niveau, un domaine et une académie, puis cliquer sur « Tester le parcours — IA payante si nécessaire ».

Le niveau/domaine effectifs et l’académie sont déterminés comme dans le hub. Le choix d’académie est appliqué en mode Examens ; ailleurs, seules les académies reconnues dans la question peuvent modifier le contexte. Les valeurs saisies restent conservées dans le résultat.

Avant les deux colonnes, la même fonction que le parcours public vérifie guidage, clarification et réponse documentaire directe. Si elle traite la demande, le comparateur affiche un seul parcours commun, sans recherche ni génération, et exporte ce résultat à zéro appel. Les parcours du guide utilisent le même composant et les mêmes preuves que le hub, avec des clés de session distinctes.

| Élément | A | B |
| --- | --- | --- |
| Question de rédaction | Originale | Originale |
| Recherche | Question originale | Requête produite par interprétation IA |
| Contexte imposé | Niveau, domaine, académie saisis | Identique |
| Filtres de diplôme et de périmètre | Question originale | Question originale |
| Modèle, température et vérification | Paramètres du hub | Identiques |
| Appels | Rédaction, réparation éventuelle | Interprétation puis rédaction, réparation éventuelle |

La requête B peut influencer le catalogue, la recherche lexicale et vectorielle. Elle ne constitue pas une preuve et ne remplace pas la question dans la rédaction. Une interprétation invalide interrompt B, avec erreur visible ; aucun repli silencieux vers A. Les deux traitements sont indépendants, exécutés successivement et affichés côte à côte, sans discussion ni arbitrage automatique.

## Limites de comparaison

La comparaison A/B n’est exécutée qu’après l’orientation commune guide/précision/réponse documentaire directe. Elle ne reproduit toutefois pas toutes les anciennes branches spécifiques du public ni les enrichissements et faits calculés antérieurs à la recherche. Ne pas présenter A comme une copie intégrale de toute réponse publique. Une comparaison encore divergente du parcours public doit être exclue d’un classement global des architectures jusqu’à explication.

Le moteur de recherche commun est extrait mécaniquement de l’application ; le parcours public conserve les mêmes entrées et l’absence de requête interprétée. Les règles du guidage ne sont pas réécrites pour le comparateur : elles sont partagées dans question_preflight.py.

Les priorités et exclusivités du catalogue demeurent actives. Ce test ne démontre pas qu'une interprétation résout tous les défauts de sélection. Le pilote `compare_candidates` reste désactivé pour ne pas changer deux mécanismes simultanément.

Le texte produit par l'interprète peut malgré les consignes contenir une supposition : vérifier son panneau avant de conclure à une meilleure recherche. Deux réponses identiques ne prouvent pas leur exactitude. Évaluer pertinence, conditions essentielles, preuves, réserves, appels, jetons et durée.

Les compteurs couvrent la génération, y compris l'interprétation B et les réparations ; les recherches vectorielles ne sont pas comprises. Une absence de métriques fournisseur est signalée. Les résultats restent en session, ne sont pas ajoutés au journal public des questions ; télécharger le JSON privé avant de quitter. Ouvrir le panneau, changer un champ ou télécharger ne lance aucune génération. Aucun lot automatique.
