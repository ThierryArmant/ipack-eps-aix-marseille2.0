# Portée académique des réponses — 13 octobre 2026

Le hub est consulté hors de l'académie d'Aix-Marseille (lien publié par une autre académie). Beaucoup de fiches contiennent des consignes propres à Aix : DIEC, bulletins académiques (BA 549, 565, 566), circuit iPackEPS → Cyclades → Santorin piloté par l'inspection d'Aix, portail ESTEREL, consignes de l'assistance académique.

## En place
- Bandeau sous le titre du hub : les consignes académiques sont celles d'Aix-Marseille ; ailleurs, les vérifier auprès de sa division des examens ; les textes nationaux et le fonctionnement de Santorin et Cyclades valent partout.
- `config/portee_academique.json` : inventaire des fichiers (101 fichiers, 187 lignes au 13 octobre 2026) qui contiennent un passage propre à Aix, avec les lignes concernées. Il est généré par `python portee_registre.py --write`, à relancer après toute modification de fiche (un test signale un registre périmé). Une ligne est marquée si elle nomme explicitement Aix (Aix-Marseille, DIEC, BA académique, ESTEREL, adresse ac-aix) ou si elle appartient à une section dont le titre nomme Aix ; un constat « aucune consigne d’Aix trouvée », une simple précision « (DIEC à Aix-Marseille) » ajoutée à un acteur générique, une règle nationale et le fonctionnement d'un logiciel ne sont pas marqués.

## À brancher dans l'interface
1. Choix de l'académie au début (« Aix-Marseille » / « autre académie »), conservé dans la session.
2. Si « autre académie » : pour tout passage listé dans `config/portee_academique.json`, la réponse présente la consigne comme « consigne d'Aix-Marseille, à vérifier auprès de votre division des examens », jamais comme une règle générale ; les dates et contacts d'Aix ne sont pas donnés comme applicables.
3. Les réponses en dur fondées sur des consignes d'Aix (protocoles 2026, délai d'activité établissement, inscription « APTE ») portent la même mention pour un utilisateur d'une autre académie.

## Coût
Une ouverture à d'autres académies peut porter le volume à environ 4 000 questions par mois : environ 6 $ par mois avec un appel par question, 15 à 20 $ avec trois appels. Le plafond mensuel actuel est de 11,96 $ : viser un appel par question (contrôle par le programme, correction seulement en cas d'échec) et mettre en mémoire les réponses aux questions fréquentes.
