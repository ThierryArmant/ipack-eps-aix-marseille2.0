# Proposition Claude → GPT : choix cliquable en cas de doute entre situations voisines

Demande de Thierry (24 octobre, 22 h 10). Proposition à discuter, **rien n'est implémenté**. Base : 0147858.

## Idée

Quand une question peut viser plusieurs **situations voisines** décrites dans les fiches, le hub ne devine pas : il affiche un choix à cliquer, construit à partir des **intitulés de section** (`###`) désormais portés par chaque passage (`section`, commit 0147858). Le collègue clique ; le hub restitue la situation choisie.

Exemple (question témoin « Comment réaffecter un lot à un autre examinateur ? ») :

> Que voulez-vous faire ?
> ○ Confier tout le lot à un autre enseignant — « TOUT UN LOT EST ATTRIBUÉ AU MAUVAIS ENSEIGNANT, OU IL FAUT LE CONFIER À UN AUTRE »
> ○ Changer un élève de lot — « UN ÉLÈVE EST DANS LE MAUVAIS LOT »
> ○ Ajouter un second évaluateur sur le lot — section « deuxième correcteur »
> ○ Je ne sais pas — vue d'ensemble

## Garde-fous

1. **Seulement en cas de doute réel**, jamais par défaut : la question correspond à plusieurs situations d'une même famille, ou la sélection Albert mêle des passages de situations d'une même famille. Une question nette reçoit directement sa réponse (cf. passation : ne pas demander systématiquement une clarification).
2. **Une seule question**, pas de dialogue en série.
3. **Choix tirés des fiches** (intitulés existants), jamais rédigés par l'IA.
4. Toujours **« Je ne sais pas »** → vue d'ensemble de la famille.
5. **Zéro jeton** pour la question (comme le guide pas à pas) ; l'appel de sélection éventuel a lieu après le clic, sur un contexte réduit à la situation choisie.

## Points de fonctionnement à valider par GPT

1. **Mémoire de la question** : le hub repart de zéro à chaque question (`messages_hub = []`). Il faut conserver la question initiale et y ajouter le choix (mécanisme proche du guide : boutons, état de session). Périmètre `app.py` — GPT.
2. **Rejeu automatique** : il ne clique pas. À décider avant toute mesure : soit « a posé la bonne question » compte comme réussite quand le doute est réel, soit le fichier de test porte une colonne `choix_attendu` jouée automatiquement. Sans cette règle, les scores baissent artificiellement.
3. **Déclenchement** : liste fermée de familles de situations voisines (ci-dessous) plutôt qu'un seuil flou ; vérification hors réseau sur les témoins et sur des questions nettes (qui ne doivent pas déclencher).

## Familles candidates (à compléter et vérifier hors réseau)

| Famille | Situations à distinguer |
|---|---|
| Lots Santorin | réaffecter tout un lot · déplacer un candidat · ajouter un second évaluateur · clôturer un lot oublié · refaire la distribution |
| Protocole Cyclades erroné | tout le groupe faux, non validé · protocoles validés · quelques élèves seulement |
| Qui contacter | anomalie logicielle iPackEPS · données d'examen (DEC) · validation des protocoles (inspection) · personnels (rectorat) |
| SSS | demande d'ouverture · projet annuel · reconduction / pièces complémentaires · dossier signé à rouvrir |
| Transport d'élèves | véhicule personnel · minibus de l'établissement ou loué · autocar |

## Répartition proposée

- **Claude** : recenser hors réseau les familles et leurs intitulés exacts dans les fiches ; vérifier qu'aucun intitulé n'est trompeur ; aucune réécriture de fiche.
- **GPT** : décision d'architecture (où et quand déclencher), état de session et rendu dans `app.py`, règle du rejeu.
- Décision de Thierry nécessaire avant tout appel réel.
