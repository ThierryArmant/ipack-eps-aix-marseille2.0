# Reprise du travail — état au 18 octobre 2026, 18 h 50 (à lire avant toute modification)

Ce document permet de reprendre le travail sans contexte préalable. Le détail chronologique est dans `docs/journal_coordination.md` (entrées du 17 et du 18 octobre). La présentation générale du projet est dans `docs/reprise_projet.md`.

## 1. Règles fixées par Thierry (non négociables)
- Pousser directement sur `main` ; garder l'historique ; toujours `git pull --rebase` avant de pousser (deux assistants travaillent sur le dépôt).
- Ne valider (commit) que si **toute** la suite de tests passe : `python3 -m unittest discover -s tests -q`. Avant chaque commit, annuler les fichiers de cache Python suivis par git : `git checkout -- __pycache__ tests/__pycache__; git clean -fq -- __pycache__ tests/__pycache__`.
- Pas de règle sans source pertinente : répondre partiellement et signaler le manque. Pas d'étape de logiciel inventée : seulement ce qui a été vu à l'écran ou dit par le correspondant (ou le référent de la FAQ lycée).
- Aucun appel IA systématique supplémentaire. Le guide pas à pas n'appelle jamais l'IA.
- Dépôt public : aucun nom d'élève, de collègue ou d'établissement dans les fiches ; ne pas nommer Thierry dans les fiches (« correspondant académique iPackEPS », « référent de la FAQ lycée »).
- Documents destinés aux collègues : ne citer aucun outil d'IA.
- Les fonctions d'iPackEPS sont communes à toutes les académies ; les dates et consignes d'Aix-Marseille vont dans une fiche marquée Aix-Marseille (`academie: aix-marseille` dans `config/nature_sources.json`, puis `python3 portee_registre.py --write`).
- Ton envers les collègues : conditionnel, sans reproche (« si vous avez respecté l'ordre…, vous devriez pouvoir… », jamais « avez-vous rempli… ? »).
- Secrets (mot de passe admin, adresses IPR, SMTP) : uniquement dans les secrets Streamlit, jamais dans le dépôt. L'ancien mot de passe admin publié dans le dépôt est à considérer comme compromis (Thierry doit définir `ADMIN_PASSWORD`).

## 2. Ce qui a été fait le 18 octobre (partie iPackEPS)
### Visite guidée de l'espace professeur collège (avec le correspondant)
Fiches créées dans `data/ipack/visite_college_2026_10_18/` (9 fiches) : équipe EPS / TZR (« Remplace »), fiche professeur / fonctions / [Enregistrer], classes ([Actualiser] → configuration → organisation avec son nom → [Importer]), APSA-périodes-séquences (déclarer l'activité d'une classe), groupes AS/SSS et placement des élèves, équipements et emploi du temps (créneau par double-clic), natation (attestations ASNS), APPN, Dossier SSS (section absente ; cas « sportifs de haut niveau visibles mais pas la section » = activation côté inspection).
Corrections : import des élèves = [Importer] (et non [Actualiser]) ; champ « Remplace » ; boutons [Créer une APSA] / [Créer un groupe] ; bloc de validation du Dossier EPS.

### Visite de l'espace professeur lycée (lecture seule) + explications du référent de la FAQ lycée
Fiches dans `data/ipack/visite_lycee_2026_10_18/` : Dossier Certificatif (référentiels, protocole d'évaluation, CAHPN, Cyclades, soumission en deux blocs), APSA certificative et protocole d'un groupe, fiche établissement / vœux de jury / inaptitudes / Mes Élèves / Mes Documents, **réponses du référent FAQ lycée** (fiche prioritaire 310), **calendrier Aix-Marseille** (référentiels jusqu'au 30 mai ; export Cyclades seulement après validation des protocoles par la CAHPN, dépôt par l'inspection, import des candidats par la DIEC).
Points clés lycée : deux contextes de classes (Éducation nationale : classes importées et organisées, obligatoire pour les classes d'examen ; CFA/MFR/AEFE : groupes créés directement, candidats associés dans Cyclades) ; 3 étapes de l'examen (Classes → Groupes > Gérer les S.A. → Dossier Certificatif > Protocole) ; co-évaluateur obligatoire seulement en voie générale ; protocole valide = coches vertes (colonnes Validité et Référentiel ; 3 épreuves bac, 2 CAP) ; élèves sans groupe : Élèves > Visualisation « Statut » > liste Sélection « élèves sans groupes » ; [Envoyer] = déposer ou remplacer un référentiel ; [Exporter les Elèves] = fichier importable dans Cyclades. Voie pro et CAP : même structure (page APSA « APSA de Collège ou Voie Professionnelle »).

### Guide pas à pas (`guided_navigation.py`)
- Bouton « ❓ Vous êtes perdu(e) ? » sous la zone de question (mode iPackEPS) ; s'ouvre aussi automatiquement, sans appel IA, pour les appels au secours (« aide moi je suis perdu ») et les demandes évasives de saisie (« J'enseigne le foot à mes 6eme4, comment renseigner ça ? ») : `guide_request.py` (`requests_guide`, `vague_request_opens_guide`).
- Guides par public : `config/guide_ipack_college.json` (Collège), `config/guide_ipack_lycee_gt.json` (Lycée voie générale), `config/guide_ipack_lycee_pro.json` (Lycée voie professionnelle). Choix dans `guide_file(public)`.
- Structure d'un guide : `parcours` (nom → étapes `{clic, video, source, preuve}`) et `menu` (rubriques calquées sur les intitulés de l'écran : Établissement, Ma Fiche Professeur, Dossier EPS, Dossier Certificatif…, chaque entrée avec `libelle`, `parcours`, `prerequis`, éventuellement `cible`).
- **Garde-fou** : chaque étape doit retrouver sa phrase `preuve` dans son fichier `source` ; sinon tout le parcours est retiré à l'exécution. Les vidéos doivent être une clé de `config/tutoriels_parcours_college.json` ou une adresse de la playlist `config/playlist_tutoriels_ipackeps.json`. Tests : `tests/test_guide_college.py`, `tests/test_guided_navigation.py`, `tests/test_guide_request.py`.
- Affichage : liste « Choisissez un dossier… », sous-menu à côté ; au-dessus des étapes « Avant [X], vous devez avoir complété : … » ; toutes les étapes affichées d'un coup ; une étape qui a une vidéo est un bandeau bleu « ▶ N. … · Lancer le tutoriel vidéo » (clic = vidéo) ; plus de bouton Suivant/Retour ; [✓ J'ai trouvé] referme le guide et revient à la question. Pas de saisie, très peu de texte (demande de Thierry : « épurer au max »).
- Styles du guide dans `app.py` (CSS `st-key-guide_callout_*`) : texte blanc, boutons fond blanc, intitulé vidéo surligné.

