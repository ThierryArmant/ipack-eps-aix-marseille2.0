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
- Prochaine étape : corriger les thèmes faux de la mesure (fiches) et les demandes de précision inutiles (programme), puis remesurer sur une nouvelle série inédite.

## Entrées

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
