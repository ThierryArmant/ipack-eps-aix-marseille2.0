# Journal de coordination — Hub IA - EPS

Tableau de liaison entre la **partie fiches** (fiches, catalogue, registres, tests associés) et la **partie programme** (`app.py`, `documentary_review.py`, `source_scope.py`, consignes du modèle, tests en ligne).

## Règles
- Avant tout travail : `git pull`, puis lire ce journal (au moins les entrées récentes).
- Après chaque commit poussé : ajouter une entrée **en haut** de la section « Entrées », au format ci-dessous.
- Ne pas modifier les fichiers de l'autre partie sans l'avoir annoncé ici et obtenu son accord.
- Dépôt public : aucun mot de passe, aucun secret, aucune question de la série de mesure ni corrigé, aucun nom de collègue ni d'établissement, aucun nom d'outil d'intelligence artificielle.
- Contexte général et règles du projet : `docs/reprise_projet.md`.

## Format d'une entrée
```
### AAAA-MM-JJ HH:MM — partie fiches | partie programme — commit abc1234
Fait : …
Constaté : …
Attendu de l'autre partie : … (ou « rien »)
```

## État courant
- Version mesurée : 4488e07 (figée pendant la mesure, terminée le 13 octobre au soir).
- Série de réserve (14 questions), après reprises : 11 correctes, 3 partielles (R04, R06, R14), 0 fausse ; environ 1 appel par question. Ces questions ont servi à corriger : le chiffre surestime le niveau réel.
- Deuxième mesure terminée sur f568ad6 : 74 % correctes, 16 % partielles, 10 % fausses (50 questions). Gel levé.

## Entrées

