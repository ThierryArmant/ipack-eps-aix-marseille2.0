# Comparateur documentaire A/B

## Variante F — préparer le contexte par rôle

F expérimente une préparation généralisable, sans liste de situations métier codée en dur. À partir de la même recherche que A, un appel au même modèle examine les passages complets de chaque document et lui attribue un rôle : principal, préalable documenté, complément d'une sous-demande, limite/exception/contradiction pertinente, incertain, ou opération voisine sans lien nécessaire. Chaque décision indique un identifiant de passage ; le programme en recopie le texte exact dans la trace. Une ancienne sortie contenant une citation exacte reste acceptée. Ces vérifications prouvent l'existence du passage, pas la justesse sémantique du classement.

Les documents principaux, préalables, compléments, limites et incertains sont conservés en entier. Seuls les documents classés voisins sont retirés. Les principaux passent en premier ; ce classement documentaire ne prescrit pas un ordre d'opérations. Pas de plafond de quatre documents pour une demande générale ou composée. Les données calculées du programme ne sont pas éliminées par le planificateur. Les restrictions, branches et portées des documents retenus restent dans leurs sources complètes ; aucune fiche n'est modifiée.

Un plan partiel conserve ses décisions valides et maintient tous les documents non classés, entiers et considérés incertains. Ils sont listés explicitement dans la trace ; une omission n'est jamais une exclusion. Des identifiants inconnus, des doublons, une citation inexistante, une réponse invalide, une panne ou l'absence de document principal conservent le contexte initial sans nouvelle tentative. Au-delà du budget expérimental de 40 000 caractères pour l'appel de préparation, le contexte initial est également conservé : aucun document ni passage n'est tronqué pour entrer dans ce budget. Une seule source ne nécessite pas d'appel de préparation.

F ajoute au plus un appel IA de préparation, compté dans sélection. Sans exclusion exploitable, F affiche que le contexte n'est pas réduit et ne lance pas sa rédaction ni de réparation : cela ne signifie pas que la question métier serait sans réponse. A est néanmoins calculée normalement, et son coût demeure. Si le plan écarte explicitement des voisins, F utilise ensuite les consignes de rédaction de A et les contrôles habituels. Il n'ajoute pas la consigne Gemini E. Aucune activation automatique sur le Hub public ni appel à Albert ou Gemini. Le résultat exporte contexte initial, rôles, passages justificatifs, exclusions, nombres de caractères avant/après et contexte transmis à la rédaction. Le panneau reste gratuit à ouvrir ; seul le bouton de test lance les appels.

Il s'agit d'une expérience : un modèle peut encore mal classer un document malgré une citation existante. Tester sur plusieurs familles, questions composées et cas déjà utiles avant toute généralisation publique. Une baisse du nombre de caractères ne démontre pas une amélioration. Les métadonnées et les consignes de rédaction ne sont pas encore compactées dans cette variante, afin d'isoler l'effet de préparation documentaire.

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
