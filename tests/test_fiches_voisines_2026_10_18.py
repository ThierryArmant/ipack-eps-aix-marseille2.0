"""Fiches voisines : une fiche ciblée ne doit pas se déclencher sur un mot pris dans un autre sens (18 octobre 2026)."""
import unittest

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
CLG = 'Collège (DNB)'


def t(q, p=GT, m='examens'):
    return kc.priority_titles(q, p, m)


class FichesVoisines(unittest.TestCase):
    def test_fiche_generale_gt_decoupee(self):
        self.assertIn("Bac GT : ensemble certificatif, listes d'activités et commission académique",
                      t("Combien d'activités peut compter la liste académique ?"))
        self.assertIn('Bac GT : absence prolongée du professeur et CCF',
                      t("Notre collègue est en arrêt depuis deux mois, nos terminales n'ont pas fait le cycle de CCF, que faire ?"))
        self.assertNotIn("Bac GT : ensemble certificatif, listes d'activités et commission académique",
                         t("Un élève blessé peut faire un badminton adapté, faut-il une validation ?"))

    def test_absence_longue_n_est_pas_co_evaluation(self):
        r = t("Notre collègue est en arrêt depuis deux mois, nos terminales n'ont pas fait le cycle de CCF, que faire ?")
        self.assertFalse(any('co-évaluateur absent' in x for x in r), r)
        self.assertTrue(any('co-évaluateur absent' in x for x in t("Mon binôme est malade le jour du CCF, je peux évaluer seul ?")))
        r = t("Mon binôme est malade le jour du CCF, je peux évaluer seul ?")
        self.assertFalse(any('inaptitude' in x.lower() for x in r), r)

    def test_accident_hors_cours_n_appelle_pas_le_rapport(self):
        r = t("Mon élève a eu un accident de ski pendant les vacances, il est inapte pour le CCF")
        self.assertNotIn('Accident scolaire : rapport et communication aux parents', r)
        self.assertIn('Accident scolaire : rapport et communication aux parents',
                      t("Un élève s'est blessé pendant le cours, que dois-je faire ?", CLG, 'textes'))

    def test_mots_larges(self):
        self.assertEqual([], t("Qui encadre l'AS le mercredi après-midi ?", CLG, 'textes'))
        self.assertEqual([], t("Le transport des élèves en car pour aller à la piscine : qui paie ?", CLG, 'textes'))
        self.assertEqual([], t("Le coordonnateur EPS doit-il faire la programmation de toute l'équipe ?", CLG, 'textes'))
        self.assertFalse(any('Sorties' in x for x in t("Je pars en voyage scolaire, qui me remplace pour le CCF ?")))
        self.assertIn('Transport d’élèves en véhicule personnel : recours exceptionnel et garanties',
                      t("Puis-je emmener des élèves dans ma voiture au cross ?", CLG, 'textes'))
        self.assertTrue(any('Sorties' in x for x in t("Faut-il une autorisation des parents pour une sortie scolaire à la journée ?", CLG, 'textes')))

    def test_fiches_textes_ouvrent_sur_une_reponse(self):
        from pathlib import Path
        import json, re
        cat = json.loads(Path('config/catalogue_documents.json').read_text(encoding='utf-8'))
        sans = []
        for p, md in cat.items():
            if md.get('prioritaire') and md.get('priorite', 0) >= 300 and md.get('modes') == ['textes'] and Path(p).is_file():
                lignes = [l for l in Path(p).read_text(encoding='utf-8').splitlines()
                          if l.strip() and not re.match(r'(###|\[PORTEE|Sigles|===)', l)]
                if lignes and lignes[0].startswith(('Nature de la source', 'Portée')):
                    sans.append(p)
        self.assertEqual([], sans)

    def test_arrete_1989_certificat(self):
        s = "Certificat d'inaptitude : contenu, durée, reprise et médecin scolaire (arrêté du 13 septembre 1989)"
        self.assertIn(s, t("Que doit indiquer le certificat médical d'inaptitude ?", CLG, 'textes'))
        self.assertIn(s, t("Mon élève est inapte depuis quatre mois, qui assure le suivi ?", CLG, 'textes'))
        self.assertIn(s, t("Puis-je demander qu'un élève soit examiné par le médecin scolaire ?", CLG, 'textes'))
        self.assertNotIn(s, t("Mon élève est inapte depuis quatre mois, quelle note au CCF ?"))
        from pathlib import Path
        texte = Path('data/textes/fiches/arrete_1989_certificat_inaptitude.txt').read_text(encoding='utf-8')
        self.assertIn('considéré apte à reprendre', texte)
        self.assertIn('abrogé depuis le 24 mai 2006', texte)

    def test_arret_long_fiche_exclusive(self):
        q = "Mon collègue est en arrêt depuis la Toussaint, mes terminales n'ont pas fait leur deuxième CCF : que faire ?"
        texte = kc.priority_context(q, GT, 'examens')
        self.assertIn('absence prolongée du professeur', texte)
        self.assertNotIn('co-évaluateur absent le jour du CCF', texte)

    def test_zero_disciplinaire_college_sans_fait_d_absence(self):
        from pathlib import Path
        code = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('comportement|refus|bavard|insolen|tenue|sanction|punition|discipl|travaill', code)

    def test_reprises_du_18_octobre(self):
        q = ("Un élève s'est blessé lors d'un déplacement vers une installation sportive municipale. Qui doit passer "
             "l'appel téléphonique aux parents et quel est le délai de transmission du rapport d'accident ?")
        r = t(q, CLG, 'textes')
        self.assertIn('Accident scolaire : rapport et communication aux parents', r)
        self.assertFalse(any('arrêté du 13 septembre 1989' in x for x in r), r)
        q = ("Notre protocole validé par la commission : à cause de travaux au gymnase, nous devons remplacer "
             "le volley-ball par le badminton. Quelle procédure, faut-il refaire signer les familles ?")
        self.assertEqual(["Remplacer une activité d'un protocole validé par une autre (travaux, installation indisponible)"], t(q))
        self.assertIn('Installation fermée pour une classe : autorisation puis CE',
                      t("La piscine est fermée pour toute la classe, l'évaluation de natation est impossible, que faire dans Santorin ?"))
        self.assertIn("Obligations de service des professeurs d'EPS (décret n° 2014-940)",
                      t("Je suis TZR sur deux établissements, qui fixe mon emploi du temps ?", CLG, 'textes'))
        from pathlib import Path
        code = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('Question de REMPLACEMENT', code)

    def test_tzr_decret_99_823(self):
        s = 'TZR : zone, rattachement, emploi du temps, service et heures (décret n° 99-823, note n° 99-152)'
        self.assertIn(s, t("Entre deux remplacements, que doit faire un TZR ?", CLG, 'textes'))
        self.assertIn(s, t("Je suis TZR, mes heures au-delà de mon service sont-elles payées ?", CLG, 'textes'))
        from pathlib import Path
        texte = Path('data/textes/fiches/tzr_decret_99_823_remplacement.txt').read_text(encoding='utf-8')
        self.assertIn("service inscrit à l'emploi du temps de l'agent remplacé", texte)
        self.assertIn("chef de l'établissement de rattachement qui définit son service", texte)
        self.assertIn("le hub ne contient pas le texte de l'ISSR", texte)
        obl = Path('data/textes/complement_obligations_service_eps.txt').read_text(encoding='utf-8')
        self.assertIn("réduit d'une heure", obl)
        self.assertNotIn("ne prévoient pas de pondération", obl)

    def test_questions_a_l_aveugle_18_octobre(self):
        from pathlib import Path
        r = t("Le coordonnateur est absent : le principal peut-il valider seul les grilles de CCF du DNB et les téléverser dans Santorin ?", CLG)
        self.assertIn("DNB : qui valide les notes d'EPS de troisième (conseil de classe, LSU), pas de grilles dans Santorin", r)
        r = t("Formateur académique, mes heures de formation hors de mon établissement de rattachement sont-elles des heures supplémentaires ?", GT, 'textes')
        self.assertIn("Obligations de service des professeurs d'EPS (décret n° 2014-940)", r)
        self.assertFalse(any(x.startswith('TZR') for x in r), r)
        r = t("La note de service impose 48 heures pour remettre un certificat médical, mon proviseur refuse la dispense : recours ?", GT, 'textes')
        self.assertIn("Certificat d'inaptitude : contenu, durée, reprise et médecin scolaire (arrêté du 13 septembre 1989)", r)
        self.assertIn('Laïcité en EPS : participation aux cours, signes et tenues, hygiène et sécurité',
                      t("Un élève veut faire EPS en survêtement ample pour motif religieux, le règlement intérieur l'interdit aux agrès", CLG, 'textes'))
        lai = Path('data/textes/fiches/base_textes_officiels_004_situation_3e_section_valeurs_de_la_republique_laicite_et_scolarisation_inclusive.txt').read_text(encoding='utf-8')
        self.assertIn('ne pas exclure seul', lai)
        self.assertNotIn('exclusivement à deux exigences', lai)
        self.assertIn('aucune règle nationale des 48 heures', Path('data/textes/fiches/arrete_1989_certificat_inaptitude.txt').read_text(encoding='utf-8'))
        self.assertIn('ne pas conclure à une obligation', Path('data/textes/fiches/tzr_decret_99_823_remplacement.txt').read_text(encoding='utf-8'))
        self.assertIn('if mode == "textes" and demande_precision.startswith', Path('app.py').read_text(encoding='utf-8'))

    def test_premisse_et_objet_non_couvert_dans_la_consigne(self):
        from pathlib import Path
        code = Path('documentary_review.py').read_text(encoding='utf-8')
        self.assertIn('PRÉMISSE DE LA QUESTION — règle prioritaire', code)
        self.assertIn('OBJET NON COUVERT — règle prioritaire', code)
        from documentary_review import render_exam_fallback, source_packets, mark_excerpt
        audit = {'documents': source_packets(mark_excerpt("L'appel et les absences se saisissent dans Pronote.", title='Appel'))}
        r = render_exam_fallback(audit, question="Notre gymnase apparaît sous son ancienne appellation dans le module équipements", mode='ipack')
        self.assertNotIn('Pronote', r)

    def test_corrections_serie_realiste(self):
        from pathlib import Path
        from documentary_review import lycee_dnb_mismatch
        self.assertFalse(any('Remplacer une activité' in x for x in t(
            "Un élève rate la dernière épreuve de CCF pour un stage obligatoire validé par le lycée : note de remplacement ?")))
        nat = Path('data/textes/complement_natation_scolaire.txt').read_text(encoding='utf-8')
        self.assertIn("ne s'applique pas au collège ni au lycée", nat)
        self.assertIn("oui, les 3 heures d'AS sont dues", Path('data/textes/complement_obligations_service_eps.txt').read_text(encoding='utf-8'))
        dnb = {'origin': 'document', 'text': '[PORTEE: dnb] LSU : saisir Dispensé.'}
        self.assertTrue(lycee_dnb_mismatch('Que mettre dans le LSU pour une élève dispensée ?', GT, dnb))
        self.assertFalse(lycee_dnb_mismatch('Que mettre dans le LSU au DNB ?', GT, dnb))
        self.assertFalse(lycee_dnb_mismatch('Que mettre dans le LSU ?', CLG, dnb))

    def test_elements_absents_des_sources(self):
        from documentary_review import absent_terms, absent_terms_notice
        P = [{'title': 'Santorin', 'text': "Choisir AFLP. Verrouiller le lot. Projet EPS déposé en PDF. TZR."}]
        self.assertEqual(['« incohérence grille groupe »'], absent_terms('message rouge “incohérence grille groupe”', P))
        self.assertEqual(['DHG'], absent_terms('incompatibilité avec la DHG', P))
        self.assertEqual(['PDF/A'], absent_terms('format PDF/A obligatoire ?', P))
        self.assertEqual([], absent_terms('URGENT ! un TZR et le bouton "Verrouiller le lot"', P))
        self.assertIn('ne mentionnent pas', absent_terms_notice(['DHG']))

    def test_absence_eleve_sans_fiche_absence_professeur(self):
        from documentary_review import situation_mismatch
        titre = 'Bac GT : absence prolongée du professeur et CCF'
        self.assertTrue(situation_mismatch("Mon élève a été absent au deuxième CCF pour un enterrement, peut-il rattraper ?", titre))
        self.assertFalse(situation_mismatch("Notre collègue est en arrêt depuis deux mois, que faire pour le CCF ?", titre))


if __name__ == '__main__':
    unittest.main()