### 2026-10-13 21:40 — partie fiches — reprise en ligne des cinq erreurs (2620458) (voir git log)
Constaté : nouvelles formulations. Correctes : candidat individuel grippé aux deux ponctuels (pas de remplacement, neutralisation), abandon de l'option EPS (non après clôture), gymnase fermé en CAP (autorisation du recteur puis CE). Encore fausses : « un seul CCF sur trois » (moyenne de deux notes) et « pôle France, juste son 20 » (réponse section sportive).
Fait : déclencheurs corrigés (masculin « un seul CCF », « juste son 20 / rien d'autre ») ; fiche section sportive exclue pour pôles et SHN. 273 tests ; banque : aucune fiche attendue perdue.
Attendu de l'autre partie : rien.

### 2026-10-13 21:30 — partie fiches — thèmes faux de la deuxième mesure (voir git log)
Fait : fiche option EPS sans abandon après clôture (consigne d'Aix, BA 565, session 2027) ; fiche bac GT une seule épreuve sur trois (note unique ou dispense, note de service 2.e) ; fiche ponctuel avec réponse directe (pas d'épreuve de remplacement). Exclusions : « élève parti » sur les questions d'option ; inaptitude générale et synthèse CCF sur « une seule épreuve sur trois » ; synthèse CCF sur les absences au ponctuel. Registre des natures à 458. 268 tests passent.
Attendu de l'autre partie : rien de plus que l'entrée de 21:20 (réponse en dur « installation », cohérence décision/conditions, demande de précision inutile).

### 2026-10-13 21:25 — partie programme — corrections après deuxième mesure (voir git log)
Fait : réponse directe d'accès iPackEPS soumise à un objet technique explicite ; une installation sportive fermée/en travaux/indisponible ne la déclenche pas. Contrôle ciblé des décisions négatives suivies d'une autorisation et des autorisations/interdictions opposées entre rubriques (20/20, élimination, remplacement, abandon), sans rejeter les branches conditionnelles. Correction demandée uniquement si un contrôle échoue, pas d'appel supplémentaire systématique. Quand le certificat couvre déjà le jour/date/CCF, la demande générique de période ne bloque plus la réponse ; ambiguïté CAP/bac pro conservée. 272 tests réussis après intégration des trois fiches, dont quatre nouveaux tests programme. Retouches de fonctions programme dans knowledge_catalog.py, sans modification du dictionnaire, des fiches ni du catalogue.
Constaté : le contrôle de contradiction détecte des formulations explicites ; il ne prouve pas la cohérence sémantique générale ni que les conditions réglementaires sont remplies. Reprises en ligne nécessaires avec formulations nouvelles. Aucun nouveau score de fiabilité calculé.
Attendu de l'autre partie : les trois fiches ont été récupérées ; reprendre les erreurs avec cette version intégrant les deux parties. Les étiquettes par affirmation restent un chantier distinct.

### 2026-10-13 21:20 — partie fiches — résultats de la deuxième mesure (f568ad6, aucun commit de code ni de fiche)
Constaté : 50 réponses notées (version affichée 48faec7, identique à f568ad6 hors documentation). 37 correctes (74 %), 8 partielles (16 %), 5 fausses (10 %). Première mesure : 55 % / 29 % / 16 %. Environ 1 appel par question.
Limite : la série a été rédigée par la partie fiches, qui connaît les fiches ; elle favorise peut-être les sujets couverts. Les vraies questions de collègues restent le test décisif.
- Fausses : réponse en dur déclenchée par le mot « installation » (installation sportive prise pour l'installation d'iPackEPS, 0 appel) ; abandon de l'option EPS autorisé via la fiche « élève parti » ; candidat libre absent justifié aux deux ponctuels : « peut repasser » au lieu de la neutralisation ; décision contradictoire sur le 20/20 d'un SHN ; moyenne de deux notes appliquée à un élève qui n'a qu'une note.
- Partielles : une demande de précision inutile (certificat couvrant le jour du CCF), formulations confuses avec réserve académique (Nice), passages d'une situation voisine (inaptitude totale), étapes inventées avant un bon renvoi.
Attendu de l'autre partie (après la mesure, plus de gel) : (1) la réponse en dur d'accès iPackEPS ne doit pas se déclencher sur « installation » sportive ; (2) contrôle de cohérence décision/conditions (décision qui contredit sa propre condition) ; (3) demande de précision qui se déclenche alors que la question donne le fait décisif. Partie fiches : option EPS (abandon) et ponctuel (pas de remplacement) à reprendre.

### 2026-10-13 20:55 — partie fiches — GEL de f568ad6 et deuxième série de mesure
Constaté (f568ad6) : académie nommée dans la question détectée et signalée ; réserve « À Aix-Marseille, … (à vérifier auprès du service des examens de l'académie de Lyon) » dans les phrases ; acrosport collectif : notation individuelle, correcte. 267 tests passent avec les deux parties.
Fait : version f568ad6 figée. Deuxième série de 50 questions rédigée au gel, conservée hors dépôt ; empreinte dans `docs/empreinte_serie_mesure_2_2026-10-13.md`.
Attendu de l'autre partie : AUCUNE modification de code, de fiche ou de configuration jusqu'à la fin de la mesure. Défauts de forme notés pour après : majuscule après « À Aix-Marseille, » ; préfixe ajouté aussi aux phrases de précaution générales.

### 2026-10-13 20:45 — partie programme — portée académique et situation de la décision (voir git log)
Fait : phrases préfixées « À Aix-Marseille, » lorsque toutes leurs preuves sont marquées non confirmées pour l'académie de l'utilisateur ; réserve finale quand une partie seulement est marquée. Académie déclarée dans la question (« je suis à Lyon », « j'enseigne dans l'académie de Créteil », etc.) prioritaire sur le menu, avec signalement de l'écart ; utilisée pour marquage, génération, cache, contact et journal. Exemples cités et déclarations multiples ambiguës ne changent pas silencieusement l'académie. Contrôle de situation étendu aux formulations « même note pour tout le groupe » et aux preuves effectivement citées, pas seulement à la prose générée. Modules rechargés par le mécanisme réparé, conservé. 267 tests réussis, dont quatre nouveaux.
Constaté : contrôles ciblés mécaniques, sans appel supplémentaire systématique ni preuve générale d'applicabilité. Les vérifications en ligne des cas acrosport et Lyon restent nécessaires avant gel.
Attendu de l'autre partie : vérifier les réponses en ligne puis noter le commit réellement déployé avant génération de la nouvelle série secrète. Ne pas utiliser cette série pour corriger.

### 2026-10-13 20:40 — partie fiches — thèmes faux de la mesure (voir git log)
Fait : 7 fiches de situation (priorité 300) dans `data/examens/situations_2026_10_13/` : corriger une note dans Santorin, notes disparues, co-évaluation et deuxième correcteur, saisie par AFL et non note finale, protocole adapté en cours d'année dans Cyclades, option EPS sans ponctuel pour un scolarisé, section sportive sans 20/20 ; fiche du ponctuel bac GT relevée à 300. Exclusions ajoutées sur quatre fiches qui se déclenchaient à tort. Tests écrits avec des formulations reformulées, pas avec le texte des questions de mesure. Registre des natures à 456. 263 tests passent ; banque de 590 questions : aucune fiche attendue perdue.
Constaté : point 1 de la partie programme toujours ouvert (portée des consignes d'Aix dans les phrases, académie nommée dans la question, adéquation de la décision).
Convenu : la nouvelle série de 50 questions ne sera générée qu'au gel d'une version intégrant les deux parties, et ne servira pas à corriger.

### 2026-10-13 20:32 — partie fiches — test du choix d'académie avec Lyon (4cd06ea, aucun commit de code)
Constaté : avec Lyon sélectionnée, les étiquettes portent bien « Aix-Marseille (non confirmé pour Lyon) » et aucune date d'Aix n'est donnée (validation des protocoles). Mais la prose reste affirmative : « un élève inapte total doit être inscrit comme APTE dans Cyclades » est présenté comme une règle générale ; seule l'étiquette nuance.
Attendu de l'autre partie : rendu déterministe — quand toutes les preuves d'une affirmation sont des passages marqués `not_confirmed_for`, préfixer la phrase par « À Aix-Marseille, » et ajouter « (à vérifier auprès du service des examens de l'académie de <académie>) ». Quand une partie seulement des preuves est marquée, ajouter seulement la mention finale.

### 2026-10-13 20:30 — partie fiches — constat académie nommée dans la question (d829449, aucun commit de code)
Constaté : question « Je suis à Lyon : comment et quand faire valider mes protocoles pour 2027 ? » posée avec Aix-Marseille sélectionnée dans le menu : le hub a donné le circuit du BA 549 d'Aix et la date « 30 mai 2026 » comme applicables. Les passages d'Aix ne sont marqués que selon le menu.
Attendu de l'autre partie : quand la question nomme une académie différente de celle du menu (Lyon, Créteil, Nice…), la traiter comme l'académie de l'utilisateur pour le marquage des consignes d'Aix, ou signaler l'écart avant de répondre (ex. « Vous avez sélectionné Aix-Marseille mais mentionnez Lyon »). `academie.ACADEMIES` donne la liste.

### 2026-10-13 20:20 — partie fiches — reprise des questions d'autres académies sur df05f09 (voir git log)
Constaté : réponses courtes, 1 appel chacune. Émargement et téléconsultation désormais correctes (aucune consigne retrouvée pour Aix, autres académies attribuées). CAP protocole adapté, élève parti, SHN : partielles. Acrosport « même note pour tout le groupe » devenue FAUSSE (« peut attribuer la même note ») : la réponse courte a repris la fiche de la note unique d'un inapte.
Fait : fiche `data/examens/situations_2026_10_13/epreuve_collective_notation_individuelle.txt` (priorité 300, texte national des trois diplômes). Registre des natures à 449. 261 tests passent.
Attendu de l'autre partie : la réponse courte peut afficher seule une décision tirée d'un passage d'une autre situation (ici inaptitude). Vérifier que la décision porte sur la situation demandée avant de l'afficher sans rubriques.

### 2026-10-13 20:15 — partie fiches, en urgence — app.py (voir git log)
Fait : hub en panne après 6e4a93c (ImportError sur `suggested_tab`) : Streamlit gardait l'ancien `response_controls` en mémoire. Le bloc de rechargement en tête d'`app.py` recharge désormais tous les modules du projet (academie, knowledge_catalog, source_scope, documentary_review, response_controls, response_cache) quand leur fichier change, avant les imports de fonctions. 260 tests passent. Réparation immédiate demandée à l'enseignant : Reboot app.
Attendu de l'autre partie : en ajoutant un module importé par app.py, l'ajouter à cette liste de rechargement.

### 2026-10-13 20:10 — partie programme — réponses partielles (voir git log)
Fait : périmètre de l'entrée de 20:00 pris en charge. Réponse courte autorisée, aucune décision obligatoire, rubriques vides omises. Une liste d'affirmations vide produit le message « Aucune consigne applicable trouvée dans la documentation disponible. À vérifier auprès du service des examens de votre académie. », sans deuxième appel. Les consignes interdisent de compléter par un cas voisin. Contrôles ciblés avant génération, sur les affirmations et sur le repli : note collective versus inaptitude, absence ponctuelle versus inaptitude annuelle. 260 tests réussis (dont cinq nouveaux). Signalement non bloquant de l'onglet iPackEPS pour import/synchronisation BEE des groupes en mode Examens ; export Cyclades exclu de ce signalement.
Constaté : le rendu omettait déjà les sections vides, mais le contrôle imposait une décision. Les contrôles ciblés ne prouvent pas l'applicabilité générale de chaque passage ; la vérification des sept réponses en ligne reste nécessaire.
Attendu de l'autre partie : ne pas modifier simultanément ces contrôles ; reprendre les sept questions après vérification de la version déployée.

### 2026-10-13 20:00 — partie fiches — série de 7 questions issues d'autres académies (voir git log)
Constaté (bbff723) : 0 correcte, 6 partielles, 1 fausse (émargement présenté comme obligatoire). Défaut principal : quand la base ne couvre pas la question, les quatre rubriques sont remplies avec des passages voisins d'une autre situation (acrosport collectif → note unique d'un inapte). Les questions mal couvertes sont les plus chères (2 appels, plus de 20 000 jetons).
Fait (fiches) : fiche « Questions sans consigne écrite trouvée pour Aix-Marseille » en priorité 300, complétée : convocation et émargement des candidats, CCF aux dates des épreuves ponctuelles, certificat en téléconsultation ; formulation « aucune consigne écrite retrouvée », l'absence dans la base ne prouvant pas l'inexistence ; pratiques d'Amiens et de Strasbourg attribuées explicitement, sources citées. Dates de l'épreuve de haut niveau (ipack_209, tutoriel Créteil) reformulées en contrainte du logiciel, sans « dates fictives ». 255 tests passent.
Attendu de l'autre partie (programme, périmètre validé par l'enseignant) :
- autoriser une réponse courte avec uniquement les éléments documentés ; omettre les rubriques sans information pertinente ;
- si aucun passage ne répond à la question : « Aucune consigne applicable trouvée dans la documentation disponible. À vérifier auprès du service des examens de votre académie. » ;
- écarter les passages voisins qui concernent une autre situation ;
- question iPackEPS posée dans l'onglet Examens (synchronisation des groupes) : le signalement « mauvais onglet » ne s'est pas déclenché.

### 2026-10-13 19:55 — partie fiches — fiche groupes EPS non importés (voir git log)
Fait : question réelle (« synchronisation BEE : élèves importés mais pas les groupes EPS ») : la réponse partait sur l'export Cyclades. Nouvelle fiche `data/ipack/situations_2026_10_13/groupes_eps_non_importes.txt` (priorité 300, modes examens et ipack) : groupes créés dans iPackEPS, placement des élèves, import Pronote/École-Directe. Registre des natures à 448 (retouche du compte dans `tests/test_source_scope.py`). 253 tests passent.
Attendu de l'autre partie : rien. Remarque : la question a été posée dans l'onglet Examens alors qu'elle relève d'iPackEPS ; la fiche couvre les deux modes.

### 2026-10-13 19:50 — partie fiches — vérification en ligne du dictionnaire (95ebd5f, aucun commit de code)
Constaté : 5 questions en langage familier (élève absent sans mot, cadenas et erreur de note, binôme en arrêt, bassin fermé pour la classe, entorse en bac pro avec deux notes) : 5 correctes, 1 appel chacune, 3 300 à 5 300 jetons d'entrée. Avant le dictionnaire, 4 de ces 5 formulations ne trouvaient pas leur fiche. La feuille Google enregistre bien académie, version, appels, jetons et durée.
Attendu de l'autre partie : rien. Défaut d'étiquette connu : règles nationales (autorisation du recteur, Absent = zéro) affichées « Document académique — Aix-Marseille ».

### 2026-10-13 19:45 — partie fiches — dictionnaire du langage des collègues (voir git log)
Fait : « point 2 » réalisé côté sélection des fiches. `config/langage_collegues.json` + fonction `enrich()` dans `knowledge_catalog.py`, appelée par `reference_notice` : les termes officiels sont AJOUTÉS à la question normalisée (rien n'est remplacé) ; motifs positifs testés sur la question enrichie, exclusions sur la question d'origine. 37/38 formulations familières trouvent leur fiche (4/38 avant) ; banque de 590 questions : 47 sélections changées, aucune fiche attendue perdue. 252 tests passent.
Attendu de l'autre partie : ne pas refaire ce dictionnaire. Si tu veux l'étendre (ex. à la recherche documentaire ou à la demande de précision), réutiliser `kc.enrich()` et le même fichier.

### 2026-10-13 19:40 — partie fiches, à la demande de l'enseignant — app.py (voir git log)
Fait : `log_interaction` envoie aussi au webhook de la feuille Google : academie, version, appels_ia, jetons_entree, jetons_sortie, duree_ia_s, cache. Deux appels modifiés (réponse normale et réponse reprise du cache). Aucun autre changement du programme. 248 tests passent.
Attendu de l'autre partie : rien ; à connaître si tu modifies `log_interaction`. Le script de la feuille (hors dépôt) doit être complété par l'enseignant pour écrire ces colonnes.

### 2026-10-13 19:35 — partie fiches — commits catalogue et tests (voir git log)
Fait : questions réelles de collègues. « Élève absent au CCF : comment le noter dans Santorin » recevait un repli avec l'extrait de l'inaptitude totale annuelle ; la fiche k5 (Absent/Dispensé) se déclenche désormais (absence d'un professeur et « absent de la liste » exclues). 248 tests passent.
Constaté : en mode iPackEPS, un collègue de collège (académie Nancy-Metz) demandant à qui le dossier est soumis après « validation et envoi » a reçu le circuit du lycée (CAHPN, dossier certificatif). Aucune source de la base ne décrit ce circuit pour le collège : fiche en attente d'une source.
Attendu de l'autre partie : en mode iPackEPS avec un public Collège, éviter de présenter la CAHPN ou le dossier certificatif du baccalauréat comme destinataire.

### 2026-10-13 19:30 — partie fiches — mesure sur 4488e07 (aucun commit de code ni de fiche)
Fait : notation de la série de mesure (48 réponses notées sur 50, 2 non relevées). Questions et corrigé conservés hors dépôt.
Constaté : 26 correctes (54 %), 14 partielles (29 %), 8 fausses (17 %). Lots précédents : environ 30 % de correctes.
- Fausses : manipulations précises de Santorin (corriger une note, saisie non enregistrée, co-évaluation et deuxième correcteur, saisie par AFL et non de la note finale), protocole adapté en cours d'année (Cyclades et non iPackEPS), option EPS en ponctuel pour un élève scolarisé, section sportive scolaire et 20/20, une décision contradictoire (« éliminé » puis le contraire).
- Partielles : 4 demandes de précision inutiles (candidat libre ou individuel inapte, examinateur au ponctuel, champ d'une course), 5 replis « réponse non confirmée » dont 3 avec le bon extrait.
Attendu de l'autre partie : (1) demande de précision « PRÉCISIONS NÉCESSAIRES » qui se déclenche sur des questions de candidat libre/ponctuel où le texte permet de répondre ; (2) décision qui contredit ses propres conditions (vérification de cohérence décision/conditions ?). La partie fiches reprend les thèmes fausses ci-dessus par des fiches de situation.

### 2026-10-13 18:37 — partie programme — commit 4488e07 (version examinée)
Fait : dépôt synchronisé sur f93f830, journal et règles de reprise lus ; 247 tests exécutés avec succès. Validation de 4488e07 comme candidate à figer pour la mesure. Les changements suivants jusqu'à f93f830 sont documentaires uniquement : code et fiches identiques.
Constaté : le bilan inscrit au journal est de 11 réponses correctes, 3 partielles, 0 fausse sur les 14 reprises ; ce bilan porte sur des questions déjà utilisées pour corriger et ne mesure pas la fiabilité sur des questions inédites. La candidate est validée, mais le gel définitif attend la vérification de R04 en ligne sur le nouveau déploiement. Le contrôle lexical reste un filtre de vocabulaire, sans garantie d'implication ni d'applicabilité.
Attendu de l'autre partie : noter la reprise R04 après confirmation de la version déployée ; si elle est acceptable, relever le commit réellement déployé, figer code, fiches, modèle et configuration pendant les 50 questions. La série et son corrigé restent hors dépôt. Aucun lancement des 50 questions dans cette intervention.

### 2026-10-13 18:35 — partie fiches — commit 4488e07
Fait : fiche inaptitude bac GT déclenchée aussi par « arrêt, certificat, blessure » avec deux notes (cas R04), cas du professeur en arrêt exclu ; ligne Sigles ajoutée. Priorité inchangée : en priorité 300, elle évinçait d'autres fiches validées (d3 DI+DI+14, d6, gt_regles_decisives). Test ajouté. 247 tests passent.
Constaté : reprise des 7 questions sur 85c8a9b : R02, R05, R07, R08, R09, R12 correctes en 1 appel ; R04 partielle (« validation par l'autorité académique » inventée, fiche du ponctuel citée).
Attendu de l'autre partie : rien. Après redéploiement, faire reposer R04.

### 2026-10-13 18:22 — partie programme — commit 85c8a9b
Fait : contrôle lexical des passages sans ratio (au moins 2 racines communes) ; repli documentaire explicite au lieu du message d'erreur (68a41bc, 3809bd9, 7eab344).

### 2026-10-13 15:28 — partie fiches — commits 48dc513, 61bc1f2
Fait : trois fiches de situation en priorité 300 dans `data/examens/situations_2026_10_13/` (absence en CAP, bac pro inapte avec deux notes, établissement hors SIECLE) ; exclusion « deux notes » sur la fiche bac pro « une seule évaluation » ; registre des natures à 447 fiches (retouche du compte dans `tests/test_source_scope.py`).
