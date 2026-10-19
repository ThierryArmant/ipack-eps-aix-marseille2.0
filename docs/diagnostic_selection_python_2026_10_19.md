# Diagnostic de la sélection Python avant rédaction — 19 octobre 2026

Version contrôlée : `0a57234`. Analyse demandée après observation de réponses hors sujet. Aucun moteur, catalogue, fiche ni consigne modifié. Aucun appel IA payant.

## Conclusion

Plusieurs défauts de préparation sont reproduits avant toute génération. Le code ne manque pas seulement d'informations : il peut trouver la bonne fiche puis la retirer, ou garder une fiche voisine sur un recoupement lexical insuffisant. La génération reste une autre cause possible ; l'analyse n'attribue pas toutes les erreurs à Python.

## Méthode et limites

Six cas déjà observés ont été retracés avec le code réel de `_recherche_documentaire`, extrait de `app.py` par AST via le banc existant `tests/test_documentation.py`. Le chargeur, le catalogue, la recherche complémentaire par mots et les filtres de `review_exam_answer` sont réels. Les retrievers vectoriels distants sont remplacés par des résultats vides ; les sorties du modèle sont simulées vides pour capturer le prompt. Il ne s'agit pas d'un rejeu des réponses ni de la reconstruction exacte des prompts de production.

Pour le cas des lots bac pro/CAP, la source hors sujet effectivement citée en production est injectée séparément comme résultat vectoriel contrôlé, avec le contenu et les métadonnées du chargeur réel. Cela établit que le filtre l'admet, pas son classement historique exact par le moteur vectoriel.

Les questions, réponses et traces individuelles restent privées. Les sujets ci-dessous décrivent les mécanismes, sans reproduire les questions du corpus de mesure.

## 1. Une bonne fiche est retrouvée puis écartée : changement d'établissement

Le catalogue sélectionne simultanément :

- `data/ipack/visite_college_2026_10_18/equipe_eps_actualiser_tzr.txt` : priorité 300, gestion de l'équipe et du remplacement ;
- `data/ipack/fiches/ipack_222_situation_enseignants_tzr_ou_partages_multi_etablissements.txt` : priorité 280, sélecteur permettant de changer d'établissement.

`review_exam_answer` considère les documents de priorité au moins 300 comme focalisation principale. La fiche 222 ne survit que si son TITRE partage au moins deux racines avec la question. Sur le cas contrôlé, elle n'en partage aucune selon cette fonction, malgré son déclencheur explicite dans le catalogue. Elle est retirée ; la fiche d'équipe reste seule.

La présence de « TZR » avec « iPackEPS » suffit au motif de la fiche d'équipe, sans demande de gestion du personnel. Deux défauts se combinent : déclencheur trop large et suppression d'une fiche ciblée reconnue par le catalogue. Modifier uniquement la rédaction ne rendra pas à l'IA la fiche retirée.

## 2. Une formule de demande remplace l'objet métier : protocole et handicap

`data/ipack/situations_2026_10_17/ordre_premiere_connexion_fiche_professeur.txt` est sélectionnée en priorité 300 par la seule formule « par quoi commencer », sans exiger une première connexion ni une difficulté d'accès.

La recherche par mots retrouve notamment `ipack_212_situation_interdiction_d_improviser_un_controle_adapte_fca_a_la_volee.txt` et des passages de protocoles adaptés. La focalisation sur la fiche de première connexion les retire. La sélection finale ne traite plus le handicap ni le protocole adapté. Le mode voie professionnelle/CAP ne permet par ailleurs pas de choisir le diplôme précis à la place de l'utilisateur.

## 3. Les consignes de présentation contaminent le filtre de complémentarité

La fiche ciblée `data/examens/audit_faq_2026_10_12/h5_procedure_verifiee.txt` est correctement retrouvée sur le problème d'accès aux lots bac pro/CAP.

Dans l'expérience d'admission vectorielle contrôlée, `data/examens/cap_unites_facultatives.txt`, pourtant hors sujet, est conservée comme complément. Les deux racines communes au titre sont :

- `disti` : le verbe demandant de distinguer les natures de sources rejoint le mot « distinction » du titre ;
- `profe` : la table de synonymes ramène « enseigne » à cette racine, également produite par la troncature de « professionnel ».

En retirant seulement la consigne de présentation, il ne reste qu'une racine commune : le critère des deux racines n'est plus satisfait. Le filtre compte donc ici une instruction sur la forme comme un indice de sujet et accepte une collision de racines comme une complémentarité métier. La priorité vectorielle n'est pas transmise par `_ajouter` : elle vaut zéro à cette étape, mais le filtre de complémentarité la réintroduit quand même.

## 4. Filtrage du diplôme insuffisant à l'échelle des passages

Sur le cas DNB, les fiches DNB sont présentes, mais deux passages de `data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt` concernant le circuit CCF de lycée restent aussi transmis par le parcours local.

`dnb_document_mismatch` utilise notamment le chemin, le titre, les marqueurs `[PORTEE: ...]` et une combinaison nom de logiciel dans chemin/titre + termes d'examen dans le corps. Les passages concernés ont le titre générique « Passage documentaire » ; le nom du fichier ne contient ni Santorin ni Cyclades, et leur balisage de diplôme ne suffit pas à les exclure. Le contenu métier incompatible survit donc.

Il faut qualifier le passage réellement envoyé, pas seulement le nom du fichier ou la première ligne encore disponible après découpage. Cela explique comment une réponse peut citer correctement le LSU puis ajouter une procédure de saisie CCF lycée ; cela ne prouve pas que toute génération reproduira cette contradiction.

## 5. Quantité de notes : la bonne situation n'est pas reconnue explicitement

