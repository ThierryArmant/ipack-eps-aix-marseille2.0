"""Corrections issues de l'audit en ligne du 12 octobre 2026 (D1, D8, E3, G3, pied de réponse)."""
import re
import unittest
from pathlib import Path

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'


def lire(p):
    return Path(p).read_text(encoding='utf-8')


class AuditEnLigneTests(unittest.TestCase):
    def test_d1_aucune_formule_negative_reprise_a_contresens(self):
        for p in ('data/commun/audit60/inaptitude_totale_annee_terminale.txt',
                  'data/examens/circuit_aix_ipack_cyclades_santorin.txt'):
            texte = lire(p)
            self.assertNotIn("ne faut pas le mettre dans un groupe", texte)
            self.assertNotIn("Ne pas le laisser sans groupe", texte)
        self.assertIn("OUI, il faut l’associer à son groupe et à un protocole",
                      lire('data/commun/audit60/inaptitude_totale_annee_terminale.txt'))

    def test_d8_certificat_tardif_sans_demande_de_precisions(self):
        self.assertEqual(kc.clarification("Le certificat médical est arrivé trois semaines après le CCF. On l'accepte ?", GT), '')
        self.assertTrue(kc.clarification("Il a un certificat médical pour le CCF, je mets DI ?", GT))
        self.assertIn("La règle des « 15 jours » est propre à l'académie de Lyon", lire('data/commun/audit60/aix_certificats_2026.txt'))

    def test_e3_ponctuel_terminal_si_deux_activites_impossibles(self):
        texte = lire('data/examens/complement_note_de_service_bac_gt_2026.txt')
        self.assertIn("AU MOINS DEUX activités impossibles", texte)
        self.assertIn("examen ponctuel terminal", texte)

    def test_g3_les_eleves_ne_viennent_pas_des_classes_ipackeps(self):
        texte = lire('data/ipack/complement_questions_boite_assistance.txt')
        self.assertNotIn("créer les classes directement dans la gestion des groupes", texte)
        self.assertIn("Les élèves ne passent pas par iPackEPS", texte)

    def test_no_generic_assistance_footer_is_appended_to_answers(self):
        src = lire('app.py')
        self.assertIn('footer_assistance = ""', src)
        self.assertNotIn("Bien entendu si ma réponse ne vous a pas aidé", src)
        self.assertNotIn("IA en apprentissage constant, je peux parfois trébucher", src)


if __name__ == '__main__':
    unittest.main()


class ApresConversionTests(unittest.TestCase):
    """Contrôles après la conversion des réponses en dur (EX091, EX106, EX115, EX116)."""

    def test_ex091_ex106_faits_donnes_ou_regle_generale_sans_demande_de_precisions(self):
        self.assertEqual(kc.clarification("Inapte sur deux épreuves, mon élève n'a qu'une note (14). Je saisis quoi : DI+DI+14 ou DI partout ?", GT), '')
        self.assertEqual(kc.clarification("Mon élève inapte peut faire l'AFL2 et l'AFL3 sans pratiquer. Je le note seulement là-dessus ?", GT), '')
        self.assertTrue(kc.clarification('Il est inapte : je saisis DI ou zéro ?', GT))
        self.assertTrue(kc.clarification('Un élève inapte sur une épreuve du CCF, quelle note finale ?', 'Lycée Pro / CAP'))

    def test_ex115_adaptation_temporaire_sans_validation_prealable(self):
        texte = kc.delivered_text("Entorse de la cheville : l'élève peut faire un badminton adapté. Faut-il un nouveau protocole validé par la commission avant de l'évaluer ?", GT, 'examens')
        self.assertIn('pas de nouvelle validation préalable', texte)
        self.assertIn("commission académique d’harmonisation et de proposition de notes (CAHPN)", lire('data/commun/audit60/gt_regles_decisives.txt'))

    def test_ex116_remise_tardive_distincte_d_un_certificat_etabli_apres(self):
        texte = lire('data/commun/audit60/aix_certificats_2026.txt')
        self.assertIn('la remise tardive ne suffit pas à le refuser', texte)
        self.assertIn("Le certificat a été établi après le CCF : il n'a pas d'effet rétroactif", texte)


