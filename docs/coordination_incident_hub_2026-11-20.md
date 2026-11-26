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
- Mise à jour 22 h 25 : Thierry décide finalement de passer les collègues en gpt-4.1 partout (choix et rédaction), Mini en secours. Référence désormais : 35/37.


## 20/11/2026 — GPT : retour sur le nouveau rejeu externe de 30 questions (Examens)

- Fichier reçu de Thierry : `retest_113_reponses_privees (13).csv` ; 30 lignes, moteur déclaré `gpt41_tout`, version indiquée `8cd8e10`. Lot distinct des 37 questions B/H ; questions WEB01–WEB30 inspirées de situations réglementaires publiques et reformulées, et non citations littérales de collègues.
- Première notation qualitative communiquée à Thierry à partir du corrigé du lot : **21 correctes, 8 partielles/à nuancer, 1 incorrecte** (WEB15). Cette notation reste **provisoire** : confronter chaque attendu aux sources officielles applicables et examiner les extraits sélectionnés avant d'imputer les erreurs au moteur.
- Cas à examiner : **WEB15**, sportif de haut niveau : la réponse s'oriente vers l'inaptitude plutôt que vers le statut sportif ; **WEB29**, adaptation en ponctuel ; **WEB06, WEB07, WEB12, WEB22**, procédures d'adaptation/validation incomplètes ; **WEB14, WEB19, WEB24**, formulations trop absolues ; contrôler aussi les attendus de ces cas.
- Diagnostic demandé à Claude : regarder d'abord les sources et le diagnostic de sélection pour WEB15, distinguer lacune documentaire / mauvais classement / rédaction / réponse attendue discutable. Ne pas ajouter de réponse en dur et ne pas changer de modèle pour ce seul lot.
- Comparaison : référence précédente 35/37 sur le lot B/H, mais **ne pas comparer les pourcentages comme s'il s'agissait d'un même jeu**. Rejouer WEB01–WEB30 à corpus et paramètres constants après correctifs vérifiés.
- Décision de déploiement : aucune modification demandée ici ; selon le dernier journal, GPT-4.1 intégral est déjà activé pour les collègues, Mini restant un secours.

— GPT

