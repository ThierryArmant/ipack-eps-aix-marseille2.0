# Fiabilisation documentaire du HUB IA EPS — 10 octobre 2026

Le pourcentage initial de 70–80 % est une estimation de l'utilisateur, pas une mesure. Ce changement corrige des erreurs identifiées et vérifie le routage local ; il ne démontre pas une fiabilité globale de 90 %. Aucun nouvel appel au HUB ni à OpenAI n'a été effectué pendant cette correction. Les six essais publics antérieurs restent les seuls essais de réponses générées. Les index reconstruits par l'application peuvent entraîner des embeddings lors de son redémarrage.

## Corrections et recoupements officiels

| Point corrigé | Source normative | Deux recoupements consultés | Décision |
|---|---|---|---|
| DNB : LSU → Cyclades, absence et remplacement | [BO, note du 2 septembre 2025, §2.3–2.4](https://www.education.gouv.fr/bo/2025/Hebdo33/MENE2515977N) | [Mémento Éduscol](https://eduscol.education.gouv.fr/sites/default/files/document/memento-evaluer-les-eleves-de-3e-dans-le-cadre-des-nouvelles-modalites-d-attribution-du-diplome-national-du-brevet-123226.pdf) ; [recommandations IG EPS relayées par Lyon](https://eps.enseigne.ac-lyon.fr/spip/spip.php?article2015=) | Retirer l'exclusion générale de Cyclades. Distinguer CCF lycée et contrôle continu DNB ; conserver les recommandations trois APSA avec leur statut disciplinaire. |
| Encadrement secondaire et sortie mixte cycle 3 | [Circulaire du 16 juillet 2024, annexe](https://www.education.gouv.fr/bo/2024/Hebdo30/MENE2407159C) | [Guide Éduscol secondaire, décembre 2025, fiche 4](https://eduscol.education.gouv.fr/sites/default/files/document/guide-sorties-et-voyages-scolaires-second-degre-101619.pdf) ; [guide primaire, décembre 2025](https://eduscol.education.gouv.fr/sites/default/files/document/guide-sorties-et-voyages-scolaires-premier-degre-101622.pdf) | Retirer le ratio national inventé du secondaire. Séparer barème général et règles propres aux activités physiques. |
| Escalade : dernier contrôle et prévention du retour au sol | [Circulaire 2017-075, annexe](https://www.education.gouv.fr/bo/17/Hebdo16/MENE1711773C.htm) | [Éduscol escalade](https://eduscol.education.gouv.fr/6285/la-pratique-de-l-escalade-en-education-physique-et-sportive) ; [protocole Rennes, novembre 2017](https://pedagogie.ac-rennes.fr/sites/pedagogie.ac-rennes.fr/IMG/pdf/protocole_de_se_curite_escalade_academie_de_rennes_10.11.2017.pdf) | Ajouter les contrôles professoraux ; ne pas inférer l'autonomie d'un simple nombre de leçons. Rennes est un exemple académique, pas une prescription supplémentaire pour Aix. |
| Bac pro / BMA, session 2026 | [Circulaire du 2 avril 2025](https://www.education.gouv.fr/bo/2025/Hebdo18/MENE2505383C) | [Modification du 24 octobre 2025](https://www.education.gouv.fr/bo/2025/Hebdo44/MENE2526357C) ; [relais officiel Besançon](https://eps.ac-besancon.fr/voie-pro-evaluation-ccf-et-ponctuel-session-2026-et-apres/) | Actualiser les références et intégrer la possibilité d'adaptation en inaptitude partielle temporaire. Annexe nationale CCF également consultée. |
| CAP, session 2026 | [Circulaire du 27 août 2025](https://www.education.gouv.fr/bo/2025/Hebdo36/MENE2517122C) | [Modification du 24 octobre 2025](https://www.education.gouv.fr/bo/2025/Hebdo44/MENE2526679C) ; [relais officiel Besançon](https://eps.ac-besancon.fr/cap-evaluation-ccf-et-ponctuel-session-2026-et-apres/) | Archiver le texte 2020 remplacé ; distinguer CAP et bac pro. |
| Natation : référence 2017 remplacée | [Note du 28 février 2022, clause d'abrogation](https://www.education.gouv.fr/bo/22/Hebdo9/MENE2129643N.htm) | [Éduscol savoir-nager](https://eduscol.education.gouv.fr/5709/savoir-nager-en-securite-de-la-maternelle-au-lycee) ; [guide primaire, p.11](https://eduscol.education.gouv.fr/sites/default/files/document/guide-sorties-et-voyages-scolaires-premier-degre-101622.pdf) | Citer 2022 ; ne pas recycler les taux des sorties générales en natation. |

Ces recoupements ont des fonctions différentes : norme, modification, explicitation nationale ou déclinaison académique. Ce ne sont pas trois autorités indépendantes de même rang. Le BO et ses modifications restent déterminants. Certaines pages Aix-Marseille n'ont pas fourni un contenu exploitable à la lecture automatique ; aucune validation exhaustive du vademecum local n'est revendiquée.

## Classement

- Trois compilations réparties en 315 fichiers de fiches. Trois fiches contenant des directives de souveraineté ou des règles médicales générales douteuses sont placées dans `data/a_verifier` : 312 fiches de ces compilations restent actives.
- Les originaux sont conservés dans `data/archives/compilations`. Les copies strictement identiques ont une seule version canonique dans `data/commun`.
- Les textes autonomes CAP et bac pro de 2020 sont conservés dans `data/archives/textes_remplaces`. Deux synthèses mixtes fondées sur d'anciens référentiels restent dans `data/a_verifier` jusqu'à revalidation.
- Le document technique d'interfaçage 2024–2025 donne deux réponses contradictoires sur les droits d'export professeur/chef. Il est conservé dans `data/a_verifier` ; aucune des deux versions n'a été promue arbitrairement.
- Chaque source active est décrite dans `config/catalogue_documents.json` : titre, chemin, statut de vérification et portée du diplôme lorsqu'elle est explicite. Les synthèses restantes sont déclarées non revalidées, elles ne deviennent pas des textes officiels par leur nom de fichier.

## Recherche et réponse

Le chargeur est récursif, découpe toutes les bases en unités cohérentes, exclut archives et quarantaine et élimine les doublons exacts dans chaque index. Il conserve la provenance. Les portées explicites sont filtrées avant de limiter le nombre de résultats. Les fiches vérifiées pertinentes sont injectées avant les synthèses. Les questions d'examen/inaptitude dans les onglets techniques consultent aussi les textes.

Le garde-fou demande le diplôme lorsque « Lycée Pro / CAP » ne le précise pas, et les éléments médicaux manquants avant de choisir une note ou un code. Le raccourci médical en dur a été désactivé. Une recherche vide ou en erreur ne débouche plus sur une réponse affirmative du modèle. La substitution Santorin → LSU a été supprimée ; elle pouvait changer le sens d'une négation. Les sources récupérées sont affichables dans les trois onglets.

## Vérification et limites

`python -m py_compile app.py knowledge_catalog.py` et `python -m unittest discover -s tests -v` passent : 11 tests, sans réseau ni API. Les tests exécutent le vrai chargeur et le vrai routage de l'application avec des retrievers simulés ; ils couvrent les portées CAP/pro/GT/DNB, le groupe CM2–6e, l'escalade, les questions médicales ambiguës, l'archivage, les sources partagées et l'ordre filtre/limite.

Ils ne mesurent ni le classement vectoriel réel, ni la qualité des réponses générées, ni le démarrage complet sur Streamlit. Les autres règles contenues dans les centaines de fiches n'ont pas fait l'objet d'une revue juridique exhaustive. Les procédures techniques sans guide actuel restent à confirmer selon les habilitations et versions. La sortie mixte sportive nécessite encore les exigences de l'activité : le barème général seul n'autorise pas une séance de course d'orientation.

## Mesurer l'objectif de 90 %

Préparer trente cas indépendants : six déjà explorés, puis questions techniques, réglementaires, ambiguës et transversales. Une réponse correcte doit satisfaire ensemble le diplôme/session, la règle, le contexte, la source et la procédure. Compter une ambiguïté correctement reconnue comme réussie seulement si la précision demandée permet de poursuivre ; une abstention systématique n'est pas une bonne réponse. Objectif indicatif : au moins 27 réponses conformes sur 30, sans erreur critique sur sécurité ou statut médical. Ce résultat serait un score sur cet échantillon, pas une garantie générale. La poursuite de tests génératifs attend un nouveau budget ; aucune nouvelle série n'a été lancée ici.

## Complément de tests après publication

Quatre cas supplémentaires ont d'abord échoué, puis passent après correction : portée du diplôme conservée dans les métadonnées même quand un fragment perd son en-tête ; conservation de deux passages distincts ayant une introduction identique ; DNB explicitement demandé prioritaire sur une sélection « Lycée Pro / CAP » ; demande du type et de la durée d'inaptitude lorsqu'un seul de ces éléments est précisé. Le chargeur propage la portée de chaque fiche dans les métadonnées des fragments. La déduplication porte sur tout le passage, et non sur ses 300 premiers caractères.

La suite compte désormais 15 tests locaux réussis. Aucun nouveau test de réponse générée ni appel au chat n'a été lancé. Les questions et réponses d'essais déjà recueillies par l'utilisateur permettront de compléter cette suite avec les erreurs observées sur le terrain.
