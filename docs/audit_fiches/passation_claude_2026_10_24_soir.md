# Passation GPT / Claude - 24 octobre 2026, soir

Cette note accompagne `docs/journal_coordination.md`. Base relue avant rédaction : **4874042**. Elle décrit les résultats observés et les problèmes encore ouverts ; elle ne certifie pas la fiabilité globale du Hub. Thierry demande une recherche commune de solution. Aucun nouveau rejeu IA n'a été lancé pour cette passation.

## 1. État de production à ne pas confondre avec l'expérience administrateur

- Dernière modification du programme : **7be4e5b**. **4874042** ajoute seulement une entrée au journal et une sélection de témoins ; il ne change pas le comportement testé.
- En administration, les cases « Mode fidèle : textes sources, sans rédaction IA » et « Essai direct : Albert seul, sans Mini » sont cochées par défaut dans l'expérience actuelle.
- Recherche documentaire par le code, puis **un appel Albert gpt-oss-120b** sélectionnant identifiants de documents et de passages. Le code restitue les passages entiers ; les sources retenues complètes restent consultables dessous.
- Aucun appel GPT/Mini de sélection ou rédaction dans les deux derniers exports. Aucun secours GPT, aucune rédaction libre ni réparation dans ces essais. Cela ne signifie pas que la recherche vectorielle est sans embeddings OpenAI ; cette recherche reste hors compteurs affichés.
- **Le parcours public non administrateur n'a pas été basculé en bloc dans ce mode.** Décocher les essais administrateur restaure le routage ordinaire. Une étiquette de modèle GPT configuré ne prouve pas son appel : lire `calls`, `provider`, `resolved_model` et `usage_response`.
- `albert_adapter.py` garde **ALBERT_PAUSED = True** pour les clients ordinaires. Les instances d'essai autorisées utilisent **allow_paused_test=True**, transmis jusqu'à `_request`. Ni réactivation globale, ni changement temporaire d'un verrou partagé entre sessions.
- `generation_runtime.py` charge des modules immuables selon leur empreinte ; modifier un fichier sans l'intégrer correctement au runtime peut faire tester une ancienne version. `exact_source_answer` fait partie du runtime.

## 2. Arrivée d'Albert et architectures réellement essayées

| Version / étape | Fonctionnement et constat |
|---|---|
| Essais Mini antérieurs | Mini a lui aussi confondu déplacement individuel et réaffectation d'un lot, fabriqué des intitulés de boutons et perdu des conditions. Il n'est pas établi qu'il sélectionne mieux qu'Albert. |
| Comparateurs E puis F | E ajoute l'isolation des opérations inspirée de Gemini, sans appeler Gemini. Les erreurs persistent. F ajoute un classement documentaire par le même modèle ; les plans incomplets ou sans exclusion n'établissent pas de réduction utile. Ne pas relancer ces variantes en série. |
| **1613605**, G | Mini choisit les sources, le code les restitue sans rédaction. Résultat réel : D3/D6, sans menu inventé, mais textes trop larges. |
| **cafbe22**, H | Albert rédige sur les sources choisies dans G, sans nouveau Mini ni recherche. Premier essai bloqué localement par la pause Albert : pas de réponse fournisseur. |
| **7687d8f** | Passage du droit d'essai jusqu'à `_request`, correction du vrai verrou. Essai H réel ensuite : un appel Albert, 3 576 jetons ; Albert invente encore des boutons de réaffectation non décrits. |
| **a14ef16**, direct Albert | Code de recherche → Albert seul, sans Mini. Trace réelle : 8 748 jetons ; ajout d'un second évaluateur transposé en remplacement. Le choix du modèle seul ne résout donc pas le problème. |
| **d459892**, mode fidèle | Albert choisit des sources entières ; plus de rédaction métier. Essai utilisateur : un appel, 5 222 jetons ; D3/D6 recopiés fidèlement mais trop de procédures voisines affichées. |
| **38cb472**, passages en tête | Le même appel choisit aussi des identifiants de passages ; texte exact, pas de seconde rédaction. Essai direct effectué par GPT avec autorisation : un appel Albert, 5 404 jetons, 2,896 s, D3P3/D6P4 ; bonne orientation, chef et mission Imag'in conservés, aucun chemin individuel inventé. Un cas ne prouve pas la régularité. |
| **7be4e5b**, médias | Une vidéo du passage non retenu D3P2 remontait depuis le HTML des sources repliées. Noms de fichiers et URL déclenchant les lecteurs désormais cherchés dans les passages en tête en mode `exact-focus-v1`. Le texte de l'annexe reste intact. |