Sur le cas GT de deux activités non évaluées et d'une seule note, aucune fiche prioritaire du catalogue ne se déclenche sur la formulation contrôlée. Le parcours local conserve des passages de note nationale et une fiche de gestion de deux notes sur trois, retrouvés par mots. Le titre de plusieurs fragments devient « Passage documentaire ».

Le moteur ne représente pas ici explicitement le triplet nombre d'épreuves évaluées / inaptitude / nombre de notes. La présence d'une source nationale ne suffit pas à empêcher la sélection d'une procédure voisine. L'absence de la recherche vectorielle dans ce diagnostic interdit d'affirmer que la bonne source était absente de la production ; le défaut de raccordement explicite est en revanche reproduit.

## 6. Sans source précise, les voisins lexicaux passent encore

Sur la conservation des données, aucune fiche prioritaire ne se déclenche. La recherche par mots propose notamment une fiche sur le temps minimum d'enseignement et une sur l'emploi du temps. En l'absence de focalisation, `review_exam_answer` conserve tous les passages compatibles avec les filtres existants. Le filtrage ne vérifie donc pas suffisamment l'identité de l'objet recherché. La génération peut alors produire un repli assorti d'extraits hors sujet, comme dans l'export reçu.

## Volume de contexte : une seconde fondation à examiner

Les principales de priorité au moins 300 ne sont pas soumises au budget de 4 500 caractères par complément / 6 000 au total / deux compléments. Ce budget n'est pas un plafond général du prompt.

Sur la trace locale du changement d'établissement, le prompt fait environ 24 557 caractères ; environ 20 354 précèdent le bloc de données, dont 9 440 caractères de consignes institutionnelles. Ces chiffres sont des caractères, pas des tokens mesurés, et n'incluent pas les résultats vectoriels distants. Ils montrent que supprimer des fiches ne suffit pas à expliquer ni à traiter tout le coût : le socle d'instructions et le schéma pèsent aussi.

## Pourquoi les tests existants passent

Les questions types vérifient surtout la présence d'un titre attendu et quelques titres interdits. Elles ne démontrent pas que le passage pertinent atteint le prompt final, ni qu'aucun complément ne traite une autre situation. `priority_context` et `_recherche_documentaire` ne sont pas une unique implémentation : le premier ne rejoue pas tous les apports ni tous les choix d'exclusivité du second. Des tests peuvent donc valider une sélection intermédiaire alors qu'un filtre ultérieur retire la bonne fiche.

## Ordre de travail proposé

1. Corriger les déclencheurs génériques en exigeant objet et action ; distinguer gestion du personnel, bascule d'établissement et démarrage d'un protocole.
2. Faire survivre la bonne fiche reconnue par un déclencheur ciblé ; ne pas employer la priorité numérique comme preuve d'applicabilité.
3. Séparer intention métier et consignes de présentation dans le recoupement ; tester les collisions lexicales et les compléments interdits.
4. Préserver identité, titre, diplôme et situation à l'échelle du passage, y compris pour les résultats par mots et vecteurs.
5. Tester le contenu du prompt réellement envoyé après tous les filtres, avec bons et mauvais documents concurrents.
6. Mesurer ensuite la longueur des instructions et des passages ; alléger avec preuves de non-régression, puis quelques reprises réelles seulement.

Aucune correction fonctionnelle appliquée par ce diagnostic. Aucun gain de fiabilité ou de tokens annoncé.


## Suite : corrections de sélection du 19 octobre

Le diagnostic ci-dessus décrit la version antérieure. Les corrections suivantes sont appliquées ensuite :

- La provenance de sélection (`catalogue`) et les diplômes sont conservés dans l'identité du passage. Une fiche explicitement ciblée à partir de la priorité 200 peut focaliser le contexte en l'absence de priorité 300 ; avec une priorité 300, elle reste admissible comme complément sous les budgets existants. La fiche multi-établissements reste à 280. Un résultat vectoriel ne peut pas revendiquer cette provenance par sa seule priorité.
- Le filtre de complémentarité distingue le sujet des demandes finales de présentation des sources. Son recoupement lexical n'utilise plus les synonymes destinés à vérifier les preuves.
- Le titre réel du fragment est conservé après découpage et après recherche par mots. Les portées déclarées des résultats vectoriels arrivent jusqu'au filtre DNB ; le corps est également contrôlé pour les procédures lycée, en préservant les explications explicites du circuit DNB/LSU.
- Une procédure portant explicitement sur un nombre unique de notes incompatible avec celui demandé est écartée. Un passage présentant plusieurs possibilités reste admissible.
- Trois entrées du catalogue sont corrigées avec l'accord de la partie fiches : démarrage conditionné au contexte logiciel et exclusions adaptées ; équipe EPS distinguée du changement d'établissement ; déclenchement explicite de la fiche 212 sur l'adaptation, sans déclenchement par la seule inaptitude. Le statut documentaire de cette fiche est conservé.

Les nouveaux tests contrôlent aussi la sélection finale avant génération, et pas uniquement les titres du catalogue. Ils utilisent des sondes publiques distinctes du corpus privé, un modèle simulé et des retrievers contrôlés.

### Points encore ouverts

Le parcours sans fiche prioritaire conserve encore des voisins lexicaux non pertinents dans certains cas. Le parcours DNB peut encore présenter des documents mixtes ou des tutoriels insuffisamment qualifiés : le filtrage renforcé ne constitue pas un inventaire complet de leurs portées. Le volume fixe des consignes, les doublons de fragments et le budget global du contexte restent à examiner. Aucun gain de qualité ni de coût en production n'est déduit de ces tests locaux. Le rejeu comparatif des réponses reste nécessaire après publication et identification de la version déployée.
