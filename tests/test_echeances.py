import datetime
import unittest

import echeances as ec


class Rappels(unittest.TestCase):
    ITEMS = [dict(date='2026-11-12', _date=datetime.date(2026, 11, 12), heure='18 h', academie='Aix-Marseille',
                  texte='Clôture des inscriptions.', fiche='f.txt', fiche_revue=False)]

    def test_rappel_la_veille(self):
        r = ec.rappels(datetime.date(2026, 11, 11), None, self.ITEMS)
        self.assertEqual(len(r), 1)
        self.assertTrue(r[0]['libelle'].startswith('Demain (12 novembre 2026 à 18 h), Aix-Marseille'))

    def test_rappel_le_jour_meme(self):
        self.assertEqual(ec.rappels(datetime.date(2026, 11, 12), 'Aix-Marseille', self.ITEMS)[0]['quand'], "Aujourd'hui")

    def test_pas_de_rappel_avant_j_moins_1_ni_apres(self):
        self.assertEqual(ec.rappels(datetime.date(2026, 11, 10), None, self.ITEMS), [])
        self.assertEqual(ec.rappels(datetime.date(2026, 11, 13), None, self.ITEMS), [])

    def test_autre_academie_sans_rappel_d_aix(self):
        self.assertEqual(ec.rappels(datetime.date(2026, 11, 11), 'Lille', self.ITEMS), [])

    def test_echeance_passee_signalee_a_l_admin_tant_que_fiche_non_revue(self):
        self.assertEqual(len(ec.a_mettre_a_jour(datetime.date(2026, 11, 13), self.ITEMS)), 1)
        revue = [dict(self.ITEMS[0], fiche_revue=True)]
        self.assertEqual(ec.a_mettre_a_jour(datetime.date(2026, 11, 13), revue), [])

    def test_fichier_reel_lisible_et_fiches_existantes(self):
        from pathlib import Path
        items = ec.load()
        self.assertGreaterEqual(len(items), 5)
        for e in items:
            self.assertTrue(Path(e['fiche']).is_file(), e['fiche'])
