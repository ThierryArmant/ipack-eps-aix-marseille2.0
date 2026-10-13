# Lecture des sources et trace exacte — 13 octobre 2026

Base : 852f7c4. Intervention GPT limitée au code et aux tests ; aucune fiche ni aucun catalogue modifiés.

## Problème constaté en ligne

Onze reprises : EX245, EX267, EX269, EX270, EX274, EX275, EX283, EX290, EX298, EX300 et EX170. Les procédures demeurent attribuées au BO en EX245/EX269/EX270. EX275 invente encore un développement de sigle. Les derniers changements de fiches ont supprimé AMEX en EX298/EX300. Ces reprises sont un diagnostic, pas une mesure de fiabilité.

## Ce qui change

En mode Examens, chaque passage de recherche conserve son identité (path/title/priorité) après concaténation. Lorsqu’il existe des fiches spécifiques de priorité au moins 300 déjà choisies par le catalogue, la rédaction s’appuie sur elles ; les autres passages restent dans le diagnostic mais ne sont pas envoyés dans ces appels. Les faits calculés par le programme restent transmis. Sans fiche spécifique, tous les passages disponibles sont transmis. Le catalogue et la recherche sont inchangés ; seule la lecture est resserrée pour éviter les démarches d’un cas voisin. Le contexte complémentaire est explicitement séparé. Deux appels remplacent le brouillon libre puis sa relecture : extraction indépendante d'affirmations sourcées, puis contrôle de l'implication, de l'applicabilité et des conditions. Le brouillon historique n'est plus transmis, même si le paramètre demeure accepté pour compatibilité.

Chaque affirmation sélectionne un document et des identifiants de passages avec une nature de source. Le programme copie les citations depuis les passages d’origine ; le modèle n’a plus à les recopier littéralement. Le programme contrôle l’existence du document, la sélection des passages, les références présentes dans les preuves, et la nature de source. Le niveau réglementaire exige une déclaration explicite de cette nature ou un texte officiel transcrit ; un NOR, un nom de fichier ou un lien BO ne suffisent pas. Une synthèse peut être citée comme passage documentaire sans devenir un texte réglementaire. Une citation simplement bibliographique ne justifie pas une affirmation. Le rendu provient directement des affirmations contrôlées : il n'y a pas de troisième paraphrase. Les ajouts de prose après contrôle sont évités dans cette voie ; les contrôles existants restent appliqués dans les autres modes. Le verdict calculé sur les champs d'apprentissage reste conservé et est distingué dans la trace finale.

Le diagnostic administrateur contient le contexte exact, ses identités et empreintes, les prompts et sorties exacts des deux appels, les erreurs de validation, les affirmations acceptées/rejetées, et le corps affiché après les contrôles. Il est téléchargeable pour la réponse en cours. Il est conservé uniquement dans la session administrateur ; aucune trace complète n'est ajoutée au journal externe, à un fichier serveur ou à la conversation d'un collègue.

## Limites

La correspondance littérale et l'interdiction d'un niveau de source sont mécaniques. L'implication sémantique, la complétude et l'applicabilité sont toujours appréciées par le même modèle et peuvent être erronées. Cette méthode ne constitue pas une preuve juridique ni une garantie de correction. Les tests sans OpenAI vérifient les garde-fous et la trace, pas la qualité des réponses en ligne.

Un défaut de JSON peut être corrigé dans le second appel. Après ce contrôle, une seule réparation ciblée est autorisée si des passages ou des niveaux de source restent rejetés. Si la sortie finale conserve une affirmation sans citation vérifiable ou une décision non vérifiée, elle est bloquée au lieu de publier un brouillon libre. Cela peut accroître les réponses non confirmées ; il faut le mesurer. Deux appels restent nécessaires, avec un troisième uniquement pour la réparation ciblée, mais la longueur des sorties structurées et donc le délai/le coût peuvent augmenter. Modèle conservé : gpt-4o-mini par défaut (secret MODELE_IA inchangé).

## Validation

203 tests passent après la sélection par identifiants et la priorité des fiches de situation. Les premières versions de cette intervention (4c5637e, de22c9a) bloquaient EX245/EX269 parce que le modèle paraphrasait les citations. Ces essais sont un constat d’échec, pas une validation de ces versions. La sélection de passages résout le problème de recopie ; elle ne prouve pas la qualité sémantique. Les retests de la version finale sont consignés séparément.

Tests de citations déplacées entre documents, faux NOR, mauvaise nature de source, citation paraphrasée, défaut de conditions/applicabilité, erreurs réseau, JSON incomplet, fuite HTML et trace exacte. Vrai routage testé sans recherche sémantique réelle. Le contrôle en ligne est consigné dans le dossier séparé avec la version effectivement affichée. La réserve de 14 questions demeure intacte jusqu'au gel d'une version.
