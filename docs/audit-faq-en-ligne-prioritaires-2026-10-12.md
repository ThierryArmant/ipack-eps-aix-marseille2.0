# Audit en ligne des FAQ EPS — 12 octobre 2026 — première tranche

## Périmètre et limites
Application testée : https://assistant-ia-eps-aix-m.streamlit.app/
Comparaison avec les réponses attendues du fichier fourni « Texte collé(8).txt » (57 questions).
14 questions prioritaires testées, plus A2 et A3 : 16 réponses effectivement lues et évaluées.
B5 a répondu en version 7f7f403 ; B7 et les suivantes en version f380e5e. Le déploiement a changé pendant la série : aucun score global du hub ne doit être extrapolé.
Les 41 autres questions restent à tester. A1 a été soumise pendant une exécution interrompue, mais sa réponse n'a pas été conservée : non évaluée.
Aucune lecture de la série de réserve. Aucune modification des fiches pendant cet audit.
Les états hors ligne ne sont pas des réponses du hub : 124 tests techniques passants au commit 7f7f403, 2 réponses directes, 26 injections prioritaires et 29 questions dépendant de la recherche réelle, dans le harnais sans recherche sémantique ni recherche par mots.
Les délais et interruptions de la session d'automatisation ont interrompu la poursuite des tests ; ils ne prouvent pas une panne générale du site.

## Résultats
Les fiches ci-dessous sont celles AFFICHÉES par le hub, et non les fiches attendues dans le corrigé.

