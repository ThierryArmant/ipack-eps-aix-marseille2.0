# Comparaison des fiches candidates — expérimentation

## Fonctionnement constaté
Dans le parcours inspecté de `app.py`, la recherche et les filtres de sélection précèdent l'appel de rédaction de `review_exam_answer`. Cet appel demande déjà au modèle de vérifier l'applicabilité, mais des documents ont pu être écartés auparavant par priorité, exclusivité ou limitation du nombre de résultats. Une consigne de rédaction ne récupère pas un document perdu avant l'appel.

## Expérience disponible, non activée
L'argument explicite `selection_policy='compare_candidates'` permet un essai contrôlé. Sa valeur par défaut reste `legacy` et aucun appel de `app.py` ne le modifie. Il ne change donc pas les réponses du hub.

Le pilote conserve les candidats déjà retrouvés après les exclusions de portée et de situation, sans leur appliquer la réduction par priorité. La comparaison s'effectue dans le même appel de rédaction, sur les passages complets, avec leurs identifiants et leur portée académique. Les contrôles de preuve ne sont pas modifiés. Les titres et exemples issus des fiches sont des descriptions de recherche, jamais des preuves ni des réponses prédéfinies. Les champs de diagnostic identifient la politique demandée et celle effectivement appliquée.

L'expérience est limitée à huit documents et 18 000 caractères documentaires. Si le paquet est trop grand, le parcours courant est conservé, avec motif de repli dans la trace. Aucun découpage arbitraire d'une condition justificative n'est fait. Les résumés produits par le programme ne sont pas traités comme candidats documentaires dans le pilote. Les exclusions spécifiques de portée, de circuits et de vue d'ensemble handicap restent en place.

Ce pilote ne transforme pas la recherche initiale en interprétation sémantique. Il ne supprime ni l'exclusivité ni la limite de récupération de `app.py`, et n'invente pas de fiche absente. Il ne constitue pas encore le processus final de sélection.

## Constat du diagnostic local
Sur le petit lot privé examiné : recherche par catalogue et recherche lexicale réelles, recherche vectorielle simulée vide ; les académies fournies sont conservées. Modèle factice sans affirmation : aucun appel de génération payé, aucune mesure de qualité des réponses IA. La comparaison conserve des alternatives utiles mais aussi des documents sans rapport. Le volume documentaire passe de 24 à 40 documents cumulés, et de 46 433 à 74 147 caractères. Ces caractères ne sont ni un décompte de jetons ni une facture. Un gain de pertinence n'est pas démontré.

La priorité peut retirer une procédure d'accès tandis qu'une fiche du même statut d'établissement demeure. À l'inverse, élargir sans départager réintroduit du bruit. Certaines demandes restent sans procédure documentée ; d'autres ne disposent pas du détail historique ou académique nécessaire. Ces constats justifient de garder le pilote désactivé.

## Suite de travail
1. Conserver le diagnostic initial, sans fabriquer un déclencheur par question.
2. Décrire les objets, actions couvertes, conditions et limites des fiches à partir de leur contenu vérifié ; ne pas les déduire du seul titre.
3. Comparer la pertinence et la couverture des ensembles de preuves, puis le volume transmis et les exclusions utiles maintenues.
4. Si ces contrôles sont concluants, mesurer la rédaction réelle sur une version identifiée ; les tests factices ne permettent pas de prévoir cette rédaction.
5. Préserver la banque de réserve pour une mesure indépendante. Vérifier auparavant que les formulations ne figurent pas déjà dans l'historique.
