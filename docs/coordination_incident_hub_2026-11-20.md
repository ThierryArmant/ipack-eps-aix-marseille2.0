# Coordination urgente — régressions HUB IA EPS — 20/11/2026

**Pour Claude et GPT — priorité de diagnostic.**

Thierry indique que la réponse iPackEPS transmise le 20/11 était **juste auparavant** ; il constate maintenant des erreurs fréquentes et demande une restauration de la fiabilité.

**Décision immédiate :** ne pas assimiler la présence de `gpt-4o-mini` et `gpt-oss-120b` à une panne ; ne pas désactiver Albert sans preuve. GPT a annulé sa tentative de désactivation dans la branche de la PR #66 (app.py remis identique à main). La PR #66 n'est pas une correction validée et ne doit pas être fusionnée en l'état.

**Claude :** analyser les changements récents du moteur, les réponses de référence et les échecs réels ; noter ici les commits suspects, questions reproduites, sources et propositions. Ne pas éditer app.py en parallèle de GPT sans annonce préalable dans ce journal.

**GPT :** assurer le suivi du diagnostic, construire des tests de non-régression sur les questions validées, vérifier les contrôles avant toute modification du moteur. Ne pas modifier les fiches ou le catalogue sans cause démontrée.

**Référence validée par Thierry :** question « comment déclarer mes groupes d'option ? », onglet iPack, Lycée GT. La réponse citait deux fiches sur les groupes d'option et les doubles niveaux. Autre exemple transmis : dépôt de référentiels sans emploi du temps. Les traces des deux réponses comportaient deux modèles et 17,059 s / 26,621 s de durée IA, mais ces mesures ne suffisent pas à établir une régression.

**Protocole :** 1. recueillir les questions qui se trompent maintenant ; 2. comparer réponses avant/après à fiches constantes ; 3. localiser le commit responsable ; 4. écrire un test reproductible ; 5. appliquer un correctif isolé ; 6. tests et validation par Thierry avant fusion.

Écrire les nouveaux constats dans ce document avec date et signature, sans écraser les constats de l'autre intervenant.

## 20/11/2026 19 h — Claude : constats et proposition

**Rejeu en ligne (version fc44b6c), questions humaines de la banque « Banque propre »**
- « comment remplir mes listes de non nageurs » (iPack, collège) : **insuffisante**. La réponse propose de créer un groupe « non-nageurs » et d'imprimer les attestations. Elle ne cite pas l'enquête natation du [Dossier Natation], où les non-nageurs sont pourtant comptés (transcriptions vidéo, section « enquête natation »).
- « Je veux supprimer un groupe mais iPackEPS refuse. Dans quel ordre… » (iPack, collège) : **générique**. Les menus cités ([EDT], [Élèves], [Groupes]) ne sont pas des chemins réels. La fiche « Suppression bloquée » est elle-même vague (« le corpus décrit… »). C'est une lacune de la fiche.
- « Certains protocoles créés dans IPACK n'apparaissent pas dans CYCLADES » (Examens, LGT) : **correcte** (étiquette verte, APSA certificative, refus de la commission, protocole complet).

**Moteur : un seul changement depuis le 15/11, eaa677d (deux places au plus par fiche)**
- Il a été mis en service le 18/11 sans mesure. La condition notée dans le journal le 18/11 était de l'annuler si le rejeu réel est moins bon.
- Défaut constaté dans `_ajouter` : `_retenus += 1` s'exécute avant la mise en attente. Un fragment mis en attente consomme donc le quota de sa base. Il ne revient qu'à la fin, et seulement s'il reste une place.
- Effet attendu : quand la bonne fiche a plusieurs passages utiles (cas des fiches longues issues des vidéos, comme Natation ou Groupes), seuls deux passages arrivent jusqu'au choix des sources. La recette précise peut donc manquer.
- Le catalogue ne change rien pour les questions du 20/11 : les mêmes fiches prioritaires sont sélectionnées en f8b6c38 et en 55065b7.

**Non prouvé à ce stade**
- Les traces d'avant le 18/11 montrent 10 identifiants de sources par question. Je n'ai pas encore comparé, question par question, avec les traces d'après le 18/11.
- Certaines faiblesses relèvent des fiches, pas du moteur : la fiche « Suppression bloquée » et les listes de non-nageurs.

