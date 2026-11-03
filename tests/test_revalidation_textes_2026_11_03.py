"""Revalidation des fiches Textes et nouvelles fiches du 3 novembre 2026."""
import glob
import unittest

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
CLG = 'Collège (DNB)'
PRO = 'Lycée Pro'
VP = "Bac professionnel et CAP : répartition des points entre AFLP (12 + 8) en CCF"
EQ = "Installations sportives de la commune : convention d'utilisation pour l'EPS (L. 214-4)"


def lire(motif):
    return open(glob.glob(motif)[0], encoding='utf-8').read()


class Routage(unittest.TestCase):
    def test_natation_second_degre(self):
        self.assertIn('complement natation scolaire', kc.priority_titles("Quelle surface d'eau par élève à la piscine ?", CLG, 'textes'))
        self.assertEqual([], kc.priority_titles("Le transport des élèves en car pour aller à la piscine : qui paie ?", CLG, 'textes'))

    def test_voie_pro(self):
        self.assertIn(VP, kc.priority_titles("En bac pro, comment sont répartis les points entre les AFLP ?", PRO, 'examens'))
        self.assertNotIn(VP, kc.priority_titles("Un élève de CAP se blesse après sa première épreuve. Peut-on le noter sur une seule activité ?", GT, 'examens'))
        self.assertNotIn(VP, kc.priority_titles("Santorin bloque la saisie de l'AFLP 3 en bac pro", PRO, 'examens'))

    def test_equipements(self):
        self.assertIn(EQ, kc.priority_titles("La mairie veut nous faire payer le gymnase, est-ce légal ?", PRO, 'textes'))


class Contenus(unittest.TestCase):
    def test_natation_second_degre_ecrit(self):
        t = lire('data/textes/complement_natation_scolaire.txt')
        self.assertIn('5 m²', t)
        self.assertNotIn('les passages du hub ne détaillent pas', t)

    def test_affirmations_retirees(self):
        self.assertNotIn('trapèze', lire('data/textes/fiches/base_textes_officiels_036_*.txt'))
        self.assertIn('Restituer', lire('data/textes/fiches/base_textes_officiels_035_*.txt'))
        self.assertNotIn('2016-178', lire('data/textes/partenariats_defense_citoyennete.txt'))
        self.assertIn('2016-103', lire('data/textes/partenariats_defense_citoyennete.txt'))
        self.assertIn('40 ans', lire('data/textes/fiches/base_textes_officiels_052_*.txt'))
        self.assertNotIn('MENE2009073C', lire('data/textes/complement_statuts_personnels_eps.txt'))
        self.assertNotIn('stéréotypes', lire('data/textes/fiches/base_textes_officiels_038_*.txt'))
        self.assertIn('DIEC', lire('data/textes/fiches/base_textes_officiels_055_*.txt'))
        self.assertNotIn('répartition universelle 7/5', lire('data/textes/fiches/base_textes_officiels_016_*.txt'))

    def test_statuts_revalides(self):
        import json
        c = json.load(open('config/catalogue_documents.json', encoding='utf-8'))
        restants = [k for k, v in c.items() if k.startswith('data/textes/') and 'non_revalid' in str(v.get('statut'))]
        self.assertEqual([], restants)


if __name__ == '__main__':
    unittest.main()


class RevueIpack(unittest.TestCase):
    def test_plus_de_consigne_interne_a_l_ia(self):
        import re
        for f in glob.glob('data/**/*.txt', recursive=True):
            if '/archives/' in f or 'ia_usages' in f:
                continue
            self.assertIsNone(re.search(r"\bL'IA (?:ne )?doit|pour l'IA|anti-hallucination", open(f, encoding='utf-8').read()), f)

    def test_une_seule_note_possible_bac_gt(self):
        t = lire('data/ipack/fiches/ipack_161_*.txt')
        self.assertNotIn('au moins DEUX notes', t)
        self.assertIn('une seule épreuve', t)

    def test_option_ponctuelle_candidat_individuel(self):
        self.assertNotIn('exclusivement réservées aux candidats libres', lire('data/ipack/fiches/ipack_153_*.txt'))

    def test_aucune_fiche_non_revalidee(self):
        import json
        c = json.load(open('config/catalogue_documents.json', encoding='utf-8'))
        self.assertEqual([], [k for k, v in c.items() if 'non_revalid' in str(v.get('statut'))])
