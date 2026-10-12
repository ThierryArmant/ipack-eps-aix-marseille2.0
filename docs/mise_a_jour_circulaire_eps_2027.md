# Circulaire EPS session 2027 d'Aix-Marseille : fiches à reprendre

Préparé le 13 octobre 2026. Les fiches ci-dessous s'appuient sur le BA spécial 549 du 17 octobre 2025 (EPS, session 2026).
Les BA spéciaux 565 et 566 du 9 octobre 2026 traitent des inscriptions de la session 2027 ; ils ne remplacent pas la circulaire EPS.
Dès la publication du BA EPS de la session 2027, relire chaque point ci-dessous et mettre à jour la fiche, sa source et son lien.

Règle : ne reprendre que ce que le nouveau BA écrit. Un point absent du nouveau texte reste daté « session 2026 », sans être étendu à 2027.

## 1. Calendrier et circuit des protocoles (priorité haute)
| Point à relire dans le BA 2027 | Fiche | Remarque |
|---|---|---|
| Dates de la CAHPN (GT/pro, EPPCS), dépôt des protocoles et FCA dans iPackEPS, transmission vers Cyclades par l'inspection | `data/commun/audit60/aix_protocoles_2026.txt` | **Garde-fou en dur** dans le catalogue : réécrire aussi la réponse en dur |
| Date limite de demande d'activité établissement (2026 : 30 mai 2026 pour la session 2027) | `data/examens/activite_etablissement_delai_aix.txt` | **Garde-fou en dur** : mettre la nouvelle échéance (session 2028) seulement si le BA la donne |
| Rôle de la CAHPN et de l'inspection dans le circuit | `data/examens/tutoriels_creteil_cyclades_santorin.txt` (l. 56) | Une phrase |
| Ajout d'un protocole standard après validation | `data/examens/audit_lot3_2026_10_12/protocole_standard_apres.txt` | Vérifier si le BA décrit la procédure |
| Listes d'APSA et activités d'établissement (annexes 1 et 2) | `config/decisions_validees.json` (décision citant les pages 2-3) | Mettre à jour la source |

## 2. Certificats et inaptitude
| Point à relire | Fiche | Remarque |
|---|---|---|
| Annexes 7 (ponctuel) et 8 (CCF), médecin, absence d'effet rétroactif, délai de remise éventuel | `data/commun/audit60/aix_certificats_2026.txt` | Si le BA 2027 fixe un délai, l'écrire ; sinon garder « pas de délai fixé » |
| Même sujet (certificat reçu après le CCF) | `data/examens/audit_faq_2026_10_12/d8_procedure_verifiee.txt` | Doit rester cohérent avec la fiche précédente |
| Formulaire et consignes d'inaptitude totale | `data/commun/audit60/inaptitude_totale_annee_terminale.txt` | Ligne 8 : « à revérifier pour la session actuelle » |
| Marche en durée adaptée (handicap, inaptitude partielle permanente sans CCF adapté) | `data/commun/audit355/aix_marche_adaptee.txt` | |
| Code ABS pour absence non justifiée au bac GT | `data/commun/audit355/aix_codes_absence_gt.txt` | |
| Pas de règle DI ni de neutralisation propre à Aix | `config/decisions_validees.json` (2 décisions) | Vérifier que le BA 2027 n'en crée pas |

## 3. CAP : trois épreuves organisées, deux retenues
| Point à relire | Fiche |
|---|---|
| « Si trois épreuves sont organisées, le candidat en retient deux en début d'année » (II.1.b.1, p. 5) | `data/examens/complement_reponses_validees.txt` |
| Même règle | `data/examens/fiches/memoire_examens_santorin_004_situation_regle_d_airain_des_champs_d_apprentissage_bac_pro_gt.txt` |
| Même règle | `config/decisions_validees.json` (décision « session 2026 (BA 549) ; à confirmer pour 2027 ») |

## 4. Conservation des éléments d'évaluation
| Point à relire | Fiche |
|---|---|
| Dossier accessible au chef d'établissement (p. 8) ; durée éventuelle | `data/commun/audit60/pv_ccf_prudence.txt` |
| Même sujet | `data/ipack/fiches/ipack_207_article_109_dossiers_dossier_certificatif_conservation_des_documents_d_evaluation_et_emarg.txt` |

## Après la mise à jour
- Remplacer le lien `BA549S/BASPE_549.pdf` par celui du nouveau BA dans chaque fiche modifiée, et mettre à jour `date_verification` dans `config/catalogue_documents.json`.
- Renommer les titres « session 2026 » qui deviennent « session 2027 ».
- Lancer `python3 -m unittest discover -s tests` (aucun test ne cite le BA 549 : ils ne bloqueront pas la mise à jour, mais vérifient le routage).
