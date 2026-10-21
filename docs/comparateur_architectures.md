# Comparateur documentaire A/B

Accès : administration du hub, panneau « Comparateur des architectures A / B ».
Saisir une question, un niveau, un domaine et une académie, puis lancer explicitement le bouton payant.

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

A reproduit le **parcours documentaire**, pas tous les raccourcis publics : guidage, clarification préalable, enrichissements antérieurs à la recherche et faits calculés ne sont pas exécutés. Ne pas présenter A comme une copie exacte de toute réponse publique. Le moteur de recherche commun est extrait mécaniquement de l'application ; le parcours public conserve les mêmes entrées et l'absence de requête interprétée.

Les priorités et exclusivités du catalogue demeurent actives. Ce test ne démontre pas qu'une interprétation résout tous les défauts de sélection. Le pilote `compare_candidates` reste désactivé pour ne pas changer deux mécanismes simultanément.

Le texte produit par l'interprète peut malgré les consignes contenir une supposition : vérifier son panneau avant de conclure à une meilleure recherche. Deux réponses identiques ne prouvent pas leur exactitude. Évaluer pertinence, conditions essentielles, preuves, réserves, appels, jetons et durée.

Les compteurs couvrent la génération, y compris l'interprétation B et les réparations ; les recherches vectorielles ne sont pas comprises. Une absence de métriques fournisseur est signalée. Les résultats restent en session, ne sont pas ajoutés au journal public des questions ; télécharger le JSON privé avant de quitter. Ouvrir le panneau, changer un champ ou télécharger ne lance aucune génération. Aucun lot automatique.
