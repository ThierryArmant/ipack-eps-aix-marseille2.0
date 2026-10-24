# Question témoin : réaffecter un lot à un autre examinateur

Pour Claude, à la demande de Thierry. Complément à `passation_claude_2026_10_24_soir.md` ; base GitHub relue : **08d9159**. Cette publication rassemble le diagnostic historique de la question longtemps répétée. Elle ne modifie pas le programme et ne relance aucun modèle.

## Question et distinction à préserver

Question de référence : **Comment réaffecter un lot à un autre examinateur ?** Contexte : Examens, lycée voie générale. Des variantes originales collées et une majuscule initiale apparaissent dans les traces conservées. Vérifier l'académie et le contexte exact de chaque fichier avant comparaison.

Trois objets ne doivent pas être confondus :

1. Réaffecter le lot entier : changer son examinateur.
2. Déplacer un candidat : changer le lot de cet élève.
3. Ajouter un deuxième évaluateur : donner accès au même lot, sans que le passage établisse le remplacement du premier.

La clôture du lot constitue encore une autre opération. Sa condition de notes complètes ne peut pas devenir une condition de réaffectation.

## Sources du corpus à examiner ensemble

- `data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt`, section « tout un lot est attribué au mauvais enseignant » : source directement centrée sur la question. Dans plusieurs contextes enregistrés, c'est D6. Elle cite le chef d'établissement, le suivi des lots Santorin, le changement d'enseignant du protocole dans Cyclades et la mission EPS dans Imag'in. **Elle ne détaille pas les boutons Santorin de réaffectation.** Ne pas inventer leur intitulé pour rendre la réponse plus concrète, ni affirmer une propagation automatique entre les outils sans preuve.
- `data/examens/circuit_aix_ipack_cyclades_santorin.txt`, section portail établissement : mélange distribution manuelle, réaffectation et clôture. Dans plusieurs contextes, D3. Les passages de réaffectation et de clôture ont été explicitement distingués ; la source entière reste plus large que la demande.
- `data/ipack/fiches/ipack_106_8_suivi_de_l_avancement_par_l_etablissement.txt` : suivi, réaffectation, clôture et harmonisation dans une fiche.
- `data/examens/complement_reponses_validees.txt` et sections voisines du premier fichier : droits et chemin du **déplacement individuel**. Le menu `[Distribution] > [Lots] > [Candidats] > [Déplacer vers un lot existant]` ne décrit pas le changement d'examinateur de tout un lot.
- `data/examens/videos_tutoriels_cyclades_santorin.txt`, section ajout d'un deuxième évaluateur : les deux enseignants accèdent alors au lot. Le chemin détaillé de cette opération ne prouve pas une procédure de remplacement.

Les Dn/Pn sont locaux à un contexte : chercher aussi la source, le titre et le texte, pas uniquement « D6 » dans un autre essai.

## Traces complètes réunies pour transmission privée

Une archive `traces_reaffectation_lot_pour_claude.zip` a été remise à Thierry : **12 JSON**, un fichier de lecture et un manifeste des fichiers avec leurs empreintes SHA-256. Onze exports JSON originaux sont copiés sans modification ; le douzième est le seul cas concerné extrait du lot de dix, sans ses autres questions. Le contenu brut des prompts, réponses et traces privées n'est pas publié dans ce dépôt.

Les numéros suivants sont les noms de classement de l'archive, pas une certification d'ordre chronologique entre toutes les branches.

