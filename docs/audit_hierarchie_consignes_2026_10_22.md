# Hiérarchie des consignes — audit du 22 octobre 2026

Correction préparée depuis a3c6b69 puis autorisée avant le prochain rejeu. Compilation et 883 tests locaux réussis. Aucune mesure distante du comportement à ce stade.

## Circuit réellement exécuté

1. L’interface fixe public et onglet ; le texte peut préciser un diplôme. La fonction de contexte conserve l’académie choisie pour Examens, mais la neutralise pour iPack et Textes sauf déclaration textuelle reconnue.
2. Les contrôles préalables peuvent ouvrir un guide, demander une précision ou rendre une réponse documentaire avant la génération. Une instruction de rédaction ne peut pas annuler cet arrêt.
3. Recherche documentaire, filtres de public et de situation, puis sélection courte lorsqu’elle est activée. Les pièces supprimées ici ne sont pas lues par le rédacteur.
4. Rédaction : préambule de documentary_review.py, schéma, config/consignes_fiabilite.txt, ajouts de contexte, puis données JSON et passages. Le grand bloc consigne_ia d’app.py n’est pas envoyé dans les trois modes documentaires.
5. Contrôles des références, de l’appui lexical, des opérations, conditions et cohérence ; réparation éventuelle, puis contrôle à nouveau. Aucun ordre de prompt ne remplace ces contrôles.

## Constats

- Le préambule prioritaire imposait une conclusion sur l’absence d’un élément alors que les consignes communes distinguent absence de preuve et interdiction. Contradiction confirmée ; elle peut favoriser une conclusion négative indue, mais l’attribution causale exige une mesure.
- La sortie doit être un JSON de textes sans HTML. Une consigne commune demandait simultanément du HTML simple : contradiction confirmée.
- Les titres, priorités et exemples ne prouvent pas l’applicabilité. Les consignes le répètent dans plusieurs couches ; il faut conserver ce principe sans addition de règles métier.
- Les repères génériques par diplôme sont préparés en amont mais retirés lorsque la sélection courte s’applique. Ne pas conclure qu’un texte visible dans app.py est présent dans tous les appels.
- L’adaptateur principal transmet le prompt complet dans un message utilisateur. Les mentions « prioritaire » dans le texte sont des instructions de lecture, pas des rôles techniques distincts de l’API.
- La réserve documentaire incorrectement transformée en certitude peut encore passer le contrôle : correction de ce contrôle à traiter séparément. Un nettoyage de consigne seul ne démontre pas la disparition de l’erreur.

## Ordre cible

Comprendre la demande et son contexte → vérifier les preuves applicables et leur portée → conserver les conditions et les alternatives → donner les démarches utiles ou la limite précise → mettre en forme.

Le contexte limite l’applicabilité ; il ne constitue pas une preuve d’un droit ou d’un bouton. La priorité de recherche guide la récupération ; elle ne confère pas une autorité documentaire. La concision et la présentation ne doivent pas imposer une conclusion ni supprimer une condition indispensable.

## Corrections préparées

- Retrait de l’injonction de décision négative pour un élément simplement non documenté ; distinction explicite preuve contraire / absence d’information.
- Ordre de lecture explicite et présentation subordonnée au sens.
- Format commun rendu dépendant du contrat du circuit ; textes simples pour le JSON.
- Aucune suppression de contrôle, modification de fiche ou nouvelle passe IA.

Le retrait des blocs inactifs, la simplification globale, la conservation du contexte académique et la correction du contrôle de certitude restent à traiter séparément. La présente préparation n’est pas une preuve de gain de fiabilité.