class Lot4Tests(unittest.TestCase):
    """Retours du lot 4 (EX151-EX200) et contrôles EX091 / EX115."""
    SUFFIXE = " Distingue ce qui relève du texte national, d’une consigne académique et du fonctionnement du logiciel. Si un élément manque, précise lequel."

    def titres(self, q, public=GT):
        return kc.priority_titles(q, public, 'examens')

    def test_suffixe_national_academique_logiciel_ne_declenche_pas_la_fiche_protocoles(self):
        for q in ["Cyclades refuse mon protocole à cause d'une date.",
                  "Mes élèves apparaissent dans Cyclades mais sans protocole.",
                  "Entorse de la cheville : l'élève peut faire un badminton adapté. Faut-il un nouveau protocole validé par la commission avant de l'évaluer ?"]:
            self.assertNotIn('Aix-Marseille : protocoles et circuit EPS — 2026', ' '.join(self.titres(q + self.SUFFIXE)))

    def test_ex115_adaptation_temporaire_fiche_dediee_en_tete(self):
        q = "Entorse de la cheville : l'élève peut faire un badminton adapté. Faut-il un nouveau protocole validé par la commission avant de l'évaluer ?" + self.SUFFIXE
        self.assertIn('pas de nouvelle validation préalable', kc.delivered_text(q, GT, 'examens'))

    def test_ex091_deux_issues_presentees(self):
        texte = kc.delivered_text("Inapte sur deux épreuves, mon élève n'a qu'une note (14). Je saisis quoi : DI+DI+14 ou DI partout ?", GT, 'examens')
        self.assertIn('certification sur la seule épreuve', texte)
        self.assertIn('ne pas proposer de note', texte)
        self.assertIn("Aucune de ces issues n'est automatique", texte)

    def test_mauvais_lot_et_mauvais_groupe_ont_leur_fiche(self):
        self.assertIn('FAQ EPS — Santorin : élève dans le mauvais lot', self.titres("Un élève est dans le mauvais lot dans Santorin."))
        self.assertIn("FAQ EPS — Protocole Cyclades avec le mauvais groupe d'élèves",
                      self.titres("Je me suis trompé de groupe d'élèves dans un protocole Cyclades et le champ est grisé."))

    def test_element_manque_ne_declenche_pas_les_candidats_absents(self):
        q = "Nous sommes un lycée français à l'étranger : aucun élève dans iPackEPS. Comment nos élèves arrivent-ils dans Cyclades ?" + self.SUFFIXE
        self.assertNotIn('Cyclades : candidats absents de la liste', ' '.join(self.titres(q)))


class SujetsManquantsTests(unittest.TestCase):
    """Sujets ajoutés le 13 octobre après comparaison avec les FAQ d'autres académies."""

    def titres(self, q):
        return ' '.join(kc.priority_titles(q, GT, 'examens'))

    def test_shn_vingt_seule_note(self):
        self.assertIn('le 20/20 ne peut pas être la seule note', self.titres("Mon SHN est inapte sur deux épreuves, il n'a que son 20 : DI + DI + 20 ?"))

    def test_note_modifiee_apres_commission(self):
        self.assertIn('harmonisation, clôture et remontée', self.titres("Pourquoi la note de mes élèves a changé après la commission ?"))

    def test_eleve_parti_mais_pas_le_professeur(self):
        self.assertIn('toujours inscrit', self.titres("Un élève a quitté le lycée en cours d'année mais il est toujours inscrit au bac, que faire pour le CCF ?"))
        self.assertNotIn('toujours inscrit', self.titres("Notre professeure a quitté l'établissement après deux CCF, que deviennent les notes des élèves ?"))

    def test_sans_consigne_aix_le_dit(self):
        for q in ["Un élève arrive en retard au CCF, peut-il passer l'épreuve ?", "Peut-on donner leurs notes de CCF aux élèves ?"]:
            self.assertIn('sans consigne écrite trouvée', self.titres(q))
        self.assertIn('sans inventer de règle', kc.delivered_text("Un élève redouble la terminale, garde-t-il ses notes d'EPS ?", GT, 'examens'))


class Lot5Tests(unittest.TestCase):
    """Retours du lot 5 (EX201-EX250)."""

    def test_j3_cloturer_n_est_pas_deverrouiller(self):
        q = "Un collègue a oublié de clôturer son lot avant la date limite. Le chef peut-il le faire ?"
        texte = kc.delivered_text(q, GT, 'examens')
        self.assertIn('tous les candidats du lot doivent avoir une saisie', texte)
        self.assertIn('Ici le lot est ouvert : il s\'agit de le clôturer, pas de le déverrouiller.', texte)

    def test_j1_verrouiller_une_seule_fois(self):
        self.assertIn('une seule fois', kc.delivered_text("Dois-je verrouiller mon lot dès que j'ai saisi la note du premier CCF ?", GT, 'examens'))

    def test_j2_seul_le_chef_deverrouille(self):
        self.assertIn('L’enseignant ne peut pas déverrouiller son lot', kc.delivered_text("J'ai verrouillé mon lot par erreur et je dois corriger une note.", GT, 'examens'))

    def test_g3_hors_siecle_association_n_est_pas_inscription(self):
        texte = kc.delivered_text("Nous sommes un lycée français à l'étranger : aucun élève dans iPackEPS. Comment nos élèves arrivent-ils dans Cyclades ?", GT, 'examens')
        self.assertIn("Associer un candidat à un protocole n'est pas l'inscrire à l'examen", texte)

    def test_ex091_reponse_en_tete(self):
        texte = kc.delivered_text("Inapte sur deux épreuves, mon élève n'a qu'une note (14). Je saisis quoi : DI+DI+14 ou DI partout ?", GT, 'examens')
        self.assertIn('deux possibilités', texte.split('\n')[2])