| Fichier de l'archive | Version | Expérience et point d'analyse |
|---|---|---|
| `01_mini_minuscules_caccd47.json` | caccd47 | Mini, question collée avec minuscule. Sélection puis rédaction, 2 appels / 9 008 jetons. Examiner le chemin de déplacement individuel attribué à la réaffectation. |
| `02_mini_majuscule_caccd47.json` | caccd47 | Mini, variante avec majuscule. 2 appels / 8 913 jetons. Les contextes transmis diffèrent : ne pas conclure que la majuscule cause la variation, ni invoquer le cache sans preuve. |
| `03_mini_actions_objets_277bed2.json` | 277bed2 | Cas extrait du lot de dix après ajout action/objet/attendu. 2 appels / 9 033 jetons. Bonne source conservée, mais intitulés Santorin de réaffectation ajoutés sans preuve. |
| `04_comparatif_E_a5de07d.json` | a5de07d | A : 17 968 jetons ; E : 8 858. E ajoute l'isolation des opérations inspirée de Gemini, sans appeler Gemini. Mauvais chemin et droits encore transposés. |
| `05_comparatif_F_cc0cba9.json` | cc0cba9 | A : 8 595 jetons ; F : 25 933. Plan F incomplet rejeté, puis rédaction/réparation sur le contexte initial : ce résultat n'évalue pas une réduction réellement appliquée. |
| `06_comparatif_F_bfbd3e9.json` | bfbd3e9 | A : 17 640 jetons ; F : 7 646. Plan partiel accepté mais pas d'exclusion utile ; F s'arrête sans rédaction. Ne pas présenter l'arrêt comme une bonne réponse métier. |
| `07_selection_G_1613605.json` | 1613605 | Mini choisit les sources, code seul pour leur restitution. G : 1 appel / 5 232 jetons ; A non recalculé. D3/D6, textes fidèles mais trop larges. |
| `08_essai_H_bloque_70b1ff2.json` | 70b1ff2 | G embarqué comme historique ; nouvel H bloqué par la pause locale. Usage fournisseur absent, durée nulle. Ce fichier n'est pas une réponse Albert incorrecte. |
| `09_Albert_sur_G_7687d8f.json` | 7687d8f | G historique, puis un nouvel appel Albert H : 3 576 jetons. Deux sources seulement, mais boutons de réaffectation inventés. Le second modèle ne suffit pas à sécuriser la rédaction. |
| `10_Albert_direct_a14ef16.json` | a14ef16 | Code de recherche → Albert seul rédacteur : 1 appel / 8 748 jetons. Procédure d'ajout d'un second évaluateur transposée en remplacement, droits élargis et propagation non prouvée. |
| `11_Albert_sources_entieres_d459892.json` | d459892 | Albert sélectionne, code recopie les sources entières : 1 appel / 5 222 jetons. Pas d'invention rédactionnelle, mais distribution/clôture et autres informations encombrent la réponse. |
| `12_Albert_passages_cibles_38cb472.json` | 38cb472 | Albert choisit D3P3/D6P4, code les restitue : 1 appel / 5 404 jetons, 556 caractères en tête. Bonne action, chef et mission Imag'in conservés ; réponses partiellement redondantes. Pas de menu individuel inventé. |

**Ne pas additionner les compteurs G réembarqués dans H comme de nouveaux appels.** Lire `historical_result`, `new_usage`, `calls` et les branches séparément. Aucun total global de coût n'est fabriqué pour cette archive.

## Les secteurs d'erreur observés

### 1. Bonne source disponible, opérations voisines encore fournies

Un contexte analysé contient dix documents et 51 passages, soit 10 898 caractères de texte de passages. Les sept documents principalement voisins représentent 7 977 caractères ; cela ne signifie pas que chacun de leurs détails est inutile. La fiche directement pertinente n'était donc pas absente, mais noyée parmi des opérations proches.

### 2. Mauvais rattachement ou ajout lors de la rédaction

Mini et Albert ont tous deux repris une opération voisine pour répondre à la question du lot entier. Une citation peut exister et les mots de menu être présents dans le corpus sans que **leur emploi pour cette action** soit justifié. Les contrôles lexicaux/citationnels ont laissé passer ces confusions.

### 3. Le moule action / objet / attendu ne suffit pas

L'ajout documentaire conserve mieux l'objectif, mais un essai Mini invente encore un menu. La fiche correcte ne garantit pas la bonne sélection ni la bonne reformulation. Le défaut FAQ / paragraphe autonome corrigé depuis par Claude porte sur une autre structure : ses effets sur les anciennes traces ne doivent pas être présumés sans reprise hors réseau.

### 4. Sélection exacte, puis absence de rédaction libre

La restitution exacte supprime les inventions faites à la rédaction, pas les erreurs de contenu de la source ni les erreurs de sélection. Le résultat intégral d459892 reste peu lisible ; 38cb472 affiche les passages plus ciblés, avec les textes complets consultables. C'est un progrès observé sur ce cas, pas une mesure générale ni une preuve de régularité.

### 5. Effet de bord après sélection

Dans le dernier essai, une vidéo de distribution située dans le passage non retenu D3P2 est tout de même ajoutée sous la réponse, car le code explore aussi les annexes repliées. Correction ultérieure **7be4e5b** : en mode exact-focus-v1, seuls les passages retenus en tête déclenchent ces lecteurs automatiques. Cette correction n'est pas rejouée dans la trace historique 38cb472. Les ajouts thématiques SSS, observés dans un autre lot, restent un problème distinct.

## Ce que Claude peut reprendre sans consommation IA

1. Ouvrir d'abord la trace 12, puis comparer 11, 10 et les deux traces Mini 01/02.
2. Pour chaque réponse, relier l'action annoncée, l'acteur, la condition et le chemin à leurs passages exacts. Repérer la première étape où l'opération change.
3. Comparer les contextes par empreinte et contenu avant d'attribuer un effet à une majuscule, une faute, la longueur ou un modèle.
4. Distinguer preuve retrouvée, choix pertinent, texte fidèle et aide réellement apportée. Ne pas inventer les boutons Santorin absents pour satisfaire une attente de procédure exhaustive.
5. Vérifier une proposition de correction sur les anciennes sorties et les contre-exemples : déplacement individuel, ajout d'évaluateur, clôture. Aucun nouveau rejeu fournisseur demandé par cette note.

**Dossier documentaire uniquement. Aucun nouvel appel IA, aucune nouvelle fiche métier, aucune modification du code.**
