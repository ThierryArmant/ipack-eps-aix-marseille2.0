# Huit essais publics réels — 23 octobre 2026

Version testée : c9a3f73efc3d2818d47a181bc983011a3d8c6854. Questions 3 à 10 du lot, chacune soumise une seule fois dans le Hub public, contexte Assistance Technique iPackEPS, avec « Académie : Aix-Marseille. » ajouté à chaque question. Collège sauf 6 et 10 en lycée voie générale. Aucun mode expérimental administrateur actif dans cette nouvelle session. Aucun compte élève ni donnée personnelle utilisé.

Chaque réponse affiche gpt-4o-mini, deux appels (orientation puis rédaction), aucune mention d’Albert. Total affiché : 16 appels, 92 933 jetons d’entrée et 2 619 de sortie, soit 95 552 jetons. Ce total provient des relevés publics ; aucune trace administrateur disponible dans cette session. Ne pas en déduire quels passages exacts étaient transmis ni si navigation_restore a été appliqué.

## Résultats

| N° | Sujet | Entrée / sortie | Appréciation fonctionnelle |
|---|---|---|---|
| 3 | Classes absentes, ordre des opérations | 10 397 / 283 | Utilisable : actualiser, configurer, organiser, importer dans cet ordre ; chemins présents. Configuration abrégée, pas détaillée champ par champ. |
| 4 | Nouveau professeur, actualiser l’équipe | 10 320 / 318 | Utilisable : chemin complet jusqu’à Actualiser, correction administrative et absence d’ajout libre. Réserve : « ne sera efficace que si […] vérifié et mis à jour » durcit le préalable ; normalement actualiser d’abord, puis vérifier si le collègue manque encore. |
| 5 | Imprimer les ASNS depuis Natation | 10 529 / 296 | Utilisable : Validation ASNS, sélection, date/enseignant facultatifs, impression. Réserve sur les années précédentes superflue à cette question. |
| 6 | APSA certificative et protocole du groupe | 13 309 / 321 | Utilisable : APSA GT, Modif., déclaration certificative, Groupes/Gérer les S.A., périodes et état du protocole. « OUI/NON » pourrait guider plus directement vers OUI pour la demande posée. |
| 7 | Reprendre les groupes Pronote | 11 149 / 408 | Utilisable : export fichier, import dans Élèves ; classes/élèves préexistants, distinction avec base élèves/synchronisation, réserve CSV/Excel conservées. Export Pronote peu détaillé. |
| 8 | Configurer classes et importer élèves | 12 530 / 266 | Utilisable : même ordre correct en quatre phases ; chemins principaux présents. |
| 9 | Valider et imprimer ASNS depuis Mes élèves | 11 539 / 353 | Insuffisant : annonce « Pour valider et imprimer […] depuis Mes élèves » mais fournit le parcours d’impression du Dossier Natation, puis seulement un retour générique à Mes élèves pour valider. La validation demandée n’est pas expliquée. |
| 10 | Configurer les épreuves dans Dossier Certificatif | 13 160 / 374 | Guidage logiciel utilisable mais réponse non validée : ajoute une dépendance chronologique non soutenue entre protocoles et import des candidats. |

## Deux défauts matériels à traiter sans nouveau rejeu massif

### 9 — Validation et impression ASNS confondues

Sortie : « Pour valider et imprimer l’ASNS depuis Mes élèves, accédez à [Tableau de bord] > [Les Dossiers et Projets] > [Dossier Natation] > [Validation ASNS] […] ». La suite indique de revenir dans Mes Élèves pour valider de nouveaux élèves mais ne décrit pas cette opération.

La fiche natation sépare pourtant impression des élèves déjà validés et retour dans Mes Élèves pour les nouvelles validations. L’article 50 indique l’accès Tableau de bord / Mes Élèves / Visualisation / Savoir Nager, mais son contenu détaillé concerne principalement d’anciens élèves. Il faut examiner le contenu et la sélection, sans inventer les boutons manquants. Sans trace interne, ne pas attribuer exclusivement le défaut au modèle ou au sélecteur.

### 10 — Deux préalables changés en ordre causal

Sortie exacte : « Les protocoles doivent être validés par la CAHPN et déposés dans Cyclades par l'inspection avant que les candidats puissent être importés dans Cyclades. »

La fiche dossier certificatif dit que l’export intervient seulement quand les protocoles sont validés et déposés, **et** que les candidats ont été importés par le service des examens. Elle ne dit pas que la validation des protocoles conditionne l’import des candidats. Le modèle a changé deux préalables à l’export en une relation d’antériorité entre ces préalables. La question portait en outre sur la configuration des épreuves, pas sur ce circuit d’export. Il faut aussi garder la portée académique de cette explication.

## Portée du bilan

Six réponses donnent un guidage utilisable, avec les réserves ci-dessus ; deux ne sont pas validées. Il ne s’agit ni d’une revalidation complète des fiches, ni d’une preuve de fiabilité du corpus. Les résultats montrent des erreurs de branche et de relation logique, au-delà des seuls chemins de menus omis. Aucun appel supplémentaire de diagnostic ou de réparation ; aucun changement de code ou fiche active pendant cette série.

Le cas TZR précédent est accepté par l’utilisateur comme guidage suffisant : ne pas exiger le bouton final exact pour qualifier toute réponse d’échec. Le cas Santorin précédent a montré la restitution finale du chemin chef ; cette série publique ne mesure pas séparément ce mécanisme.
