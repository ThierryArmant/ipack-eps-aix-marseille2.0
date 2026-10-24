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
