# Recensement hors réseau des situations voisines (Claude, 24 octobre 2026)

Base : 25e99db. Recensement des intitulés `###` existants dans `data/` (hors archives), par mots du titre. **Aucune fiche modifiée, aucun appel IA.** Liste brute de travail : elle ne dit pas qu'un choix cliquable doit être déclenché (accord avec GPT, 25e99db : une question explicite comme « réaffecter un lot à un autre examinateur » n'est pas ambiguë ; le choix est réservé aux discriminants réellement absents).

## Constats utiles au sélecteur, au-delà du choix cliquable

1. **Copies multiples d'une même situation dans des fichiers différents.** Exemple « élève dans le mauvais lot / déplacer un candidat » : `audit_faq_2026_10_12/g5_procedure_verifiee.txt`, `complement_reponses_validees.txt` (« DÉPLACER UN CANDIDAT D'UN LOT À UN AUTRE »), `cas_concrets_lots_inaptes_coevaluation_etranger.txt` (« UN ÉLÈVE EST DANS LE MAUVAIS LOT »). Réaffecter : `audit100_2026_10_20/reaffecter_evaluateur_cyclades.txt` (côté Cyclades), `cas_concrets…` (« TOUT UN LOT… »), `circuit_aix…` (portail établissement), `ipack_106` (suivi). Ces copies entrent en concurrence dans le même contexte et multiplient les lignes voisines proposées au modèle.
2. **Titres-bannières** (`############# LOTS DANS SANTORIN ################`, `############# CO-ÉVALUATION, DEUXIÈME CORRECTEUR, ENSEIGNANT ABSENT ###`) : ce sont des regroupements, pas des situations. `bind_sections` les traite comme intitulés seulement pour les lignes situées avant la première situation qui suit.
3. Les intitulés de `cas_concrets…` sont discriminants (objet + action) : ce sont les meilleurs candidats d'étiquettes si un choix est un jour proposé.

## Comptes par famille (titres contenant les mots de la famille)

- SSS 27
- Lots Santorin 68
- Transport 5
- Protocole Cyclades erroné 7
- Qui contacter 2

