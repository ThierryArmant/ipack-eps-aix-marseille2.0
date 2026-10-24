# Restitution des conditions de branche : contrôle borné

Base : 9c5dd8d. Le rejeu privé des dix premières questions sur cette version conserve les contextes précédents : mini seul, 17 appels (7 orientations, 10 rédactions), 101693 jetons, aucun échec fournisseur, aucune réparation. Bilan manuel : cinq réponses exploitables, trois partielles, deux problématiques. Le raccordement Textes est corrigé, mais les réponses 6/7 perdent encore la condition de leur branche. Aucun nouvel appel IA n'est exécuté pour ce travail.

## Défauts reproduits

Les citations et leur existence sont correctes. Une prescription cite le passage commençant par « Branche — handicap ou inaptitude partielle permanente : », puis supprime le périmètre de la prescription. Une autre citation porte sur la branche temporaire, mais la proposition produite n'en conserve pas la condition. Enfin, une non-équivalence (« préparer ou saisir ne constitue pas une décision ») devient une obligation de préparer ou saisir. Les marqueurs supported/applicable retournés par le modèle ne prouvent pas ces interprétations.

## Modification

Deux vérifications dans evidence_logic, déjà appelé sur les affirmations sourcées avant affichage et lors de la réparation :

- Pour les preuves commençant explicitement par « Branche — condition : », une prescription doit conserver le périmètre d'une des alternatives citées. Vérification lexicale normalisée et limitée à ce format ; les deux branches peuvent être conservées dans deux phrases d'une même affirmation. Une réserve après « mais » ne corrige pas une prescription générale qui la précède.
- Une phrase indiquant qu'une action ne vaut pas décision/validation ne prouve pas que cette action est obligatoire. Si l'affirmation rend cette action obligatoire, rechercher une preuve distincte établissant cette obligation ; sinon signaler l'inférence.

Aucune condition médicale, aucun diplôme, aucune réponse attendue codés dans Python. Aucun changement de modèle, de température, de plafond d'appels ou de contenu des fiches. Le paquet immuable de génération inclut déjà evidence_logic : le nouveau code change son empreinte.

## Vérification et effets

Sur les affirmations acceptées enregistrées dans le CSV : trois affirmations de la question 6 sont signalées (l'une reçoit deux motifs), et une de la question 7. Les huit autres réponses ne reçoivent aucun nouveau signal de ces contrôles. Cela ne les certifie pas : les réponses 4/8/9 restent partielles selon l'analyse précédente.

Simulations avec les propositions exactes de 6/7 et une fausse réparation reproduisant la même erreur : rejet à l'issue des deux appels simulés et réserve institutionnelle par le rendu de secours existant. Test synthétique de réparation correcte : une prescription portant explicitement sa condition est acceptée. Dix tests dédiés couvrent cas réels, domaines fictifs, alternatives, deux branches explicites, réserve neutre, preuve sans marqueur, obligation séparément établie, réparation correcte et refus persistant.

La réparation reste celle qui existait : jusqu'à un appel de rédaction supplémentaire lorsqu'une réponse échoue au contrôle. Le nombre réel de réparations peut donc augmenter ; aucun nouvel appel n'est ajouté à chaque réponse par principe.

## Limites

Ce contrôle est lexical, pas une preuve sémantique. Il ne couvre pas toutes les formulations conditionnelles, peut demander la conservation explicite d'un libellé là où une paraphrase serait correcte, et ne prouve pas que les faits de l'utilisateur établissent la condition citée. Il ne choisit pas une branche à la place du modèle. Il ne vérifie pas à lui seul qu'une règle portant sur une branche n'est pas attribuée à l'autre. Ne pas annoncer 90 % ni une suppression générale des erreurs. La prochaine génération réelle de 6/7 reste à observer ; aucun lot massif n'est requis pour ce contrôle.

## Suite sur Examens — base 39ea338 : unités autonomes dans iPack 212

Le rejeu privé de 6/7 dans Textes avait déclenché deux réparations : 7 exploitable, 6 bloquée après une réparation encore incomplète. Puis les mêmes questions ont été déplacées vers Examens : 31346 jetons, deux orientations et deux rédactions, aucun rejet. Les deux réponses étaient pourtant défectueuses. La comparaison entre onglets ne mesure pas l'effet isolé d'un changement de code.

Le parcours Examens sélectionne aussi iPack 212. L'annotation nationale isolait « Pour une inaptitude temporaire… », puis le reste de la même ligne devenait une nouvelle preuve commençant par « Pas de nouvelle validation… ». Ce fragment avait perdu son antécédent. Le contrôle limité aux preuves portant un libellé explicite de branche ne pouvait pas récupérer une condition absente de sa preuve.

Réorganisation de la fiche existante, avec conservation du titre et des formulations de recherche : unités séparées pour permanente/handicap, temporaire (alternatives de certification), adaptation d'une épreuve si partielle temporaire, création technique éventuelle, déclaration d'inaptitude, calendrier avant/après, traçabilité et réserve SAV locale. La condition et l'action sont dans la même ligne et dans la même annotation. Les attributions nationales et logicielles couvrent désormais les unités complètes. Le code ne choisit pas le cas médical et aucune piste audio de visite n'est nouvellement exploitée.

Les alternatives d'une inaptitude temporaire totale ne sont pas supprimées : elles sont dans une unité distincte de l'adaptation d'une épreuve pour inaptitude partielle. La réserve technique Aix-Marseille est conservée avec sa date, son circuit et sa limite de portée. Les empreintes et le registre de portée sont actualisés, statut documentaire a_confirmer.

Le contrôle de branche conserve maintenant l'ordre des mots significatifs pour les libellés temporels explicites « avant/après la date… » ; rencontrer « après » ailleurs dans la phrase ne suffit plus à compenser une inversion. Il couvre aussi les possibilités et les conséquences négatives futures. Un contrôle borné repère également une action « au besoin » devenue obligatoire sans condition ni autre preuve établissant cette obligation. Il s'appuie sur le verbe cité et ne couvre pas tous les synonymes.

Six tests dédiés : vraies unités après annotation, nature nationale/logicielle, condition conservée dans la création, obligation injustifiée, inversion exacte de date, domaines fictifs et vérification des offsets. Un test ancien recherchait justement le fragment isolé « Pas de nouvelle validation » : il exige maintenant l'unité logicielle complète et sa condition. Les autres tests sont conservés.

Les contrôles restent lexicaux et bornés ; ils ne prouvent pas toute l'applicabilité et peuvent refuser des paraphrases éloignées. Aucun nouvel appel IA, aucune modification des plafonds de réparation. La prochaine rédaction réelle n'est pas prétendue validée par les tests locaux.
