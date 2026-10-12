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

    def test_pied_de_reponse_ipackeps_seulement_en_mode_ipack(self):
        src = lire('app.py')
        self.assertRegex(src, r'ipackeps@ac-aix-marseille\.fr</a>"\s*"</div>"\s*\) if mode == "ipack" else ""')


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