### Playlist des tutoriels
Inventaire dans `config/playlist_tutoriels_ipackeps.json` (92 vidéos visibles sur 107 annoncées). Vidéos utiles rattachées au guide et aux fiches lycée (champ `tutoriels` du catalogue).

## 3. Où modifier quoi
- Ajouter ou corriger une fiche : fichier `.txt` dans `data/…` (première ligne `### titre`, lignes « Réponse directe — … », puis « Nature de la source » et « Source ») ; l'inscrire dans `config/nature_sources.json` (indent 1) et `config/catalogue_documents.json` (indent 2 ; `prioritaire`, `priorite`, `modes`, `examens`, `motifs` testés sur la question enrichie et normalisée sans accents, `exclure_motifs` sur la question d'origine normalisée) ; puis `python3 portee_registre.py --write`.
- Vérifier quelle fiche une question déclenche : `python3 -c "import knowledge_catalog as kc; print(kc.priority_titles('question', 'Collège', 'ipack'))"` (publics : `Collège`, `Lycée Général & Techno`, `Lycée Pro / CAP`, `1er degré`). Attention : une question qui cite Cyclades est routée vers le mode Examens (`effective_context`).
- Ajouter une étape au guide : modifier le JSON du public ; la phrase `preuve` doit figurer mot pour mot dans la fiche `source`.

## 4. Reste à faire
1. Mesure réelle après les vacances (export de l'historique vers le 9 novembre ; noter correct / partiel / faux avant de corriger).
2. Vérifier sur un vrai lycée professionnel la fenêtre « Configuration d'une APSA » (case « Certificative ») — Thierry dit que c'est la même structure que la voie générale.
3. Question ouverte : quand un TZR complète le service d'un collègue, faut-il passer le collègue remplacé sur NON ? Ne rien affirmer au-delà du texte de l'écran.
4. Nom exact des cases que l'IPR coche pour activer une section sportive : à relever lors de la visite de l'espace IPR.
5. Espace IPR (après finalisation des fiches) : accès réservé par code envoyé à des adresses autorisées ; liste des adresses et boîte d'envoi à placer dans les secrets Streamlit ; visite en lecture seule (ne jamais cliquer Valider, Refuser, Envoyer, Enregistrer).
6. Textes officiels à demander à Thierry (non intégrés) : ISSR, frais de déplacement (décret 2006-781), section natation second degré de la note 2022, sorties ski, devoirs faits, pacte / RCD, circulaire AS/UNSS, circulaire 90-107.
7. Surveiller : la question « je vois les sportifs de haut niveau mais pas ma section sportive » reçoit aussi une fiche DNB voisine (le filtre des fiches ciblées devrait l'écarter à la rédaction).

## 5. Navigation dans iPackEPS (si une nouvelle visite est faite)
Entrer par https://appli.ac-aix-marseille.fr/ipackeps/professeur/ (Thierry se connecte lui-même ; ne jamais saisir d'identifiants). Ne pas passer par le favori ESTEREL (il ouvre l'espace Correspondant). Les adresses de sous-pages ne s'ouvrent pas directement : naviguer par clics. Ne cliquer sur aucun bouton qui modifie (Enregistrer, Valider, Ajouter, Effacer, Envoyer, Importer, Actualiser, Créer…) sans accord explicite bouton par bouton. Ne relever aucune donnée personnelle.
