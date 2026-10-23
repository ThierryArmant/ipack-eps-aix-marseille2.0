# Dix fiches : essais structurels de restitution de chemins

Ces résultats sont des scénarios simulés hors ligne sur les passages réels des dix fiches. La reformulation de départ omet volontairement le chemin. Aucun appel à mini : ce tableau ne mesure ni sa qualité, ni le taux de réponses complètes, ni la justesse métier des sources. Chaque scénario déclare une affirmation déjà acceptée ; les contrôles de preuve et de sens restent testés séparément par le test d’intégration.

Le code ne reconstitue jamais un chemin absent de la source. Il copie le passage logiciel transmis entier, sous conditions de longueur, citation unique, fichier enregistré et empreinte inchangée. Les étiquettes éditoriales, les passages longs et les chemins multiples sont laissés intacts. Les icônes ou chemins écrits autrement que `[Menu] > [Sous-menu]` ne sont pas traités par ce pilote.

| N° | Fiche | Passages avec chaîne reconnue | Restitutions exactes | Abstentions | Motifs supplémentaires |
|---|---|---:|---:|---:|---|
| 1 | `data/examens/complement_saisie_bloquee_diagnostic.txt` | 1 | 1 | 0 | aucune |
| 2 | `data/ipack/fiches/ipack_222_situation_enseignants_tzr_ou_partages_multi_etablissements.txt` | 0 | 0 | 0 | sans chemin de forme reconnue |
| 3 | `data/ipack/visite_college_2026_10_18/classes_actualiser_configurer_organiser_importer.txt` | 6 | 2 | 4 | libelle_editorial_a_separer, passage_long_ou_plusieurs_chemins |
| 4 | `data/ipack/visite_college_2026_10_18/equipe_eps_actualiser_tzr.txt` | 4 | 2 | 2 | libelle_editorial_a_separer |
| 5 | `data/ipack/visite_college_2026_10_18/natation_asns_diplomes_enquete.txt` | 2 | 1 | 1 | libelle_editorial_a_separer |
| 6 | `data/ipack/visite_lycee_2026_10_18/apsa_certificative_et_protocole_groupe_lycee_gt.txt` | 7 | 0 | 7 | libelle_editorial_a_separer, passage_long_ou_plusieurs_chemins |
| 7 | `data/ipack/fiches/ipack_066_article_88_dossiers_dossiereps_eleves_import_d_eleves_depuis_pronote_ecole_directe.txt` | 1 | 0 | 1 | passage_long_ou_plusieurs_chemins |
| 8 | `data/ipack/fiches/ipack_060_article_14_dossiers_dossiereps_classes_configuration_des_classes_et_import_des_eleves.txt` | 1 | 0 | 1 | passage_long_ou_plusieurs_chemins |
| 9 | `data/ipack/fiches/ipack_086_article_50_mes_eleves_visualisation_asns_validation_et_impression_de_l_asns.txt` | 0 | 0 | 0 | sans chemin de forme reconnue |
| 10 | `data/ipack/fiches/ipack_069_article_42_dossiers_dossier_certificatif_protocoles_configuration_des_protocoles_des_epreu.txt` | 1 | 0 | 1 | passage_long_ou_plusieurs_chemins |

Les refus sans motif supplémentaire peuvent venir d’une portée non logicielle ou d’une unité déjà exclue : ils ne constituent pas un échec du modèle. La portée et les restrictions du passage entier restent conservées en cas de copie. Aucun seuil de fiabilité globale ne peut être tiré de ce tableau.