## 22/11/2026 18 h 50 — Claude : relecture de trois questions réelles du journal d'exploitation (21 et 22/11, version ee49af0)
- **Vestiaires** : la fiche contenait bien le cas « à défaut de vestiaires séparés », mais la « Réponse directe » ne le reprenait pas, et le rédacteur ne s'appuie que sur ces lignes. Corrigé dans la fiche 030 (le texte prévoit la séparation ; à défaut, solution adaptée préservant l'intimité). Pas de réponse en dur.
- **Dossier certificatif, « répondre à un lycée qui a déposé un commentaire »** : lacune documentaire, pas défaut de rédaction. Les fiches 003 et 075 décrivent la soumission côté établissement ; rien ne décrit la lecture ou la réponse côté académie. Ajout d'une limite de rôle dans les deux fiches : ne pas présenter les étapes de soumission comme la réponse, dire que la procédure côté académie n'est pas documentée, orienter vers le correspondant. **La procédure côté commission/IPR reste à documenter par Thierry** (personne ne l'a transcrite).
- **Affichage** : les étiquettes « [FICHE PRIORITAIRE — statut …] » et « [DOCUMENT: chemin; statut …] » apparaissaient dans « Consulter les passages complets » ; elles sont retirées à l'affichage (texte métier intact). Test ajouté.
- Registre des empreintes : mis à jour pour les fiches 003 et 075 (statut « a_confirmer » conservé : la nouvelle limite n'est pas revue). Suite de tests : tout passe, sauf `test_openai_test_adapter.py::test_clients`, déjà en erreur avant (fonction d'aide collectée comme test).
- **Non rejoué** : pas de clé ni d'accès réseau ici. À rejouer par Thierry sur les 37 + WEB01–WEB30 avant de conclure ; ne rien annoncer comme gagné d'ici là.

— Claude

## 22/11/2026 19 h 30 — Claude : relevé de l'interface IA-IPR (SSS, APPN, Dossier Certificatif)
- Parcours avec Thierry dans l'interface « IA-IPR EPS / Conseillers techniques » (version 2026.2.1.1), comme la visite professeur du 18/10. J'ai lu les menus, les légendes et les fenêtres (masquées), sans ouvrir de dossier d'établissement ni cliquer sur Enregistrer, Valider, Signer ou Envoyer. Les listes étaient vides à l'ouverture, sans filtre.
- 4 fiches dans `data/ipack/visite_ipr_2026_11_22/`, statut `releve_ecran_ipr_2026-11-22_a_confirmer` :
  - plan des menus et dossiers attendus (dont sous-commissions) ;
  - Dossier Certificatif : statuts de validation d'un référentiel, réponse au commentaire d'un lycée (champ « Commentaires éventuels de la commission », face aux « Commentaires de l'équipe EPS »). Cela comble le trou noté le 22/11 à 18 h 50 ;
  - Dossier SSS : la coche [SSS] de [Établissements] > [Dossiers Attendus] conditionne la création des groupes SSS, et sa suppression vaut fermeture ; ouverture, projets, bilans, évolution ;
  - Dossier APPN : légende, avis, date de fin de validité.
- À confirmer sur un dossier réel : effet de [Envoyer Bilan] (certificatif), de [Débloquer] (SSS), bouton qui enregistre la décision APPN.
- Fiches 003 et 075 : la limite de rôle renvoie maintenant à la fiche côté inspection, au lieu de « non documenté ». Empreintes mises à jour.
- Motifs du catalogue : ils exigent que la question vienne de l'inspection (« je suis IPR », « côté inspection », « valider le dossier … d'un établissement », « répondre à un lycée »). Ils excluent « mon / notre dossier », « par l'inspection ». Test `tests/test_fiches_ipr_2026_11_22.py` : 7 questions d'inspection captées, 10 questions de professeurs non captées. Suite : 1 430 tests OK.
- Pas de réponse en dur, pas de consigne IA, pas de changement de modèle. **Non rejoué en ligne** : les rejeux 37 B/H et WEB01–WEB30 restent à faire.

— Claude

## 22/11/2026 19 h 20 — Claude : motifs IA-IPR fondés sur la situation, pas sur le rôle déclaré (remarque de Thierry)
- Un IPR ne dit pas « je suis IPR ». Les fiches côté inspection se déclenchent donc sur la situation :
  - répondre à un lycée, un collège, un prof, une équipe (toutes conjugaisons) ;
  - valider, refuser, débloquer ou relire le dossier, le référentiel ou la demande d'un établissement ;
  - demander des ajustements à un lycée ;
  - « un lycée m'a écrit » ;
  - référentiels à lire, avis de la commission à mettre.
- Le thème choisit la fiche : SSS, APPN, sinon Dossier Certificatif par défaut.
- Exclusions (côté prof) : mon / notre / nos dossier ou référentiel, mes élèves, « par l'inspection », « la commission a… », répondre à la commission.
- Test : 21 formulations d'inspection captées, 20 questions de professeurs non captées. 88 questions réelles des CSV du dépôt : aucune captée. Suite : 1 430 tests OK.

— Claude

## 26/11/2026 — Claude : relecture de 7 questions réelles (21–25/11, gpt-4.1)
- Version f56ecaa :
  - APSA non certificative : juste.
  - Lycée agricole : à nuancer, la réponse dit « dans l'académie de Normandie » alors que l'académie n'est pas précisée.
  - Redoublant de terminale : prudente, mais lacune documentaire.
  - Lycée pro « 2 meilleures notes » (Grenoble) : fausse en portée, la règle du BA 549 d'Aix est présentée comme générale.
- Version ee49af0 :
  - SSS : juste.
  - Vestiaires : partielle, déjà corrigée le 22/11.
  - Répondre à un lycée : fausse ; elle va maintenant à la fiche côté inspection (vérifié).
- Corrections (fiches seulement) :
  - CFA / lycée agricole (`complement_cyclades_cas_pratiques.txt`) : portée commune à toutes les académies ; les guides de Corse, Normandie et Besançon ne sont cités que comme sources, plus dans la marche à suivre.
  - CAP / meilleures notes (`examens/complement_reponses_validees.txt`) :
    - CAP 2 épreuves, bac pro 3 ;
    - le choix (meilleures notes ou épreuves retenues en début d'année) dépend des consignes de l'académie ;
    - ligne « Aix-Marseille uniquement » pour le BA 549 ;
    - solution logicielle (un groupe par combinaison, article 17 R4) quand l'académie le permet.
  - `portee_academique.json` régénéré.
  - Fiche iPackEPS lycée : la solution « meilleures notes » est conditionnée à la consigne EPS de l'académie.
  - Empreintes (registre, navigation_restore_pilot) mises à jour. Suite : 1 430 tests OK.
- Reste à faire : fiche « redoublant de terminale et note d'EPS », à écrire après lecture de la note de service du 25/08/2025 (NOR MENE2523745N) et de la page Eduscol « Redoublement et conservation des notes au bac GT ». La fiche « sans consigne écrite » affirme à tort qu'aucun texte national n'existe.
- Non rejoué : les deux questions (lycée agricole, lycée pro) arrivent par la recherche, pas par le catalogue. Il faut les reposer en ligne.

— Claude

## 26/11/2026 — Claude : fiche « redoublant de terminale et note d'EPS » (textes fournis par Thierry)
- Lus : la note de service du 25/08/2025 (NOR MENE2523745N, partie IV.A) et la page Éduscol « Redoublement et conservation des notes au bac GT » (février 2026).
- Nouvelle fiche `data/examens/textes_2026_11_26/bac_gt_redoublant_conservation_note_eps.txt` (bac GT uniquement) :
  - un candidat scolaire qui redouble la terminale ne conserve pas sa note d'EPS : il est réévalué en CCF. L'EPS relève du contrôle continu, et les notes de contrôle continu de terminale ne sont pas conservées ;
  - la conservation des notes ≥ 10 pendant 5 sessions ne vaut que pour les épreuves terminales du 1er groupe, dont l'EPS ne fait pas partie ;
  - la règle est une déduction des textes (aucune phrase spécifique à l'EPS) : c'est indiqué dans la fiche.
- Fiche « sans consigne écrite » : la ligne redoublant renvoie maintenant à la nouvelle fiche pour le bac GT ; pour le bac pro et le CAP, faire confirmer par le service des examens.
- Tutoriel Cyclades de Créteil (R3, dispense automatique d'EPS) : ajout d'un avertissement, ce comportement ne vaut pas règle pour un redoublant scolaire du bac GT (texte prioritaire).
- Catalogue : motifs redoublement / échec + EPS, CCF, note ; exclusion du redoublement en seconde, en première, au collège, en BTS. Suite : 1 430 tests OK.
- À reposer en ligne : la question réelle du 23/11.

— Claude
