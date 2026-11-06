"""Questions humaines des 5 et 6 novembre 2026 : sélection documentaire (sans appel d'IA)."""
import os
import unittest

import knowledge_catalog as kc

GT = 'Lycée Général & Techno'
PRO = 'Lycée Pro / CAP'
APSA = "iPackEPS lycée : APSA certificative et protocole d'un groupe"


class SelectionDocumentaire(unittest.TestCase):
    def test_apsa_cochees_message_moins_de_trois(self):
        for q in ("Les 3 APSA certificatives sont cochées pourtant c'est noté que je n'ai pas 3 APSA certificatives au LGT",
                  "Moins de 3 APSA déclarées certificatives alors que je l'ai coché"):
            t = kc.priority_titles(q, GT, 'ipack')
            self.assertEqual(APSA, t[0], (q, t))
            self.assertFalse(any('notes, moyennes' in x or 'PÉRIMÈTRE' in x for x in t), (q, t))

    def test_mot_note_reste_reconnu(self):
        self.assertTrue(any('notes, moyennes' in x for x in kc.priority_titles("Peut-on saisir une note dans iPackEPS ?", GT, 'ipack')))

    def test_certificatives_ne_declenche_pas_inaptitude(self):
        t = kc.priority_titles("Moins de 3 APSA déclarées certificatives alors que je l'ai coché", GT, 'ipack')
        self.assertFalse(any('inaptitude' in x.lower() for x in t), t)

    def test_post_bac_sans_eps(self):
        t = kc.priority_titles("Certaines classes ne sont pas configurées, ce sont des classes post bac qui n'ont pas d'EPS.", GT, 'ipack')
        self.assertTrue(t and 'post-bac' in t[0], t)

    def test_csv_enseignants(self):
        t = kc.priority_titles("Y a-t-il une vidéo pour importer le fichier CSV des enseignants ?", GT, 'ipack')
        self.assertTrue(t[0].startswith('[ARTICLE 13]'), t)
        self.assertFalse(any('Pronote' in x or 'FILMER' in x for x in t), t)

    def test_dispenses_examens(self):
        for mode in ('examens', 'textes'):
            t = kc.priority_titles("comment je gère les dispenses d'EPS aux examens", GT, mode)
            self.assertTrue(t and t[0].startswith("Dispense d'EPS aux examens"), (mode, t))

    def test_rgpd_droits(self):
        t = kc.priority_titles("Demande d'exercice des droits RGPD", GT, 'textes')
        self.assertTrue(any(x.startswith('RGPD : répondre') for x in t[:2]), t)

    def test_cas_a_preserver(self):
        self.assertIn(APSA, kc.priority_titles("Comment retirer une APSA qui n'est plus certificative ?", GT, 'ipack'))

    def test_pas_de_doublon_apsa(self):
        self.assertFalse(os.path.exists('data/ipack/situations_2026_11_06/apsa_deja_cochees_message_moins_de_trois.txt'))
        t = open('data/ipack/visite_lycee_2026_10_18/apsa_certificative_et_protocole_groupe_lycee_gt.txt', encoding='utf-8').read()
        self.assertIn('Ne pas faire recocher la case', t)


if __name__ == '__main__':
    unittest.main()


class QuestionsGsSuite(unittest.TestCase):
    def test_trop_d_apsa_bac_pro_et_cap(self):
        for q in ("J'ai 4 APSA certificatives, ce qui ne convient pas à iPackEPS qui m'indique \"Le protocole n'est pas complet : Il faut exactement 3 APSA certificatives\"",
                  "iPackEPS m'indique que j'ai moins de 2 APSAs déclarées certificatives en CAP, alors que ce n'est pas le cas. Que puis-je faire ?"):
            t = kc.priority_titles(q, PRO, 'ipack')
            self.assertTrue(t[0].startswith('[ARTICLE 17]'), (q, t))

    def test_greve_surveillance(self):
        t = kc.priority_titles("Mes AED sont en grève, puis-je surveiller seul cinq classes devant un film ?", GT, 'textes')
        self.assertIn('Grève et surveillance des élèves en collège et lycée', t)
