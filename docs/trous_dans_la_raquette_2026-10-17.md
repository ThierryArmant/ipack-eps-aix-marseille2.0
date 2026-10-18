# Trous dans la raquette — pourquoi des erreurs alors que les fiches existent (17 octobre 2026)

Base : analyse des réponses de la troisième mesure (version f2b989b, 50 questions), puis relecture du catalogue après les corrections 67d7af6, 3d8586b et suivantes. La série 3 a servi au diagnostic : elle ne peut plus servir de mesure. Une série 4 indépendante sera nécessaire pour mesurer.

## 1. Ce que montrent les erreurs de la série 3

| Cause | Questions | Part |
|---|---|---|
| A. Mauvaise fiche transmise, ou fiche hors sujet | M08, M09, I11, T05, T03, T08 | environ 1/3 |
| B. Bonne source transmise, mais lue de travers ou complétée par invention | I13, T06, T13, M16, M03, T09 | environ 1/3 |
| C. Bonne fiche, réponse non confirmée par le contrôle | M14, T05 | rare |
| D. Aucune source dans le corpus | T12, M20, M07 (partiel), I04 | environ 1/5 |

Le problème principal n'est donc pas l'absence de fiches. C'est **quelle fiche arrive au modèle, et sous quelle forme**.

## 2. Pourquoi iPackEPS est meilleur qu'Examens et Textes

1. **Les fiches iPackEPS répondent à une question à la fois.** Un chemin de menu, un symptôme, une cause. Les fiches d'examen et de textes sont souvent des synthèses : une ligne porte trois ou quatre règles conditionnelles (inaptitude → moyenne de deux notes / note unique / dispense). Le modèle choisit alors la mauvaise branche.
2. **Les fiches Textes s'ouvrent souvent sur des métadonnées ou une liste thématique.** Une vingtaine de fiches ciblées de l'onglet Textes commencent par « Nature de la source : … » et couvrent un thème large (carrière, sorties, RGPD…), sans phrase qui réponde. Les fiches d'examen, elles, commencent presque toutes par la réponse (« Oui… », « Non… »). Pour une question précise, la ligne « Réponse directe » s'est montrée la correction la plus efficace (SHN ponctuel, DNB dispensé, laïcité…).
3. **Des fiches d'examen débordaient sur l'onglet Textes.** 24 fiches prioritaires n'avaient aucun onglet déclaré, dont 9 fiches DNB. Exemple : une question sur une dispense d'un mois recevait la fiche « examen DNB ». Corrigé (3d8586b).
4. **Des fiches générales à motifs très larges.** Exemple : « Bac GT : CCF, activité établissement et harmonisation », qui se déclenche sur « ponctuel », « commission », « inapt… note »… Elle arrive sur beaucoup de questions d'examen avec des lignes de plus de 1 500 caractères. Quand elle accompagne une fiche ciblée, le modèle peut mélanger les deux.
5. **Correction (18 octobre) : une fiche ciblée n'exclut la recherche documentaire que si elle est « exclusive ».** Sinon, les passages trouvés par la recherche s'ajoutent, et un passage voisin peut l'emporter sur la bonne fiche. Exemple : « collègue en arrêt depuis la Toussaint » a reçu la bonne fiche, mais la réponse a suivi la FAQ « co-évaluateur absent le jour du CCF », venue par la recherche. Corrigé en rendant la fiche « absence prolongée du professeur » exclusive. À l'inverse, M08 et M09 ont échoué parce qu'une fiche voisine était sélectionnée.
6. **Vocabulaire des collègues différent de celui des textes** (« dispense » ≠ « inaptitude », « prof » ≠ « enseignant », « principal » ≠ « chef d'établissement »). Le contrôle lexical rejetait des réponses justes. La table d'équivalences strictes l'a en partie réglé.
7. **Textes manque de sources nationales de base sur l'inaptitude.** La circulaire 90-107 (1990), le décret 88-977 et l'arrêté du 13 septembre 1989 ne sont pas intégrés. Les questions de vie courante (présence en cours, rôle du médecin scolaire) ne trouvent qu'une fiche partielle.

## 3. Corrections faites cette nuit (sources vérifiées)

- **Contrôle adapté au bac GT** (inaptitude partielle permanente, handicap) : trois cas — trois épreuves dont une adaptée, deux adaptées, ou une seule. Concertation avec la santé scolaire, PPS/PAI, commission académique. Source : note 2026, 2.e. Fiche ciblée, exclue pour l'inaptitude totale ou temporaire.
- **Protocole porté à la connaissance des élèves et familles** (note 2026, 2.b). Réponse directe : oui. Le support n'est pas fixé par le texte.
- **Bouton d'envoi du dossier grisé** (iPackEPS) : fonctions Coordonnateur EPS et Responsable de la Certification, vérification des données et alertes. Sinon, l'assistance.
- **Inapte ou dispensé : doit-il venir en cours ?** Le certificat n'autorise pas l'absence ; la dispense est une décision de l'établissement, selon le règlement intérieur. Code de l'éducation R. 312-2, avec les documents de Besançon et de Martinique. La **lacune est signalée** : circulaire 90-107 non intégrée.
- **Vidéo en EPS** : la fiche est désormais aussi disponible dans l'onglet Textes.

## 4. Trous restants (par ordre d'impact)

1. **Fiches Textes thématiques à découper en fiches-réponses courtes**, chacune ouverte par sa réponse. C'est le plus gros levier pour l'onglet Textes. À faire question réelle par question réelle (historique des collègues), seulement à partir du texte de la fiche, sans règle nouvelle.
2. **Fiche générale GT à découper** : chaque bloc (activités / commission / inaptitude / absence du professeur) en fiche courte et ciblée. Cela évite qu'un bloc voisin pollue la réponse.
3. **Textes nationaux d'inaptitude à intégrer** : circulaire 90-107 du 17 mai 1990, arrêté du 13 septembre 1989, décret 88-977. Le texte officiel est à fournir : Légifrance n'est pas accessible d'ici.
4. **Sans source aujourd'hui** :
   - TZR sur deux établissements (emploi du temps, AS) ;
   - remplacement d'une activité après validation du protocole ;
   - rôles exacts en cas d'accident (qui prévient, qui déclare).

   Le hub doit répondre partiellement et le dire.
5. **21 fiches prioritaires sans source ni référence écrite**, surtout iPackEPS (pas grave pour le logiciel). Mais deux fiches d'examen sont concernées : « contestation de note » et « saisie CCF ». Une ligne Source est à ajouter.
6. **4 fiches sans onglet déclaré**, donc présentes partout :
   - responsabilité civile et pénale ;
   - SSS ;
   - sport-études ;
   - remplacement d'AS.

   Pour l'instant c'est volontaire, mais à surveiller.