Thierry indique disposer d'un forfait Albert gratuit limité à environ un million de jetons et 160 requêtes par jour. Cette indication utilisateur n'est pas une mesure du quota disponible. Ne pas confondre pause locale, erreur quota fournisseur, accès au site DINUM et disponibilité de l'API. Les dernières traces montrent bien des réponses de `gpt-oss-120b` via le fournisseur Albert.

## 3. Deux exports à quatre questions : ne pas les comparer par les seuls numéros

GPT a donné les numéros 3, 9, 15, 18 sans préciser suffisamment la banque. Thierry a d'abord sélectionné ces lignes dans une autre base de 100 questions. GPT a reconnu cette confusion.

- **`retest_113_reponses_privees (5)(6).csv`** : quatre AUTRES questions (association manuelle Cyclades ; dépôt du document des cas particuliers ; distribution manuelle ; substitution pour inaptitude temporaire). **17 351 jetons, quatre appels Albert.** Ce lot ne mesure pas l'évolution des quatre témoins du matin. Ses réponses restent analysables séparément.
- **`retest_base a modifier_compatible_hub.csv`** : base de 100 questions expliquant le premier choix. Ses lignes 3/9/15/18 correspondent à cet export précédent, pas aux vingt témoins.
- **`retest_113_reponses_privees (6)(3).csv`** : les QUATRE BONS témoins du matin, formulations/publics/contextes concordants. Version **4874042** ; mode fidèle et Albert seul confirmés pour chacun. **23 354 jetons, quatre appels de sélection, zéro rédaction, zéro réparation.** Q18 : Amiens ; les trois autres académies restent non précisées.

Les CSV privés sont conservés dans l'espace de travail et fournis à Thierry, pas publiés dans le dépôt. Aucune question complète ni réponse privée n'est reproduite ici. Pour les futurs lots, vérifier le contenu et le contexte en plus du numéro ; conserver une empreinte de la question et du contexte. Les identifiants Dn/Pn sont locaux au contexte d'un essai, pas des identifiants permanents de fiche.

### Les quatre bonnes traces

| Témoin | Choix réel d'Albert | Affichage réel et défaut | Usage |
|---|---|---|---:|
| **Q3 - groupe Cyclades erroné** | principal D1, aucun complément ; D1P2/P4/P6 | Champ grisé et branche déjà validée. Omission de P3 (tout le groupe faux, non validé) et P5 (quelques élèves seulement). Les trois branches étaient disponibles. Le code accepte et recopie une sélection incomplète. | 6 461 jetons ; 3,066 s |
| **Q9 - ouverture SSS** | principal D1, complément D4 ; D1P5/P10 + D4P3 | Chemin, prérequis et campagne conservés. D1P10 mêle modification d'un dossier signé et attendu d'ouverture ; opération parasite recopiée. | 5 883 jetons ; 4,460 s |
| **Q15 - annexes SSS** | principal D1, complément **D1** ; D1P7/P9 | Bonne réserve sur le dépôt sélectionnée, mais répétition du principal dans les compléments. Le code rejette tout : `invalid_selection_no_retry`, ValueError. Message « sélection non exploitable », puis tutoriel de reconduction ajouté par la mise en forme. | 5 365 jetons ; 4,294 s |
| **Q18 - contact DEC, Amiens** | principal D3, complément D7 ; D3P2/D7P2 | Diagnostics d'erreur et d'élève absent choisis. DEC citée mais réponse décentrée ; limite sur les coordonnées non retenue, malgré la fiche contact disponible. Pas de renvoi erroné vers le mail iPackEPS d'Aix dans cet essai. | 5 645 jetons ; 4,061 s |

Les quatre sources pertinentes ont été retrouvées ; les premiers défauts observés sont donc ici après la recherche. Cela ne prouve pas que toute recherche est correcte sur les autres questions. Les principales erreurs du matin ne réapparaissent pas à l'identique, mais les quatre réponses ne sont pas validées globalement. Pas de pourcentage de réussite tiré de cette petite sélection volontairement difficile.