| Question | Verdict | Fiche citée / source affichée | Motif et correction attendue |
|---|---|---|---|
| B5 | partielle | data/examens/complement_cyclades_protocoles_cas_enseignant.txt ; data/examens/complement_saisie_santorin_cas_pratiques.txt ; data/examens/tutoriels_creteil_cyclades_santorin.txt | Donne la distribution et Imag’in, mais omet le problème d'adresse du coordonnateur et sa correction dans Cyclades > Contrôler / réaffecter des protocoles. |
| B7 | partielle | data/examens/circuit_aix_ipack_cyclades_santorin.txt ; data/ipack/complement_reponses_validees.txt | ESTEREL puis Santorin : manque le passage par Imag’in, Portail d’accès aux missions, mission Notation EPS CCF et choix de l’examen. |
| C3 | partielle | Bac GT : CCF, activité établissement et harmonisation ; Blocages des lycées : CCF EPS — bac GT ; data/examens/faq_evaluation_certification_2025_mise_a_jour_2026.txt | Correct sur l'accord du chef et la force majeure conditionnelle ; manque l’épreuve de substitution et son motif dans Santorin. La fiche blocage des lycées est encore citée pour une grève des trains : examiner le routage. |
| D1 | fausse | Bac GT : inaptitude totale annuelle sans évaluation | Contradiction interne : « vous ne devez pas mettre l’élève dans un groupe Cyclades », puis « reste dans son groupe et doit être associé à un protocole ». Supprimer la première affirmation ; conserver groupe et protocole, puis traiter les dispenses selon le circuit. |
| D2 | correcte | Aix-Marseille : inscriptions terminale GT, session 2027 (EPS) ; Aix-Marseille : certificats EPS — 2026 | Inscription APTE et distinction du statut final expliquées. Mentionner explicitement la portée Aix-Marseille ; le renvoi complémentaire au BA 2026 doit rester daté. |
| D8 | partielle | aucune fiche affichée — réponse PRÉCISIONS NÉCESSAIRES | La clarification demande totale/partielle, notes et adaptation, mais ne traite pas le certificat tardif. Demander académie, session, date d’établissement et période du certificat ; répondre sur la non-rétroactivité d’Aix 2026 sans importer les 15 jours de Lyon. |
| E3 | fausse | data/commun/texte_officiel_bac_gt_note_de_service_2026.txt ; data/examens/complement_note_de_service_bac_gt_2026.txt ; autres fiches médicales | Propose seulement une autorisation de « moins de trois activités ». Omet la solution propre au GT : impossibilité majeure de réaliser au moins deux activités attestée par l’inspection, demande au recteur pour le ponctuel terminal. |
| F2 | correcte | Aix-Marseille : protocoles et circuit EPS — 2026 ; data/ipack/complement_cyclades_cas_pratiques.txt | Distingue le protocole standard iPackEPS avec inspection préalable et le protocole adapté créé dans Cyclades. Ne pas confondre création technique et autorisation d’un aménagement certificatif. |
| F5 | partielle | data/examens/videos_tutoriels_cyclades_santorin.txt ; data/ipack/transcriptions_videos_tutoriels.txt ; tutoriels creteil cyclades santorin | Non sans coche verte : correct. Mais pas de contrôle du statut validé dans Cyclades ni du circuit de transfert par l’inspection à Aix ; formule vague « tenter de renvoyer ». |
| G3 | fausse | data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt ; data/ipack/fiches/correspondant_01_acces_comptes_enseignants.txt ; data/ipack/complement_questions_boite_assistance.txt | Affirme que les élèves arrivent dans Cyclades après création des classes dans iPackEPS. Expliquer les candidats inscrits et l’association directe aux protocoles dans Cyclades pour les établissements hors SIECLE relevant du guide applicable. |
| H3 | partielle | data/examens/tutoriels_creteil_cyclades_santorin.txt ; data/ipack/fiches/ipack_169_situation_santorin_lot_manquant_d_un_collegue_imag_in.txt ; data/ipack/fiches/ipack_009_situation_synchronisation_imag_in_santorin.txt | Le PDF est identifié. Manquent le signataire et l’adresse du protocole/lot ; la relance automatique est présentée comme systématiquement nécessaire, alors qu’il faut vérifier l’affectation. |
| I3 | partielle | data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt ; data/ipack/fiches/ipack_170_situation_santorin_epreuve_adaptee_et_distribution_des_lots.txt ; data/ipack/fiches/ipack_102_4_erreurs_de_distribution_et_distribution_manuelle.txt | Donne l’association dans Cyclades, mais énonce l’absence de blocage total sans qualifier la portée ni la divergence Lyon/DIEC ; omet la distribution manuelle du candidat restant. |
| J1 | partielle | data/examens/complement_cyclades_protocoles_cas_enseignant.txt ; data/examens/fiches/examens_105_situation_santorin_valider_definitivement_ses_notes_eps.txt ; data/examens/fiches/memoire_examens_santorin_011_3_saisie_des_notes_et_cas_particuliers_santorin_ccf.txt | Non au verrouillage après CCF1 : correct. Expliquer explicitement toutes les notes du lot saisies et vérifiées, évaluations différées comprises, plutôt que seulement attendre une réunion. |
| J2 | correcte | data/examens/complement_cyclades_protocoles_cas_enseignant.txt ; data/examens/fiches/examens_105_situation_santorin_valider_definitivement_ses_notes_eps.txt ; data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt | Chef > Correction > Liste des lots > cadenas ; correction puis reverrouillage. Tutoriel associé affiché consacré au verrouillage : vérifier sa pertinence pour le déverrouillage. |
| A2 | correcte | bac pro session 2026 ; Bac professionnel : circulaire EPS du 2 avril 2025 en détail ; data/examens/complement_saisie_santorin_cas_pratiques.txt | Explique qu’aucune co-évaluation obligatoire n’est imposée au bac pro et que l’enseignant peut évaluer seul. |
| A3 | partielle | Bac GT : CCF, activité établissement et harmonisation ; data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt ; data/examens/complement_cyclades_protocoles_cas_enseignant.txt | Pas de DI collectif ; accord préalable puis Déclarer CE : correct. La réponse attribue l’autorisation uniquement à la commission ; préciser recteur après expertise de l’inspection et circuit direction/inspection/DIEC, selon le corrigé. |

## Priorités de correction pour Claude
1. D1 : contradiction dangereuse sur groupe/protocole Cyclades.
2. E3 : distinguer les exceptions GT et bac pro ; exposer la demande de ponctuel terminal prévue au GT.
3. G3 : supprimer le lien causal erroné entre classes iPackEPS et arrivée des élèves dans Cyclades.
4. B5 : injecter la fiche de réaffectation des adresses ; elle existe mais la réponse l’omet.
5. D8 : ne pas détourner une demande sur la rétroactivité vers une clarification générale d’inaptitude.
6. B7/H3/I3/F5/J1/C3/A3 : compléter les étapes manquantes et borner les procédures à leur portée.
7. La phrase finale d’assistance iPackEPS reste visible pour les réponses Examens/Santorin. Sa suppression doit viser ce renvoi automatique, pas les mentions de contact concernant les données personnelles.

## Bilan de cette tranche uniquement
4 correctes, 9 partielles, 3 fausses sur 16.
Pour les 14 prioritaires uniquement : 3 correctes, 8 partielles, 3 fausses.
Le corrigé fourni sert de référence de notation ; cet audit ne constitue pas une nouvelle validation indépendante de toutes ses sources.
Ne pas présenter ce résultat comme le score des 57 questions ni comme une mesure générale du hub.
