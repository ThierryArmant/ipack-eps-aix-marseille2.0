"""Corrections après la troisième mesure (17 octobre 2026). Formulations différentes de la série secrète."""
import unittest
from pathlib import Path

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
PRO = 'Lycée Pro / CAP'
CLG = 'Collège (DNB)'


def t(q, p=GT, m='examens'):
    return kc.priority_titles(q, p, m)


class CorrectionsMesure3(unittest.TestCase):
    def test_shn_ponctuel_a_sa_demande(self):
        s = 'Bac GT : SHN et examen ponctuel à sa demande (note 2026, 4.b)'
        self.assertIn(s, t("Ma joueuse est en pôle France, elle veut passer l'EPS en ponctuel : c'est possible ?"))
        self.assertNotIn('Bac GT ponctuel : publics et conditions de neutralisation',
                         t("Un sportif des collectifs nationaux peut-il demander le ponctuel plutôt que le CCF ?"))
        self.assertIn('il n\'a pas à prouver une impossibilité',
                      Path('data/examens/mesure3_corrections/gt_shn_ponctuel_a_sa_demande.txt').read_text(encoding='utf-8'))

    def test_bac_pro_inapte_une_epreuve_sur_trois(self):
        q = "Bac pro : mon élève est blessé pour une des trois activités, comment est calculée sa note ?"
        self.assertIn('Bac professionnel : inapte sur une épreuve, deux notes sur trois', t(q, PRO))
        self.assertNotIn('Bac professionnel : inaptitude et une seule évaluation', t(q, PRO))

    def test_fermeture_d_un_jour_rattrapage(self):
        texte = Path('data/examens/audit_lot3_2026_10_12/fermeture_collective.txt').read_text(encoding='utf-8')
        self.assertIn("fermeture d'un jour", texte)
        self.assertIn('date de rattrapage', texte)

    def test_reprise_programmation(self):
        q = "Peut-on récupérer la programmation de l'année dernière dans iPackEPS ?"
        r = t(q, CLG, 'ipack')
        self.assertIn('Reprendre la programmation : conservé et à actualiser', r)
        self.assertNotIn('Suppression : ne pas conclure à une restauration impossible', r)
        self.assertIn('Suppression : ne pas conclure à une restauration impossible',
                      t("J'ai supprimé ma programmation par erreur, peut-on la récupérer ?", CLG, 'ipack'))

    def test_groupe_general_technologique(self):
        g = 'iPackEPS : terminale générale et technologique dans le même groupe EPS (oui)'
        self.assertIn(g, t("J'ai des STMG et des élèves de la voie générale ensemble en EPS, un seul groupe ?", GT, 'ipack'))
        self.assertNotIn(g, t("Terminale pro et terminale générale dans le même groupe ?", GT, 'ipack'))

    def test_velo_premier_degre_et_orientation(self):
        velo = Path('data/commun/sorties_premier_degre.txt').read_text(encoding='utf-8')
        self.assertIn('ne suffit pas pour encadrer une activité à vélo', velo)
        co = Path('data/commun/audit355/co_securite_sortie.txt').read_text(encoding='utf-8')
        self.assertIn("ne prévoient pas d'autorisation générale de la mairie", co)

    def test_laicite_et_natation(self):
        lai = 'Laïcité en EPS : participation aux cours, signes et tenues, hygiène et sécurité'
        r = t("Une famille ne veut pas que sa fille aille à la piscine pour motif religieux : que dire ?", CLG, 'textes')
        self.assertIn(lai, r)
        self.assertNotIn('complement natation scolaire', r)
        self.assertNotIn(lai, t("Le professeur peut-il imposer une marque de tenue ?", CLG, 'textes'))

    def test_dnb_dispense_lsu_reponse_directe(self):
        texte = Path('data/examens/regles_dnb_eps.txt').read_text(encoding='utf-8')
        self.assertIn("saisir « Dispensé » pour l'EPS dans le LSU", texte)

    def test_fiches_examen_hors_onglet_textes(self):
        r = t("Un élève a une dispense d'EPS d'un mois : doit-il venir en cours ?", CLG, 'textes')
        self.assertFalse(any(x.startswith('DNB') for x in r), r)
        self.assertIn('DNB EPS : inaptitude, dispense, PAP, PAI et PPS',
                      t("En troisième, un élève est dispensé d'EPS toute l'année : que met-on dans le LSU ?", CLG, 'examens'))
        self.assertIn('Certificat d’inaptitude : rôle médical et rôle pédagogique',
                      t("Un élève a un certificat médical pour deux semaines : que fait-il en EPS ?", CLG, 'textes'))

    def test_controle_adapte_inaptitude_permanente_gt(self):
        s = 'Bac GT : contrôle adapté pour inaptitude partielle permanente ou handicap (note 2026, 2.e)'
        self.assertIn(s, t("Mon élève de première a un handicap moteur attesté : comment l'évaluer en CCF ?"))
        self.assertNotIn(s, t("Un élève totalement inapte toute l'année de terminale : note EPS au bac ?"))
        self.assertNotIn(s, t("Bac pro : élève en inaptitude partielle permanente, comment l'évaluer ?", PRO))
        texte = Path('data/examens/mesure3_corrections/gt_controle_adapte_inaptitude_permanente.txt').read_text(encoding='utf-8')
        self.assertIn('ou exceptionnellement une seule', texte)

    def test_protocole_porte_a_connaissance_familles(self):
        s = "Bac GT : protocole porté à la connaissance des élèves et familles (note 2026, 2.b)"
        self.assertIn(s, t("Faut-il informer les parents du protocole d'évaluation du bac en EPS ?"))
        self.assertNotIn(s, t("Comment déposer notre protocole dans iPackEPS ?", GT, 'ipack'))

    def test_envoi_dossier_bouton_grise(self):
        s = 'iPackEPS : envoi du dossier pour validation impossible (bouton grisé)'
        self.assertIn(s, t("Je n'arrive pas à envoyer le dossier pour validation, le bouton est grisé", GT, 'ipack'))
        self.assertNotIn(s, t("Le bouton Verrouiller est grisé dans Santorin", GT, 'ipack'))

    def test_presence_cours_inapte_et_video_textes(self):
        self.assertIn("Élève inapte ou dispensé : présence en cours d'EPS",
                      t("Mon élève a un certificat d'inaptitude de trois semaines, doit-il être présent en EPS ?", CLG, 'textes'))
        self.assertIn('Vidéo EPS : démarche institutionnelle et périmètre iPackEPS',
                      t("Ai-je le droit de filmer mes élèves en acrosport ?", CLG, 'textes'))


if __name__ == '__main__':
    unittest.main()
