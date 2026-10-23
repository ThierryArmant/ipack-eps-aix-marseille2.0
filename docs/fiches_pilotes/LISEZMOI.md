# Pilote de modèle commun des fiches

Ce pilote prépare une structure réutilisable. Les trois JSON de ce dossier sont des prototypes hors index documentaire : ils ne remplacent pas les fiches actives et ne modifient pas la réponse du Hub. Ne pas convertir massivement avant des essais sur plusieurs situations.

## Champs communs

| Champ | Règle de rédaction |
|---|---|
| `id`, `type`, `situation` | Identifier la situation et distinguer diagnostic, navigation et règle/circuit. |
| `scope` | Déclarer diplômes, académies et logiciels ; répéter la portée propre à chaque branche. `non_precisee` signifie que la portée académique n’est pas attribuée précisément dans ce prototype ; ce n’est pas une garantie de validité nationale. |
| `verification` | Conserver date et statut. Ici seules structure et copies sont contrôlées ; sources non revalidées. |
| `sources` | Fichier d'origine, empreinte SHA-256 et liens déjà présents. Un lien recensé n'est pas une source relue à cette date. |
| `branches[].condition` | Nommer la condition sans la présenter comme un fait donné par l'utilisateur. |
| `steps[].actor` | Identifier qui réalise l'action. |
| `steps[].nature` | Distinguer manipulation logicielle, circuit académique et synthèse réglementaire. |
| `steps[].text`, `evidence` | Chaque unité garde un extrait exact de la fiche d'origine et sa preuve ; les règles, préalables et réserves restent liés. |
| `steps[].navigation` | Recopier les chemins et libellés exacts ; ne pas inventer de séquence en rapprochant deux écrans. |
| `steps[].required_elements` | Éléments dont une omission mérite une revue. Ce sont des repères documentaires, pas une réponse en dur dans le code. |
| `branches[].limits` | Réserves et exceptions recopiées de la source, à lire avec la branche. |

Une action par unité lorsqu'une séparation ne fait pas perdre son contexte. Une condition, une exception ou un acteur indispensable doit rester dans la même unité ou dans la branche qui la porte. Une règle ne se découpe pas en fragments qui en changeraient le sens. Les trois prototypes ne représentent pas exhaustivement tous les sujets des fiches d'origine : ils couvrent les branches explicitement inventoriées.

## Trois exemples

- `santorin_saisie_bloquee.json` : GT, pro/CAP, cadenas et clarification tardive ; répartition et chemin de déverrouillage explicitement repérés.
- `ipack_multi_etablissements.json` : navigation et préalables administratifs ; délai indicatif sans garantie conservé et circuit local distingué.
- `gt_absence_ccf.json` : règle GT, force majeure et circuit d'Aix-Marseille distincts. La qualification d'une absence reste une appréciation des faits et justificatifs ; le script ne prend aucune décision individuelle.

Les références sont celles des fiches existantes. Le pilote ne confirme pas à nouveau les textes, écrans ou témoignages cités et ne prétend pas avoir transcrit les vidéos de visite.

## Vérification hors ligne

Depuis la racine du dépôt :

```bash
python scripts/fiche_pilot.py
python -m unittest discover -s tests -p 'test_fiche_pilot.py' -q
```

Le contrôleur vérifie champs, portées déclarées, identifiants, empreintes, citations exactes et présence des repères dans les extraits. Il ne prouve ni l'exactitude métier des sources, ni l'applicabilité de la branche à une personne, ni l'exhaustivité du prototype.

Pour examiner une trace locale sans l'envoyer à un service :

```bash
python scripts/fiche_pilot.py --trace /chemin/trace.json --pilot docs/fiches_pilotes/santorin_saisie_bloquee.json --branches gt lot_verrouille
```

Les branches sont choisies explicitement par le réviseur : sélectionner une branche hypothétique ne signifie pas qu'elle est établie. L'outil signale les omissions lexicales possibles dans la proposition initiale de l'IA. Une reformulation correcte peut être signalée et une erreur de sens peut lui échapper. Il ne répare, ne publie et n'accepte automatiquement aucune réponse ; il ne lance aucun appel réseau. Ne pas transformer tous ces signaux en blocages dans le Hub sans mesurer leurs effets sur plusieurs cas.

## Suite nécessaire avant généralisation

1. Relire le découpage et les attributions avec les sources propres à chaque exemple.
2. Éprouver le format sur un petit lot comprenant procédures, diagnostics et règles avec exceptions.
3. Mesurer omissions, erreurs et jetons sur les mêmes questions, modèles et paramètres.
4. Décider ensuite comment alimenter la recherche et la rédaction avec cette structure, en gardant les preuves et une trace de migration.

Les consignes courtes restent un essai administrateur. Elles ne sont pas devenues les consignes générales du Hub. La dernière réponse citant le bon passage mais omettant le chemin ne justifie pas une réinsertion automatique du chemin dans toutes les réponses.
