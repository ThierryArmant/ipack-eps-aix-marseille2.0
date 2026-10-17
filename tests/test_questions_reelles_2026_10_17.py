"""Questions réelles relevées dans le journal du 13 au 17 octobre 2026 (autres académies comprises)."""
import unittest
from pathlib import Path

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
CLG = 'Collège (DNB)'
AJOUT = "iPackEPS : élève absent de la liste, comment l'ajouter"
PRONOTE = '[ARTICLE 88] [Dossiers]/[DossierEPS]/[Élèves] Import d’élèves depuis Pronote / École-Directe'
PONCTUEL = 'Bac GT ponctuel : publics et conditions de neutralisation'
EQUIPE = 'iPackEPS : actualisation de l’équipe EPS'


def titres(q, public=GT, mode='ipack'):
    return kc.priority_titles(q, public, mode)


class QuestionsReellesTests(unittest.TestCase):
    def test_ajout_manuel_d_un_eleve(self):
        self.assertIn(AJOUT, titres("ajouter un eleve manuellement"))
        self.assertIn(AJOUT, titres("Un nouvel élève n'apparaît pas dans ma classe, comment le rajouter ?", CLG))
        self.assertNotIn(AJOUT, titres("Élève arrivé en cours d'année absent de Santorin", GT, 'examens'))
        texte = Path('data/ipack/situations_2026_10_17/eleve_absent_liste_ajout.txt').read_text(encoding='utf-8')
        self.assertIn('[importation élèves] > [Actualiser]', texte)
        self.assertIn('ne décrivent pas de formulaire', texte)

    def test_import_pronote_sans_fiches_de_notes(self):
        t = titres("importer des eleves pronote")
        self.assertIn(PRONOTE, t)
        self.assertFalse(any('notes, moyennes' in x or 'PÉRIMÈTRE' in x for x in t), t)
        # Une question sur les notes garde la fiche de périmètre.
        self.assertIn('iPackEPS : notes, moyennes, résultats et sens des transferts',
                      titres("exporter mes notes ipack vers pronote"))

    def test_ponctuel_candidat_individuel_sans_fiche_ccf(self):
        t = titres("Un candidat individuel choisit-il librement trois activités pour son épreuve ponctuelle ?", GT, 'examens')
        self.assertIn(PONCTUEL, t)
        self.assertNotIn('Bac GT : CCF, activité établissement et harmonisation', t)

    def test_collegue_absent_de_l_equipe(self):
        self.assertIn(EQUIPE, titres("Un collègue n'apparaît pas dans la liste de l'équipe EPS"))

    def test_marque_de_tenue_formulation_des_collegues_acceptee(self):
        from documentary_review import mark_excerpt, source_packets, lexical_support_details
        p = 'data/textes/fiches/fournitures_neutralite_commerciale.txt'
        packet = source_packets(mark_excerpt(Path(p).read_text(encoding='utf-8'), path=p, title='t', priority=330))[0]
        for t in ("Le professeur ne peut pas demander aux familles d'acheter une tenue d'EPS d'une marque précise.",
                  "Non, le professeur ne peut pas imposer une marque de tenue aux familles."):
            self.assertTrue(any(lexical_support_details(t, [s['text']])['passed'] for s in packet['passages']), t)

    def test_centre_etranger_sans_eleves(self):
        t = "Aix-Marseille : établissement à l'étranger ou hors MEN — compte professeur, pas d'élèves, protocoles transférés par l'inspection"
        self.assertIn(t, titres("Lycée français à l'étranger : je ne peux pas actualiser mes classes et je n'ai pas l'onglet chef d'établissement."))
        self.assertIn(t, titres("Établissement AEFE : la saisie des protocoles est fermée dans Cyclades, comment faire ?", GT, 'examens'))
        self.assertNotIn(t, titres("Un élève étranger nouvellement arrivé n'apparaît pas dans ma classe"))
        self.assertNotIn(t, titres("Nous sommes un CFA, aucun apprenti n'apparaît dans iPackEPS"))
        texte = Path('data/ipack/courriels_aix_2026_10_14/etablissement_etranger_compte_professeur_sans_eleves.txt').read_text(encoding='utf-8')
        self.assertIn("c'est l'inspection qui transfère les protocoles", texte)
        self.assertNotIn('@', texte)
        q = ("Lycée français à l'étranger : je n'ai pas l'onglet chef d'établissement, Cyclades est fermé "
             "pour les protocoles et le dossier est à 100 % sans élèves.")
        self.assertEqual([t], titres(q, GT, 'examens'))

    def test_audit_declencheurs_17_octobre(self):
        cert = 'Certificat d’inaptitude : rôle médical et rôle pédagogique'
        self.assertNotIn(cert, titres("Le vérificateur me dit que je n’ai pas assez d’APSA certificatives"))
        self.assertIn(cert, titres("Mon élève a un certificat médical pour le CCF", GT, 'examens'))
        acces = 'Accès iPackEPS et portail ESTEREL'
        self.assertNotIn(acces, titres("Où déclarer mes installations sportives ?", CLG))
        self.assertNotIn(acces, titres("CAP : notre installation est inutilisable, comment organiser le CCF ?", 'Lycée Pro / CAP', 'examens'))
        self.assertIn(acces, titres("Je n'arrive pas à installer iPackEPS sur mon ordinateur"))
        sss = '### [SITUATION: SECTION SPORTIVE SCOLAIRE : PRATIQUE SUPPLEMENTAIRE ET EPS OBLIGATOIRE]'
        self.assertNotIn(sss, titres("Comment préparer les vœux SSS ?", CLG))
        self.assertIn(sss, titres("Un élève de section sportive est-il dispensé d'EPS ?", CLG, 'textes'))

    def test_synonymes_eleve_candidat_et_chef(self):
        from documentary_review import lexical_support
        self.assertTrue(lexical_support("Le principal autorise l'élève à passer l'épreuve différée.",
                                        ["Le chef d'établissement peut autoriser le candidat à une épreuve différée."]))

    def test_accident_scolaire_hors_questions_de_note(self):
        a = 'Accident scolaire : rapport et communication aux parents'
        pro = 'Lycée Pro / CAP'
        self.assertNotIn(a, titres("Bac pro : blessé avant la troisième épreuve, il a déjà deux notes. Quelle note finale ?", pro, 'examens'))
        self.assertNotIn(a, titres("Mon binôme est malade le jour du CCF, je note seul ?", GT, 'examens'))
        self.assertIn(a, titres("Un élève s'est blessé pendant le CCF : faut-il faire un rapport d'accident ?", GT, 'examens'))
        self.assertIn(a, titres("Un élève s'est blessé en cours, que dois-je faire ?", CLG, 'textes'))
        self.assertNotIn('complement natation scolaire',
                         titres("Piscine fermée pour toute la classe : natation non évaluée, Santorin ?", GT, 'examens'))

    def test_cap_circulaire_2025_fiches_prioritaires(self):
        pro = 'Lycée Pro / CAP'
        inst = 'CAP : installation fermée ou activité impossible — une seule activité sur autorisation du recteur'
        ref = 'CAP : notation du CCF par champ et épreuves du ponctuel (référentiel national)'
        self.assertIn(inst, titres("Les travaux bloquent cette installation : quelles possibilités pour le CAP ?", pro, 'examens'))
        self.assertIn(ref, titres("En CAP, comment sont répartis les 8 points au fil de la séquence ?", pro, 'examens'))
        self.assertIn(ref, titres("CAP : quelles épreuves au ponctuel pour un candidat libre ?", pro, 'examens'))
        t = titres("Bac pro : le gymnase est fermé, que faire pour la troisième activité ?", pro, 'examens')
        self.assertNotIn(inst, t)
        texte = Path('data/examens/cap_2026_10_17/cap_activite_impossible.txt').read_text(encoding='utf-8')
        self.assertIn('une seule activité au lieu des deux', texte)
        self.assertIn('ne pas transposer la procédure « Déclarer CE »', texte)

    def test_handicap_code_education_eduscol(self):
        h = "Handicap et inaptitude partielle en EPS aux examens : code de l'éducation (D. 312-4 à D. 312-6, D. 351-27)"
        self.assertIn(h, titres("Un élève en situation de handicap moteur peut-il passer une épreuve ponctuelle aménagée en EPS ?", GT, 'examens'))
        self.assertIn(h, titres("Quand faut-il faire la demande d'aménagement d'examen pour le bac ?", GT, 'examens'))
        self.assertNotIn(h, titres("Entorse de cheville : badminton adapté, protocole validé par commission avant évaluation ?", GT, 'examens'))
        texte = Path('data/examens/eduscol_2026_10_17/handicap_eps_code_education.txt').read_text(encoding='utf-8')
        self.assertIn('D. 312-4', texte)
        self.assertIn('une seule session', texte)


if __name__ == '__main__':
    unittest.main()