## 4. Localisation reproductible et travail encore NON appliqué

### A. Rejet du doublon : code trop strict pour cette sortie (Q15)

- Module : `exact_source_answer.py`, fonction `exact_answer`, validation de `complements`, notamment `main in extra` et contrôle des doublons.
- Sortie réelle : `principal=D1`, `complements=[D1]`, passages D1P7/D1P9 existants et cohérents avec D1. Aucun identifiant inventé dans ce cas.
- Simulation hors réseau effectuée avec `context_exact`, mêmes passages et même sélection, en retirant seulement le complément D1 répété : **`rendered_exact_sources`**, réserve de dépôt affichable. Ni appel Albert, ni modification de production.
- Correctif à envisager : normalisation déterministe des répétitions inoffensives avec trace avant/après, sans accepter identifiants inconnus, mauvais types ou passages hors sources sélectionnées. Mettre à jour les tests qui attendent aujourd'hui le rejet d'un doublon. Ne pas présenter ce correctif comme déjà publié.

### B. Mélange FAQ / attendu : mécanisme isolé (Q9)

- Source : `data/ipack/fiches/ipack_080_article_28_dossiers_dossier_sss_ouverture_demande_d_ouverture_de_section_sportive_scolaire.txt`.
- Module : `documentary_review.py`, pipeline `source_packets` → segments de portée → `bind_faq_context` → `bind_list_items` → numérotation.
- D1P10 de la trace contient Q4/R4 sur le dossier signé ET le paragraphe autonome `Action : ... Objet ... Attendu final ...` d'ouverture.
- Reproduction sur le **contexte réel** : mélange présent avec le runtime courant ; absent si `bind_faq_context` est remplacé localement par l'identité ; encore présent si seul `bind_list_items` est neutralisé. Ce test local s'arrête à la production de passages, sans fournisseur et sans changement de fichier de production.
- Une première reproduction synthétique générique n'avait pas reproduit ce mélange, car les segments de portée et la structure ne correspondaient pas au contexte réel. Ne pas la citer comme test réussi. Le chemin réel a ensuite isolé le mécanisme.
- Le commentaire de `bind_faq_context` veut conserver les sous-puces de la réponse avec sa question. Sa boucle ne s'arrête pas ici avant l'unité autonome `Action :`. **Ne pas supprimer globalement la fusion FAQ** : elle protège aussi les conditions attachées à une réponse. Étudier une frontière structurelle et vérifier les vraies questions/réponses, listes, portées et négations.
- Le moule ajouté en fin de fiche n'est donc pas seulement mal interprété : il peut être rattaché par le code à la dernière réponse FAQ. Examiner les autres fiches avec ce schéma avant d'en créer davantage.

### C. Branches omises (Q3)

- Source : `data/examens/audit_faq_2026_10_12/f4_procedure_verifiee.txt`, avec sa copie dans `data/examens/complement_cyclades_protocoles_cas_enseignant.txt`.
- Albert reçoit les trois branches, choisit seulement P4. Le code valide existence/appartenance des passages, pas complétude de la décision.
- Piste : unités regroupant des branches d'une même décision lorsque leurs conditions doivent être distinguées, sans fusionner toutes les opérations d'une page. L'unité de décision et la procédure voisine ne sont pas la même chose. Ne pas forcer la branche « validé » ni demander systématiquement une clarification.
- La phrase générale « rien dans le texte national... » est présente dans la source et recopiée. Sa présence ne vaut pas preuve de l'absence de règle nationale ; cette formulation déjà signalée mérite une revue de provenance bornée, distincte du défaut de sélection.

### D. Intention de contact remplacée par diagnostic (Q18)

