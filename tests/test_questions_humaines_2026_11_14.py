"""Questions réelles du 10 au 14 novembre 2026 : la réponse complète tient dans un seul passage."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import short_answer as sa
from knowledge_catalog import priority_titles

ACCES = Path('data/ipack/acces_ipackeps_problemes.txt')
PROJET_SSS = next(Path('data/ipack/fiches').glob('ipack_081_*'))
RECONDUCTION = next(Path('data/ipack/fiches').glob('ipack_083_*'))
PONCTUEL = Path('data/examens/eduscol_2026_10_17/gt_referentiel_ponctuel.txt')
CCF = Path('data/examens/eduscol_2026_10_17/gt_referentiel_ccf.txt')


def lignes(path):
    return [line for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


class Erreur404Tests(unittest.TestCase):
    QUESTION = ("Lorsque j'essaie de me connecter à ipack EPS, une page s'affiche avec pour information "
                "\"ressource non trouvée 404\". Comment puis-je faire pour résoudre ce problème ?")

    def test_fiche_acces_prioritaire(self):
        self.assertIn('Accès iPackEPS et portail ESTEREL', priority_titles(self.QUESTION, 'Collège (DNB)', 'ipack'))

    def test_les_trois_essais_dans_un_seul_passage(self):
        passage = [l for l in lignes(ACCES) if l.startswith('- Réponse directe — le lien iPackEPS existe')]
        self.assertEqual(len(passage), 1)
        for attendu in ('404', 'ressource non trouvée', 'changer de navigateur', 'vider le cache', '[Gérer mes favoris]'):
            self.assertIn(attendu, passage[0])

    def test_aucun_renvoi_sans_contenu(self):
        texte = ACCES.read_text(encoding='utf-8')
        self.assertNotIn('ci-dessous', texte)
        self.assertNotIn('suivre le diagnostic', texte)


class ProjetBilanSectionTests(unittest.TestCase):
    def test_cas_courant_avant_le_cas_annee_precedente(self):
        texte = PROJET_SSS.read_text(encoding='utf-8')
        direct = texte.index("Réponse directe — où rédiger le projet et le bilan")
        self.assertLess(direct, texte.index('Q3 :'))
        self.assertIn('[Projet Annuel SSS]', texte[direct:texte.index('- URL')])
        self.assertIn('[Bilan Annuel SSS]', texte[direct:texte.index('- URL')])
        self.assertIn("ce n'est pas la démarche pour le projet ou le bilan de l'année en cours", texte)

    def test_reconduction_adressee_au_chef_d_etablissement(self):
        passage = [l for l in lignes(RECONDUCTION) if l.startswith('- Réponse directe — renouveler une section sportive')]
        self.assertEqual(len(passage), 1)
        for attendu in ('[Évolution SSS]', 'signe ensuite électroniquement', '[Projet Annuel SSS]'):
            self.assertIn(attendu, passage[0])

    def test_proces_verbal_du_ca_dans_un_seul_passage(self):
        passage = [l for l in lignes(RECONDUCTION) if l.startswith("- Réponse directe — déposer le procès-verbal")]
        self.assertEqual(len(passage), 1)
        for attendu in ('[Évolution SSS]', 'ne confirme pas', "auprès de l'inspection"):
            self.assertIn(attendu, passage[0])


class PonctuelOuCcfTests(unittest.TestCase):
    def test_chaque_epreuve_du_ponctuel_se_nomme(self):
        for activite in ('demi-fond', 'danse', 'tennis de table'):
            with self.subTest(activite=activite):
                self.assertTrue(any(l.startswith('Examen ponctuel terminal, ' + activite) for l in lignes(PONCTUEL)))
        self.assertFalse(any(l.startswith(('Tennis de table :', 'Danse :', 'Demi-fond :')) for l in lignes(PONCTUEL)))

    def test_organiser_une_epreuve_au_bac_ouvre_le_ccf(self):
        question = 'Comment organiser les épreuves de tennis de table au bac ?'
        titres = priority_titles(question, 'Lycée Général & Techno', 'examens')
        self.assertTrue(any('CCF' in t for t in titres), titres)
        self.assertFalse(any('ponctuel' in t for t in titres), titres)
        self.assertTrue(any(l.startswith("Réponse directe — organiser l'épreuve d'une activité") for l in lignes(CCF)))

    def test_le_ponctuel_reste_ouvert_quand_il_est_demande(self):
        question = 'Quelles épreuves pour un candidat individuel au ponctuel du bac ?'
        self.assertTrue(any('ponctuel' in t for t in priority_titles(question, 'Lycée Général & Techno', 'examens')))


class NumeroArticleTests(unittest.TestCase):
    """Trace du 13 novembre : trois étapes justes refusées parce qu'elles commençaient par « [ARTICLE 94] »."""
    TITRE = "[ARTICLE 94] [Dossiers]/[Dossier SSS]/[Évolution] Demande de Reconduction ou Fermeture d'une SSS"
    PASSAGES = [(TITRE, "R1 : La reconduction se demande dans le module [Dossiers] / [Dossier SSS] / [Évolution] : vous y "
                        "choisissez « reconduction » pour l'année suivante, puis le chef d'établissement signe "
                        "électroniquement la demande (signature obligatoire).")]

    def reponse(self, phrases):
        vu = {}

        class Redacteur:
            def complete(self, prompt):
                vu['prompt'] = prompt
                return SimpleNamespace(text=json.dumps({'phrases': phrases}))
        audit = {}
        sa.short_answer(Redacteur(), tracer=lambda llm, a, stage: llm, audit=audit,
                        question='Comment renouveler la section sportive ?', passages=self.PASSAGES)
        return audit['short_answer'], vu['prompt']

    def test_etape_gardee_sans_le_numero_d_article(self):
        rapport, prompt = self.reponse([{
            'texte': "[ARTICLE 94] [Dossiers]/[Dossier SSS]/[Évolution] : faites signer électroniquement la demande "
                     "par le chef d'établissement (signature obligatoire).", 'passages': [1], 'etape': True}])
        self.assertEqual(rapport['rejected'], [])
        self.assertEqual(len(rapport['kept']), 1)
        self.assertNotIn('ARTICLE', rapport['kept'][0]['texte'])
        self.assertNotIn('[ARTICLE 94]', prompt)

    def test_un_menu_invente_reste_refuse(self):
        rapport, _ = self.reponse([{'texte': "[Dossier SSS] > [Renouvellement] : cochez la case.", 'passages': [1], 'etape': True}])
        self.assertEqual(rapport['kept'], [])
        self.assertTrue(any(r.startswith('menu:') for r in rapport['rejected'][0]['raisons']))


if __name__ == '__main__':
    unittest.main()