## Détail : famille « Lots Santorin » (la plus chargée)

  - Cyclades : faire réaffecter les protocoles au bon évaluateur | examens/audit100_2026_10_20/reaffecter_evaluateur_cyclades.txt
  - FAQ EPS — Absence d'enseignant : co-évaluateur absent le jour du CCF (bac GT) | examens/audit_faq_2026_10_12/a1_procedure_verifiee.txt
  - FAQ EPS — Absence d'enseignant : donner l'accès à la saisie d'un lot | examens/audit_faq_2026_10_12/a4_procedure_verifiee.txt
  - FAQ EPS — Blocage / distribution | examens/audit_faq_2026_10_12/b1_procedure_verifiee.txt
  - FAQ EPS — Certification réduite : un seul élève non évalué, pas de CE sur le lot | examens/audit_faq_2026_10_12/e4_procedure_verifiee.txt
  - FAQ EPS — Santorin : élève dans le mauvais lot | examens/audit_faq_2026_10_12/g5_procedure_verifiee.txt
  - FAQ EPS — Distribution : qui distribue les lots et quand | examens/audit_faq_2026_10_12/i1_procedure_verifiee.txt
  - FAQ EPS — Distribution : recommencer la distribution des lots | examens/audit_faq_2026_10_12/i2_procedure_verifiee.txt
  - FAQ EPS — Distribution : candidat non distribué, faute de protocole | examens/audit_faq_2026_10_12/i3_procedure_verifiee.txt
  - FAQ EPS — Santorin : quand verrouiller son lot | examens/audit_faq_2026_10_12/j1_procedure_verifiee.txt
  - FAQ EPS — Santorin : clôturer le lot d'un collègue qui a oublié (ce n'est pas déverrouiller) | examens/audit_faq_2026_10_12/j3_procedure_verifiee.txt
  - FAQ EPS — Santorin : candidature non valide, lot impossible à verrouiller | examens/audit_faq_2026_10_12/j4_procedure_verifiee.txt
  - Élèves inscrits mais absents des lots Santorin | examens/audit_lot1_2026_10_12/eleves_manquants.txt
  - Après la saisie : harmonisation, clôture et remontée des notes (Santorin, Cyclades) | examens/audit_lot4_2026_10_13/harmonisation_cloture_remontee.txt
  - Bac GT : statut SHN obtenu après la clôture des inscriptions | examens/audit_lot4_2026_10_13/shn_statut_tardif.txt
  - ############# LOTS DANS SANTORIN ################ | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — MESSAGE « AUCUN CORRECTEUR POUR CETTE ÉPREUVE », IMPOSSIBLE DE DISTRIBUER LES LOTS] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — LA DISTRIBUTION AUTOMATIQUE ÉCHOUE : « NOUS N'AVONS PAS TROUVÉ D'EXAMINATEUR CORRESPONDANT AU MAI | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — DES ÉLÈVES SONT DANS CYCLADES MAIS JE NE LES VOIS PAS DANS MON LOT] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — ERREUR « LA CANDIDATURE N'EST PLUS VALIDE DANS LE SYSTÈME D'INFORMATION EXAMENS/CONCOURS », OU IM | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — IMPOSSIBLE D'AFFECTER DANS UN LOT UN ÉLÈVE VENU D'UN AUTRE ÉTABLISSEMENT OU D'UNE AUTRE ACADÉMIE] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — UN ÉLÈVE EST DANS LE MAUVAIS LOT] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — TOUT UN LOT EST ATTRIBUÉ AU MAUVAIS ENSEIGNANT, OU IL FAUT LE CONFIER À UN AUTRE] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — LA DISTRIBUTION DES LOTS A ÉTÉ MAL FAITE, PEUT-ON RECOMMENCER ?] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN — ENSEIGNANT QUI ÉVALUE POUR PLUSIEURS EXAMENS : JE NE RETROUVE PAS TOUS MES LOTS] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - ############# CO-ÉVALUATION, DEUXIÈME CORRECTEUR, ENSEIGNANT ABSENT ################ | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: « DEUXIÈME CORRECTEUR » DANS SANTORIN POUR L'EPS — CE N'EST PAS LA DOUBLE CORRECTION DES COPIES] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: BAC GÉNÉRAL ET TECHNOLOGIQUE — LE CO-ÉVALUATEUR EST ABSENT OU NON REMPLACÉ LE JOUR DE L'ÉPREUVE] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: L'ENSEIGNANT ÉVALUATEUR EST ABSENT AU MOMENT DE LA SAISIE DES NOTES] | examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt
  - [SITUATION: SANTORIN, PORTAIL ÉTABLISSEMENT — IL MANQUE DES ÉLÈVES APRÈS LA DISTRIBUTION, OU UN ENSEIGNANT A OUBLIÉ DE C | examens/circuit_aix_ipack_cyclades_santorin.txt
  - [SITUATION: SANTORIN — FAUT-IL UNE DATE DE FIN DE CORRECTION POUR DISTRIBUER LES LOTS ?] | examens/complement_cyclades_protocoles_cas_enseignant.txt
  - [SITUATION: CADENAS ET DÉVERROUILLAGE DE LOT SUR SANTORIN] | examens/complement_reponses_validees.txt
  - [SITUATION: DÉPLACER UN CANDIDAT D'UN LOT À UN AUTRE DANS SANTORIN] | examens/complement_reponses_validees.txt
  - [SITUATION: FAUT-IL VERROUILLER SON LOT TOUT DE SUITE APRÈS LA SAISIE ?] | examens/complement_saisie_santorin_cas_pratiques.txt
  - [SITUATION: QUI SAISIT LES NOTES DE CCF, ET QUE FAIRE SI L'ÉVALUATEUR EST ABSENT ?] | examens/complement_saisie_santorin_cas_pratiques.txt
  - [SITUATION: SANTORIN AFFICHE « AUCUN LOT À CORRIGER »] | examens/fiches/correspondant_04_cyclades_santorin_imagin.txt
  - [SITUATION: UN EXAMINATEUR MANQUE (LOTS ABSENTS, ENSEIGNANT ABSENT DE LA LISTE)] | examens/fiches/correspondant_04_cyclades_santorin_imagin.txt
  - [SITUATION: SANTORIN POUR LES CORRECTEURS — À QUOI IL SERT, OUVRIR, ANNOTER ET NOTER UNE COPIE DÉMATÉRIALISÉE] | examens/fiches/examens_101_situation_santorin_correction_et_annotation_copie.txt
  - 2. Logistique Santorin et Distribution des Lots | examens/fiches/memoire_examens_santorin_010_2_logistique_santorin_et_distribution_des_lots.txt
  - Santorin — Repérer la mention SHN dans un lot | examens/pilote_shn_2026_10_16/reperer_mention_santorin.txt

Les autres familles (SSS, transport, protocole Cyclades erroné, qui contacter) restent dans la liste de travail ; à détailler seulement si GPT ou Thierry le demandent.