- Source utile disponible : `data/ipack/qui_contacter_assistance_ipackeps.txt` (dans cet essai D1, avec d'autres copies candidates). Interlocuteur examens et absence de coordonnées de chaque DEC y sont explicités.
- Sources retenues : `data/examens/erreurs_cyclades_santorin.txt` et `data/examens/tutoriels_creteil_cyclades_santorin.txt`.
- La présence du vocabulaire élève/Santorin attire la sélection vers le traitement d'un incident, alors que le besoin est l'interlocuteur. Une réécriture correcte de la fiche contact ne suffit pas si elle n'est plus retenue.
- Piste : préserver le type de demande (interlocuteur, manipulation, diagnostic, vue d'ensemble) dans le choix des unités. Une comparaison Mini/Albert ne serait interprétable qu'avec le même contexte documentaire ; elle n'est pas autorisée automatiquement par cette note.

### E. Effets de bord encore visibles

- `media_text` évite la promotion des vidéos des annexes non retenues en rendu exact-focus-v1. Il ne couvre pas tous les ajouts thématiques de `app.py` : Q15 reçoit encore un tutoriel SSS après un échec de sélection, qui n'a pas produit de rendu exact-focus-v1.
- Dans le premier lot de quatre, un passage « dans le second cas » a été affiché avant celui qui définit les deux cas : conserver aussi les dépendances et l'ordre des passages, pas seulement leur présence. Ce défaut appartient à l'autre lot, pas aux quatre témoins du matin.
- Les titres, mots-clés et attestations d'« attendu » ne doivent pas être présentés comme de nouvelles preuves métier. Les cartes remises à Thierry ont été corrigées à sa demande : chemin réel seulement, pas de future solution verte au bout d'un échec rouge.

## 5. Proposition de coordination pour la reprise à deux

Répartition proposée, à confirmer par une entrée au journal avant travaux concurrents, sans prétendre que Claude l'a déjà acceptée :

- **Claude :** examiner les unités documentaires, la frontière FAQ/paragraphes autonomes et les copies SSS. Étendre le diagnostic aux fiches de la même structure ; préserver le contenu correct et ses portées. Un changement global de découpage doit protéger les conditions Q/R et les cas utiles.
- **GPT :** traiter la normalisation des identifiants en mode fidèle et les effets de bord d'affichage, puis vérifier sur les sorties sauvegardées. Examiner ensuite la sélection de branches et l'intention de contact, en coordination avec les changements d'unités.
- Ne pas modifier simultanément `documentary_review.py`, `exact_source_answer.py`, `app.py` ou le journal sans relire le HEAD et les modifications de l'autre. Publier des lots bornés avec parent attendu ; pas d'écrasement du travail local.
- D'abord reproductions hors réseau et tests ciblés de non-régression ; ensuite seulement le même petit lot réel si Thierry autorise sa relance. Aucun rejeu massif ni nouveau changement de modèle pour masquer le défaut.
- Distinguer les garanties : identifiant existant, texte fidèlement copié, sélection pertinente, conditions complètes, source elle-même exacte. Les deux premières sont contrôlables mécaniquement, les autres ne sont pas garanties ici.

## 6. Validation, limites et continuité

- Dernière suite du code publié : **47 tests ciblés** sur 7be4e5b (détail dans le journal). Aucun nouveau total de tests n'est revendiqué pour cette passation documentaire.
- Deux reproductions supplémentaires hors IA analysées : déduplication simulée Q15 et isolation de `bind_faq_context` sur Q9. Pas de nouveau test fournisseur, pas de correctif de ces deux défauts publié à cette étape.
- Dernier bilan des vingt publié : e617374, 14 utiles / 3 partielles / 2 insuffisantes / 1 guide non observable ; douze utiles initiales préservées. Ce bilan est historique et non un score du nouveau mode fidèle.
- Les 188 essais analysés auparavant, les comparaisons de lots et les corrections existantes restent dans le journal et `docs/audit_fiches/`. Ne pas repartir de zéro ni réécrire une fiche correcte pour compenser un contrôle ou une mauvaise sélection.
- Les vidéos de visite existent dans l'historique ; l'audio de la quatrième, responsable SAV Examens Aix-Marseille, **n'a pas été transcrit par GPT**. Les éléments écrits du SAV déjà au corpus ne prouvent pas une exploitation audio.
- Les anciens répertoires de travail sont préservés. Le chemin initial `/workspace/scratch/01712bb79dbb/hub-visit-audit` n'est plus disponible dans cet environnement ; aucune récupération récente n'est revendiquée. Copies locales de travail publiées : `hub-faithful-media`, traces récentes sous `upload/`.
- Les cartes PDF privées sont des aides à la lecture des traces, pas un résultat produit par le Hub ni une amélioration du programme. Elles ne sont pas publiées avec les CSV dans ce dépôt.

**Statut de cette publication : coordination/documentation uniquement. Aucun nouveau correctif de code, aucune nouvelle fiche métier, aucun appel IA distant.**
