# Répertoire des ambiguïtés iPackEPS / Examens

État au 23 octobre 2026 : répertoire préparatoire, non branché sur le hub. Le correctif dc7cc79 reste conservé. Aucun appel IA n’a été réalisé pour ce travail.

## Corpus et portée

Les copies locales accessibles fournissent 1 236 formulations distinctes après normalisation des accents, espaces et ponctuation. La base consolidée contient 1 239 lignes de questions ; les cinq lots complémentaires disponibles ont été rapprochés de cette base. Le total n’est pas une preuve que la banque annoncée d’environ 1 400 questions est intégralement couverte. Les contextes et provenances restent distincts dans la trace privée. Les réponses historiques, verdicts et consommations ne servent pas à décider de la bonne procédure.

Le repérage thématique a identifié 693 formulations candidates dans au moins une des 24 familles. Ce nombre inclut des questions parfaitement précises et des faux rapprochements lexicaux : il ne mesure ni les ambiguïtés avérées ni les erreurs. Les motifs de repérage ne sont pas des déclencheurs de production. Les questions brutes et leurs correspondances sont conservées hors dépôt public.

## Utilisation prévue

Le répertoire décrit le fait à vérifier avant le choix d’une fiche ; il ne contient pas de réponse réglementaire à réutiliser. Une famille possède des branches reliées aux documents existants, une clarification courte, une réponse libre et un contre-exemple qui ne doit pas déclencher de clarification. Les sept règles de config/lexique_clarification.json restent intactes et sont référencées lorsque pertinentes.

Avant une activation éventuelle : la question complète et les informations explicites du contexte doivent laisser au moins deux procédures documentées plausibles. Le fait manquant doit réellement changer la démarche. Une différence de vocabulaire, plusieurs fiches proches, un score faible ou un mot isolé ne suffisent pas. Une comparaison peut souvent recevoir une réponse conditionnelle sans interrompre le collègue.

Quand l’utilisateur répond, conserver la demande originale et ajouter seulement sa précision. Refaire la sélection et la vérification documentaire. Ne pas transformer le choix en réponse métier. Si aucune source ne couvre le point, le dire ; une clarification ne crée pas une preuve.

## Familles

| ID | Distinction à vérifier | Repères thématiques candidats* |
| --- | --- | ---: |
| A01 | Élèves ou candidats manquants | 119 |
| A02 | Lots absents ou candidats absents du lot | 35 |
| A03 | Import et export : sens du transfert | 51 |
| A04 | Accès impossible ou base élèves vide | 18 |
| A05 | Collègue absent : équipe, mission ou droits sur le lot | 55 |
| A06 | Deux établissements : navigation, personnels ou service | 33 |
| A07 | Activité d’une classe, spécialité du professeur ou AS | 12 |
| A08 | Classe, groupe EPS, protocole ou lot | 38 |
| A09 | Protocole : programmation ou certification | 48 |
| A10 | Contrôle adapté : permanent ou temporaire, règle ou saisie | 37 |
| A11 | Déclaration médicale, statut et résultat | 47 |
| A12 | DI, absence et nombre de notes par diplôme | 59 |
| A13 | Certificat : CCF ou ponctuel | 30 |
| A14 | Valider : quel objet et quel rôle ? | 72 |
| A15 | Soumis, en attente et validé | 43 |
| A16 | Saisie des notes bloquée | 113 |
| A17 | Erreur de saisie, harmonisation ou contestation | 28 |
| A18 | Déposer plusieurs FCA ou composer le menu individuel | 18 |
| A19 | Fiche individuelle, fiche établissement ou référentiel | 9 |
| A20 | Natation : enquête, ASNS ou statistiques | 6 |
| A21 | Année précédente : consulter, recopier, saisir ou conserver | 15 |
| A22 | EPS obligatoire, option, EPPCS et régime d’examen | 186 |
| A23 | SHN : éligibilité, mention, protocole et notation | 43 |
| A24 | Absence individuelle, enseignant absent ou impossibilité collective | 56 |

*Comptages qui se chevauchent, avant validation sémantique. Ne pas les additionner et ne pas les présenter comme des erreurs.*

## Vérification ciblée avec Albert

Le fichier docs/jeu_cible_ambiguities_albert.json prépare 14 essais : 12 formulations dont les deux cas de frontière Cyclades/Santorin sont chacun présentés dans les deux onglets. Les attendus décrivent le comportement à vérifier, pas une réponse métier imposée. Les cas sont des formulations de test rédigées pour ce lot ; aucune question brute de collègue n’est publiée.

Vérifier d’abord le quota et la disponibilité réels. Lancer les cas un par un sur une version figée. Relever le fournisseur réel : un appel Albert refusé suivi du secours GPT ne mesure pas Albert. Examiner les fiches sélectionnées, la question de clarification éventuelle, les preuves et les motifs de réparation, puis les appels, jetons et temps. Une clarification justifiée n’est pas un échec ; une clarification redondante l’est pour ce critère. Aucun seuil global de qualité ne sera déduit de 14 essais.

## Contrôles réalisés

Structure des 24 entrées, identifiants et branches uniques, choix cohérents, texte libre autorisé, rattachement aux 7 règles existantes et existence de 58 chemins documentaires actifs contrôlés. Les 14 cas sont tous marqués non exécutés. Aucun import du répertoire n’a été ajouté à l’application ; aucune consigne de production ni aucun document métier n’a été modifié.