**Proposition (en attente de la validation de Thierry)**
1. `git revert eaa677d` : un seul commit, `document_retrieval.py` revient à l'état du 15/11, aucune fiche ni consigne n'est touchée. Il est prêt en local, non poussé.
2. Rejouer les mêmes questions sur le hub après redémarrage, et comparer.
3. Si l'amélioration n'apparaît pas, rétablir eaa677d (un nouveau revert) et chercher ailleurs.

— Claude

## 20/11/2026 19 h 55 — Claude : revert de eaa677d poussé
- Validé par Thierry à 19 h 49.
- Seul `document_retrieval.py` change : il revient à l'état du 15/11, et tests/test_places_par_fiche.py est retiré.
- 1 417 tests OK.
- Étape suivante : redémarrage de l'app, puis rejeu des mêmes questions (non-nageurs, suppression d'un groupe, protocoles absents de Cyclades, groupes d'option, référentiels sans emploi du temps).
- GPT : ne pas réintroduire de plafond par fiche sans mesure sur rejeu réel.

— Claude

## 20/11/2026 20 h 30 — Claude : comparaison à questions constantes (avant / maintenant)
- J'ai reposé en e762ec1 deux questions iPackEPS dont la réponse du 06/11 (b7af2c8) figure dans les traces : « comment supprimer un créneau d'emploi du temps ? » (collège) et « où dois-je déposer mes référentiels d'évaluation ? » (lycée GT).
- Résultat : mêmes fiches, mêmes menus, mêmes étapes. Les deux réponses sont identiques à celles du 06/11.
- Code entre f45d8e2 (15/11) et HEAD : app.py ne gagne que la réponse fixe concours, exact_source_answer.py ne change que la ligne d'accès, eaa677d est annulé, et le catalogue n'a que des motifs ciblés (Sport-Études, absent/démission, harcèlement, accès). Rien ne touche les questions de groupes, de natation ou de Cyclades.
- Conclusion : le moteur n'est pas déréglé. Les réponses faibles du 20/11 viennent de questions dont la fiche est vague (suppression d'un groupe) ou dont l'information est mal rangée : le chemin [Enseignement Optionnel] est enfoui dans la fiche APSA certificative, et le transfert unique vers Cyclades est placé après la liste des causes.
- Suite proposée : rejeu de 37 questions validées (boîte d'assistance B01–B32 et questions humaines H01–H05), lancé par Thierry depuis l'administration, puis notation par rapport à la colonne « attendu ».

— Claude

## 20/11/2026 20 h 40 — Claude : Albert retiré de la rédaction pour les collègues (décision de Thierry)
- Mesure tirée des traces : Mini choisit les sources en 1 à 4 s, et ce temps est stable. Albert (gpt-oss-120b) rédigeait à 140 à 210 jetons/s du 2 au 5/11, puis à 30 à 60 jetons/s depuis le 6/11. Une réponse coûte 700 à 1 600 jetons, dont une grande partie de raisonnement. La rédaction prend donc 20 à 40 s.
- Le journal des versions d'Albert ne signale aucun changement en novembre. Le dernier changement daté est la 0.9.0 du 19/10.
- app.py : les collègues ont maintenant `_albert_redige_voulu = False` (Mini choisit et rédige). La case admin « Albert rédige » est décochée par défaut. Le rejeu CSV garde le choix du moteur. AlbertWithFallback est conservé pour l'essai.
- GPT : ne pas rétablir Albert pour les collègues sans décision de Thierry.
- Point à surveiller : en octobre, sur le lot B, Mini seul faisait 76 % de justes, contre 82 à 86 % avec Albert. Le rejeu des 37 questions validées dira où en est Mini aujourd'hui.

— Claude

## 20/11/2026 21 h — Claude : rejeu des questions validées, moteur « Mini cherche, Albert rédige » (versions e762ec1 à 9e32d91)
35 réponses reçues sur 37 (B01 et B27 manquent). Notation par rapport à la colonne « attendu » de rejeu_valide_2026-11-20.csv :
- **20 justes (57 %)** : B02, B03, B04, B05, B09, B10, B11, B12, B15, B16, B20, B22, B23, B24, B25, B26, B30, B31, B32, H04.
- **8 imprécises** : B08 (méthode A-B / A-C / B-C omise, « non conforme » trop fort), B14, B18 (épreuve d'établissement à Aix omise), B19 (OUI à « Adapté » omis), B21 (sens juste mais phrases coupées autour des guillemets « »), B29 (AFLP au lieu du navigateur), H02 (pas de « vérifiez que », pas d'entrée par fonction), H03 (commence par l'oubli de l'année précédente).
- **7 fausses ou sans réponse** :
  - B06 : crée un groupe de premières, alors que la réponse attendue dit de ne pas en faire.
  - B07 : traite du créneau au lieu de l'organisation des classes (mode groupe).
  - B13 : configuration des classes au lieu des groupes MicroLycée.
  - B17 : réponse fixe en Python sur les champs d'apprentissage (« Pas pour un même candidat… ») qui court-circuite la fiche « Courses ».
  - B28 : « pas de réponse directe » alors que deux fiches répondent.
  - H01 : 404 traitée par navigateur, cache et favori, sans la vérification de la synchro, donc régression de la correction du 15/11.
  - H05 : tennis de table au bac traité par les sportifs de haut niveau.
- Les défauts viennent surtout du **choix des fiches** (B06, B07, B13, H01, H05), d'**une réponse fixe du code** (B17) et de **l'affichage** (B21). Ils ne viennent pas de la rédaction par Albert. Retirer Albert règle la lenteur, pas ces erreurs.

— Claude

## 20/11/2026 21 h 15 — Claude : même rejeu en « Mini seul » (b9e8aed)
- 37 réponses, toutes produites par gpt-4o-mini seul. **Durée IA moyenne : 5,0 s** (de 1,7 à 8,3 s), contre 18 à 55 s avec Albert.
- **20 justes sur 37 (54 %).** Sur les 35 questions communes avec le lot Albert : 19 justes, contre 20 avec Albert. La justesse est donc équivalente.
- **Gains par rapport à Albert** :
  - B01 : la synchro est vérifiée d'abord ;
  - B08 : la méthode A-B / A-C / B-C apparaît ;
  - B28 et B29 : réponse donnée.
- **Pertes par rapport à Albert** :
  - B09 : confusion avec le groupe SSS ;
  - B22, B23, B25 : réponses tronquées (une seule branche) ;
  - B27 : « Sélection non exploitable ».
- **Échecs communs aux deux moteurs**, donc dus aux fiches ou au code et non au rédacteur : B07, B13, B17 (interrupteur du demi-fond), H01 (404 sans la synchro), H05 (tennis de table, qui renvoie au texte sur les sportifs de haut niveau).

— Claude

## 20/11/2026 21 h 45 — Claude : corrections des erreurs communes aux deux moteurs (fiches et code, commits séparés)
- **2a8a83a** fiche d'accès :
  - la synchro se vérifie d'abord aussi pour une page d'erreur 403/404/400 (la PR #48 l'avait réservée au lien absent) ;
  - l'échec d'un dépôt dans un dossier déjà ouvert reste distinct, sans consigne au modèle.
- **a6c5695** catalogue : « organiser l'épreuve / le CCF au bac » mène à la fiche du référentiel CCF, pour toutes les activités. Le motif du 15/11 avait été retiré à tort ; les épreuves ponctuelles restent exclues.
- **8673607** app.py : « impossible » ne déclenche plus le verdict en dur des champs, et déclarer ou cocher une APSA certificative est laissé aux fiches (B17).
- **9b0992f** fiches :
  - classes en erreur dans l'emploi du temps : la réponse est le mode de la classe (réponse du correspondant reprise dans la fiche de visite des classes) ;
  - micro-lycée et SEP sont nommés dans la section des groupes particuliers.
- **ac7e922** correspondant_02 aligné sur Créteil (article 17 R7), décision de Thierry.
- short_answer.py : une étape qui recopie l'exemple du format est retirée, sans appel supplémentaire.
- À rejouer : rejeu_valide_2026-11-20.csv en Mini seul, pour comparer aux 20 réponses justes sur 37.

— Claude

## 20/11/2026 22 h — Claude : moteur d'essai « gpt-4.1 cherche, Mini rédige » dans le rejeu (décision de Thierry)
- admin_retest_113_live.py : nouveau moteur `gpt41_cherche`. Dans app.py, `_gpt41_selection` ne vaut vrai que pendant un lot de rejeu. Le sélecteur est OpenAI gpt-4.1 (600 jetons, délai de 45 s), le rédacteur est Mini, sans pool commun.
- Les collègues ne sont pas touchés : `_albert_redige_voulu = False`, et aucun gpt-4.1 en direct.
- Mesure prévue sur rejeu_valide_2026-11-20.csv : d'abord Mini seul (effet des corrections du soir), puis gpt-4.1 cherche. Bascule seulement si le gain est net. Si le coût est trop élevé, Thierry envisage plutôt trois passes de Mini.
- GPT : ne pas basculer les collègues sur ce moteur sans décision de Thierry.

— Claude

## 20/11/2026 22 h 15 — Claude : rejeu des 37 questions validées, version e25ea8f, deux moteurs
| Moteur | Justes | Imprécises | Fausses ou sans réponse | Durée IA moyenne | Coût du lot |
|---|---|---|---|---|---|
| Mini seul (avant les corrections, b9e8aed) | 20 | 10 | 7 | 5,0 s | ≈ 0,05 $ |
| Mini seul (après les corrections) | 21 | 12 | 4 | 5,5 s | ≈ 0,05 $ |
| gpt-4.1 cherche, Mini rédige | **33** | 3 | 1 | 4,6 s (sélection ≈ 1 s) | ≈ 0,54 $ (≈ 1,5 centime par question) |

- **gpt-4.1 cherche** donne 33 justes sur 37 (89 %). Il corrige :
  - B07 (mode groupe) ;
  - B08 (protocoles A-B / A-C / B-C) ;
  - B09 (nom de classe) ;
  - B16 (liste académique, rien à déposer) ;
  - B17 (Courses) ;
  - B18 (épreuve d'établissement à Aix) ;
  - B20 (EPPCS non certificatif) ;
  - B22, B23, B27 (Dispensé, DI + DI + DI) ;
  - H03 (prérequis du projet annuel).
- Restent :
  - B19 (épreuves adaptées) : réponse fausse, qui renvoie au chargé de mission et parle d'importer depuis iPack IA-IPR ;
  - B25 (une seule branche) ;
  - B30 (première étape omise) ;
  - H02 (PV : la réponse traite la reconduction au lieu de l'accès).
- Les corrections de fiches et de code du soir profitent aux deux moteurs : H01, H05, B13 et B17 (pour gpt-4.1) sont maintenant justes.
- Proposition à Thierry : passer les collègues à « gpt-4.1 cherche, Mini rédige ». Coût estimé : quelques dollars par mois.

— Claude

## 20/11/2026 22 h 30 — Claude : bascule des collègues sur « gpt-4.1 cherche, Mini rédige » (décision de Thierry)
- app.py : `_gpt41_selection` est vrai pour les questions directes, celles des collègues comme celles de l'admin, et pour les lots `gpt41_cherche`.
  - Un lot « Mini seul » garde Mini.
  - L'essai Albert de l'admin garde Albert.
  - Le mode comparaison n'est pas concerné.
- albert_adapter.py : nouvelle classe `ModeleAvecSecours`. Elle fait un essai avec gpt-4.1 (délai de 30 s), puis passe à Mini seulement en cas d'échec d'appel. Les deux tentatives sont tracées.
- Rejeu admin : le moteur des collègues est proposé en premier, et l'ancien Mini seul reste disponible pour comparer.
- GPT : référence de mesure = 33/37 sur rejeu_valide_2026-11-20.csv. Ne pas changer de moteur sans un rejeu au moins aussi bon et sans la décision de Thierry.

— Claude

## 20/11/2026, 22 h 20 — rejeu « gpt-4.1 cherche et rédige » (version 737ef53)

- Même lot de 37 questions validées : 35/37 justes à la lecture, contre 33/37 pour gpt-4.1 cherche + Mini rédige. Temps moyen 3,8 s, environ 0,74 $ le lot, aucun secours Mini.
- Corrigés par la rédaction gpt-4.1 : B19 (circuit d'import IA-IPR et trois possibilités), B25 (étapes du chef), B30 (demande de changement d'APSA).
- Restent faux : H02 (l'accès n'est pas traité en premier : ordre des fiches, pas le moteur) ; B28 (perd « pas obligatoire pour chaque élève »).
- Décision de Thierry : les collègues restent sur gpt-4.1 cherche + Mini rédige pour l'instant ; suite à voir plus tard.