class Lot6Tests(unittest.TestCase):
    """Retours du lot 6 (EX251-EX300)."""

    def texte(self, q, public=GT):
        return kc.delivered_text(q, public, 'examens')

    def test_option_dispense_non_en_tete(self):
        t = self.texte("Un candidat individuel peut-il présenter l’option EPS au baccalauréat et quelles sont les conditions si son EPS obligatoire est dispensée ?")
        self.assertIn("NON, il ne peut pas présenter l'option EPS", t)
        self.assertLess(t.index('NON, il ne peut pas'), t.index('Sinon, oui'))
        self.assertIn('MENE2533572N', t)

    def test_fraude_participation_maintenue_et_suspicion(self):
        t = self.texte("Lors d’un CCF du baccalauréat, je soupçonne une fraude en course d’orientation. Puis-je saisir immédiatement zéro dans Santorin ?")
        self.assertIn('sans interrompre la participation du candidat', t)
        self.assertIn('suspicion documentée', t)
        self.assertNotIn('Sorties : second degré', t)

    def test_codes_differe_avant_dispense(self):
        t = self.texte("Quelle différence entre « Absent » et « Dispense » dans Santorin ?")
        self.assertIn('On ne saisit pas « Dispensé » à ce stade', t)

    def test_shn_vingt_santorin_et_eligibilite(self):
        t = self.texte("Santorin ne me propose pas le 20/20 pour mon sportif de haut niveau.")
        self.assertIn('crayon', t)
        self.assertIn('ne se limite pas aux listes ministérielles', t)

    def test_aflp_bac_pro_et_candidature_invalide(self):
        self.assertIn('vaut pour tous les élèves du protocole', self.texte("Bac pro : les cases de notes sont grisées dans mon lot.", 'Lycée Pro / CAP'))
        self.assertIn('Ce n\'est pas une question de déverrouillage', self.texte("Impossible de verrouiller : « la candidature n'est plus valide dans le système d'information examens/concours »."))


class AcademieTests(unittest.TestCase):
    """Le hub contient des consignes d'Aix : un utilisateur d'une autre académie doit en être averti."""

    def test_note_vide_pour_aix_et_presente_pour_les_autres(self):
        import academie as a
        self.assertEqual(a.note_academie('Aix-Marseille'), '')
        n = a.note_academie('Créteil')
        self.assertIn("consigne de l'académie d'Aix-Marseille", n)
        self.assertIn("de l'académie de Créteil", n)
        self.assertIn('Nice', a.note_academie('Nice'))

    def test_assistance_et_inventaire(self):
        import academie as a
        self.assertEqual(a.adresse_assistance('Créteil'), 'ipackeps@ac-creteil.fr')
        self.assertEqual(a.adresse_assistance('Lyon'), '')
        self.assertIn('data/commun/audit60/aix_protocoles_2026.txt', a.FICHIERS_AIX)
        self.assertIn('Aix-Marseille : protocoles et circuit EPS — 2026', a.titres_aix(kc.catalog()))

    def test_selection_obligatoire_dans_l_interface(self):
        src = lire('app.py')
        self.assertIn('key="academie_utilisateur"', src)
        self.assertIn('Choisissez votre académie', src)


class Reprise11Tests(unittest.TestCase):
    """Reprise des 11 questions sur d2be361."""

    def test_shn_tardif_fiche_exclusive(self):
        q = "Un candidat au bac GT obtient son statut SHN après la clôture des inscriptions. Peut-on modifier ce statut et lui attribuer automatiquement 20 comme note finale EPS ? Explique les démarches dans l’ordre et qui doit intervenir."
        self.assertEqual(kc.priority_titles(q, GT, 'examens'), ['Bac GT : statut SHN obtenu après la clôture des inscriptions'])
        self.assertIn("ni aménagement à demander", kc.delivered_text(q, GT, 'examens'))

    def test_f6_pas_de_derogation_technique(self):
        self.assertIn('il ne modifie pas le logiciel', lire('data/examens/audit_faq_2026_10_12/f6_procedure_verifiee.txt'))

    def test_causes_a_verifier_et_ordre_des_codes(self):
        self.assertIn('vérifiez d’abord si l’AFL1 est saisie', lire('data/examens/audit_faq_2026_10_12/k2_procedure_verifiee.txt'))
        self.assertIn("Le certificat médical n'est pas exigé pour une force majeure", lire('data/examens/audit_faq_2026_10_12/k5_procedure_verifiee.txt'))
        self.assertIn('consigne manquante', lire('data/examens/fraude_ccf_eps.txt'))
