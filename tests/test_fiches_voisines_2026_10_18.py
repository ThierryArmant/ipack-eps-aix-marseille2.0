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


if __name__ == '__main__':
    unittest.main()
