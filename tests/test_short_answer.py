"""Réponse courte : rédigée à partir des seuls extraits retenus, contrôlée phrase par phrase."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from generation_runtime import load_runtime
import short_answer as sa


def _llm(*outputs):
    llm = Mock()
    llm.complete.side_effect = [SimpleNamespace(text=o if isinstance(o, str) else json.dumps(o)) for o in outputs]
    return llm


PASSAGES = [('Réaffecter un lot', "Dans Santorin, le suivi des lots permet au chef d'établissement de réaffecter un lot à un autre examinateur."),
            ('Réaffecter un lot', "Le nouvel enseignant doit avoir une mission d'évaluation EPS dans Imag'in.")]


class ControlesPhrases(unittest.TestCase):
    def run_sa(self, phrases):
        audit = {}
        out = sa.short_answer(_llm({'phrases': phrases}), tracer=lambda llm, a, stage: llm,
                              audit=audit, question='Comment réaffecter un lot ?', passages=PASSAGES)
        return out, audit['short_answer']

    def test_phrase_appuyee_conservee_avec_ses_numeros(self):
        out, rep = self.run_sa([{'texte': "Demandez au chef d'établissement de réaffecter le lot dans le suivi des lots de Santorin.", 'passages': [1]},
                                {'texte': "Le nouvel enseignant doit avoir sa mission dans Imag'in.", 'passages': [2]}])
        self.assertEqual(rep['status'], 'rendered')
        self.assertIn('<sup>1</sup>', out)
        self.assertIn('<sup>2</sup>', out)

    def test_interlocuteur_menu_nombre_inventes_retires(self):
        out, rep = self.run_sa([{'texte': 'Contactez la DEC.', 'passages': [1]},
                                {'texte': 'Allez dans [Lots] > [Réaffecter].', 'passages': [1]},
                                {'texte': 'Vous avez 15 jours.', 'passages': [2]},
                                {'texte': "Le nouvel enseignant doit avoir sa mission dans Imag'in.", 'passages': [2]}])
        self.assertEqual([r['texte'] for r in rep['rejected']], ['Contactez la DEC.', 'Allez dans [Lots] > [Réaffecter].', 'Vous avez 15 jours.'])
        self.assertNotIn('DEC', out)
        self.assertIn("Imag&#x27;in", out)

    def test_renvoi_ecrit_dans_la_phrase_retire_et_non_pris_pour_un_nombre(self):
        out, rep = self.run_sa([{'texte': "Le nouvel enseignant doit avoir sa mission dans Imag'in (2).", 'passages': [2]}])
        self.assertEqual(rep['status'], 'rendered')
        self.assertNotIn('(2)', out)

    def test_renvoi_discordant_ou_nombre_metier_toujours_controle(self):
        out, rep = self.run_sa([{'texte': "Le nouvel enseignant doit avoir sa mission dans Imag'in (3).", 'passages': [2]},
                                {'texte': "Réaffectez le lot sous 15 jours.", 'passages': [1]}])
        self.assertEqual(rep['status'], 'nothing_kept')
        self.assertEqual([r['raisons'] for r in rep['rejected']], [['nombre:3'], ['nombre:15']])

    def test_numero_absent_ou_hors_liste_refuse(self):
        out, rep = self.run_sa([{'texte': 'Phrase sans source.', 'passages': []},
                                {'texte': 'Autre.', 'passages': [9]}])
        self.assertEqual(out, '')
        self.assertEqual(rep['status'], 'nothing_kept')

    def test_json_invalide_sans_relance(self):
        audit = {}
        llm = _llm('pas du json')
        out = sa.short_answer(llm, tracer=lambda l, a, stage: l, audit=audit, question='q', passages=PASSAGES)
        self.assertEqual(out, '')
        self.assertEqual(audit['short_answer']['status'], 'invalid_no_retry')
        llm.complete.assert_called_once()


class Integration(unittest.TestCase):
    def setUp(self):
        self.rt = load_runtime()
        dr = self.rt.documentary_review
        self.docs = dr.mark_excerpt("Dans Santorin, le suivi des lots permet au chef d'établissement de réaffecter un lot à un autre examinateur.",
                                    path='data/exemple.txt', title='Réaffecter un lot')

    def answer(self, llm, synthesis):
        audit = {}
        out = self.rt.exact_source_answer.exact_answer(llm, reviewer=self.rt.documentary_review,
            tracer=lambda l, a, stage: l, documents=self.docs, question='Comment réaffecter un lot ?',
            public='Lycée Général & Techno', mode='examens', academy='Aix-Marseille', audit=audit, synthesis=synthesis)
        return out, audit

    def selection(self):
        dr = self.rt.documentary_review
        pid = dr.source_packets(self.docs)[0]['passages'][-1]['id']
        return {'principal': 'D1', 'complements': [], 'passages': [pid]}

    def test_reponse_courte_en_tete_et_extraits_replies(self):
        llm = _llm(self.selection(), {'phrases': [{'texte': "Le chef d'établissement réaffecte le lot dans le suivi des lots de Santorin.", 'passages': [1]}]})
        out, audit = self.answer(llm, True)
        self.assertEqual(llm.complete.call_count, 2)
        self.assertLess(out.index('réaffecte le lot'), out.index('<details>'))
        self.assertIn('Voir les extraits des fiches (1)', out)
        self.assertIn('<strong>1.</strong>', out)

    def test_echec_de_la_reponse_courte_garde_les_extraits(self):
        llm = _llm(self.selection(), {'phrases': [{'texte': 'Contactez la DEC.', 'passages': [1]}]})
        out, audit = self.answer(llm, True)
        self.assertNotIn('Voir les extraits des fiches', out)
        self.assertIn('suivi des lots', out)

    def test_sans_option_un_seul_appel(self):
        llm = _llm(self.selection())
        self.answer(llm, False)
        llm.complete.assert_called_once()


class GardeFousDeSens(unittest.TestCase):
    """Le sens de la source (incertitude, interdiction, portée) ne peut pas être transformé."""
    def test_incertitude_transformee_en_interdiction_refusee(self):
        src = ("La description de la demande ne suffit pas à confirmer la possibilité de joindre les pièces "
               "dans le même module. Le lieu et le mode de transmission restent à vérifier.")
        self.assertIn('modalite:incertitude_effacee', sa.unsupported("Les pièces ne peuvent pas être jointes dans ce module.", src))
        self.assertIn('modalite:interdiction_ajoutee', sa.unsupported("Les pièces ne peuvent pas être jointes dans ce module.", src))
        self.assertEqual(sa.unsupported("La possibilité de joindre les pièces dans ce module n'est pas confirmée : vérifiez le lieu et le mode de transmission.", src), [])

    def test_vraie_interdiction_de_la_source_conservee(self):
        src = "Dans Cyclades, le champ « groupe élève » d'un protocole n'est plus modifiable une fois le protocole créé."
        self.assertEqual(sa.unsupported("Une fois le protocole créé, le champ « groupe élève » ne peut plus être modifié.", src), [])

    def test_consequence_inventee_refusee(self):
        src = "Il faut au préalable déclarer l'APSA dans [Dossiers] / [Dossier EPS] / [APSA]."
        self.assertIn('modalite:consequence_ajoutee',
                      sa.unsupported("Déclarez d'abord l'APSA, sinon la demande ne s'affichera pas.", src))

    def test_consequence_presente_dans_la_source_conservee(self):
        src = "Le chef d'établissement met à jour l'inscription, sinon contacter la DEC de son académie."
        self.assertNotIn('modalite:consequence_ajoutee',
                         sa.unsupported("Le chef d'établissement met à jour l'inscription, sinon il contacte la DEC.", src))

    def test_consigne_academique_garde_son_academie(self):
        src = "À Aix-Marseille, ne pas demander d'invalidation : prévenir l'inspection pédagogique au préalable."
        self.assertIn('portee:aix-marseille', sa.unsupported("Prévenez l'inspection pédagogique au préalable.", src))
        self.assertEqual(sa.unsupported("À Aix-Marseille, prévenez l'inspection pédagogique au préalable.", src), [])


class ConditionsEtCouverture(unittest.TestCase):
    BRANCHE = ("- Si les protocoles sont déjà validés, la suppression directe n'est plus possible. À Aix-Marseille, "
               "créer le protocole corrigé dans iPackEPS ([Dossiers] > [Dossier Certificatif]) et prévenir l'inspection pédagogique au préalable.")

    def test_trait_d_union_insecable_vaut_trait_d_union(self):
        phrase = "Si les protocoles sont déjà validés, à Aix\u2011Marseille, créez le protocole corrigé dans iPackEPS ([Dossiers] > [Dossier Certificatif]) et prévenez l'inspection pédagogique au préalable."
        self.assertEqual(sa.unsupported(phrase, self.BRANCHE), [])

    def test_condition_de_la_branche_perdue_refusee(self):
        phrase = "À Aix-Marseille, créez le protocole corrigé dans iPackEPS ([Dossiers] > [Dossier Certificatif]) et prévenez l'inspection pédagogique au préalable."
        self.assertEqual(sa.unsupported(phrase, self.BRANCHE), ['modalite:condition_perdue'])

    def test_vraie_omission_d_academie_toujours_refusee(self):
        phrase = "Si les protocoles sont déjà validés, prévenez l'inspection pédagogique au préalable."
        self.assertIn('portee:aix-marseille', sa.unsupported(phrase, self.BRANCHE))

    def test_extrait_non_repris_n_est_plus_affiche(self):
        # Décision de l'utilisateur (26/10/2026) : pas d'« autres cas » non demandés sous la réponse.
        rt = load_runtime(); dr = rt.documentary_review
        docs = dr.mark_excerpt("Le champ est grisé : c'est normal.\n\nSi quelques élèves sont mal placés : ne rien supprimer.",
                               path='data/exemple.txt', title='Mauvais groupe')
        ids = [s['id'] for s in dr.source_packets(docs)[0]['passages']][-2:]
        llm = _llm({'principal': 'D1', 'complements': [], 'passages': ids},
                   {'phrases': [{'texte': "Le champ grisé est normal.", 'passages': [1]}]})
        audit = {}
        out = rt.exact_source_answer.exact_answer(llm, reviewer=dr, tracer=lambda l, a, stage: l, documents=docs,
            question='Mauvais groupe', public='Lycée Général & Techno', mode='examens', academy='Aix-Marseille',
            audit=audit, synthesis=True)
        self.assertEqual(audit['short_answer']['uncited_passages'], [2])
        self.assertNotIn('Autres cas', out)
        self.assertNotIn('mal placés', out.split('Consulter les passages complets')[0])
        self.assertIn('Voir les extraits des fiches (1)', out)


class PhraseTropLongue(unittest.TestCase):
    def test_phrase_qui_enchaine_les_cas_est_coupee_puis_controlee(self):
        cas = ("Si tout le groupe est faux et que le protocole n'est pas validé, il faut supprimer le protocole puis le recréer avec le bon groupe, "
               "en vérifiant ensuite que chaque élève apparaît bien dans le nouveau protocole")
        phrase = cas + " ; si seuls quelques élèves sont mal placés, il ne faut rien supprimer et il faut ouvrir le menu [EPS] > [Associer les élèves à un protocole] pour les replacer."
        self.assertGreater(len(phrase), sa.MAX_CHARS)
        parts = sa._split_long([{'texte': phrase, 'passages': [1]}])
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[1]['texte'].startswith('Si seuls quelques élèves'))

    def test_phrase_longue_sans_coupure_possible_reste_refusee(self):
        phrase = 'x' * (sa.MAX_CHARS + 10)
        self.assertEqual(sa._split_long([{'texte': phrase, 'passages': [1]}])[0]['texte'], phrase)


class ObjetEtRenvoisNommes(unittest.TestCase):
    def test_renvoi_passage_n_retire(self):
        out, rep = ControlesPhrases.run_sa(ControlesPhrases(), [{'texte': "Le nouvel enseignant doit avoir sa mission dans Imag'in (passage 2).", 'passages': [2]}])
        self.assertEqual(rep['status'], 'rendered')
        self.assertNotIn('passage 2', out)

    def test_regle_appliquee_a_un_autre_document_refusee(self):
        src = "Trop peu d'éléments pour noter : ne pas proposer de note et mentionner « dispensé de l'épreuve d'EPS »."
        self.assertIn('objet:\\bbulletins?\\b', sa.unsupported("Ne proposez pas de note et indiquez « dispensé de l'épreuve d'EPS » sur le bulletin.", src))
        self.assertEqual(sa.unsupported("Ne proposez pas de note et indiquez « dispensé de l'épreuve d'EPS ».", src), [])


class PoolCommun(unittest.TestCase):
    """Pool commun Mini/Albert : identifiants stables, récupération, portée diplôme et académie."""
    POOL = [
        dict(id='D1P1', section='Contacts', texte="Bug iPackEPS non résolu : le correspondant académique iPackEPS ; à Aix-Marseille : ipackeps@ac-aix-marseille.fr.",
             portee={'academie': 'Aix-Marseille'}, propose_par_mini=True),
        dict(id='D1P2', section='Contacts', texte="Dans une autre académie, s'adresser au correspondant académique iPackEPS de son académie.",
             portee={}, propose_par_mini=False),
        dict(id='D2P1', section='Co-évaluation GT', texte="Au bac GT, la co-évaluation est réalisée par deux enseignants d'EPS.",
             portee={'examens': ['gt']}, propose_par_mini=True),
    ]

    def run_pool(self, phrases, public='Lycée Général & Techno', academy='Paris'):
        audit = {}
        out = sa.short_answer(_llm({'phrases': phrases}), tracer=lambda l, a, stage: l, audit=audit,
                              question='Qui contacter ?', passages=self.POOL, public=public, academy=academy)
        return out, audit['short_answer']

    def test_identifiants_du_pool_et_recuperation_tracee(self):
        out, rep = self.run_pool([{'texte': "Adressez-vous au correspondant académique iPackEPS de votre académie.", 'passages': ['D1P2']}])
        self.assertEqual(rep['status'], 'rendered')
        self.assertEqual(rep['kept'][0]['ids'], ['D1P2'])
        self.assertEqual(rep['kept'][0]['recupere_du_pool'], ['D1P2'])

    def test_consigne_d_une_autre_academie_refusee(self):
        out, rep = self.run_pool([{'texte': "À Aix-Marseille, écrivez à ipackeps@ac-aix-marseille.fr.", 'passages': ['D1P1']}])
        self.assertIn('portee:autre_academie', rep['rejected'][0]['raisons'])
        out, rep = self.run_pool([{'texte': "À Aix-Marseille, écrivez à ipackeps@ac-aix-marseille.fr.", 'passages': ['D1P1']}], academy='Aix-Marseille')
        self.assertEqual(rep['status'], 'rendered')

    def test_regle_d_un_autre_diplome_refusee(self):
        phrase = [{'texte': "Au bac GT, la co-évaluation est réalisée par deux enseignants d'EPS.", 'passages': ['D2P1']}]
        out, rep = self.run_pool(phrase, public='Lycée Pro / CAP')
        self.assertIn('portee:autre_diplome', rep['rejected'][0]['raisons'])
        out, rep = self.run_pool(phrase, public='Lycée Général & Techno')
        self.assertEqual(rep['status'], 'rendered')

    def test_identifiant_inconnu_et_renvoi_ecrit(self):
        out, rep = self.run_pool([{'texte': 'Phrase.', 'passages': ['D9P9']},
                                  {'texte': "Adressez-vous au correspondant académique iPackEPS de votre académie (D1P2).", 'passages': ['D1P2']}])
        self.assertEqual(rep['rejected'][0]['raisons'], ['forme'])
        self.assertNotIn('(D1P2)', out)

    def test_consigne_mentionne_la_proposition_mini_et_les_identifiants(self):
        prompt = sa.build_prompt('q', self.POOL, {'public': 'Lycée Général & Techno', 'academie': 'Paris'})
        self.assertIn('"propose_par_mini": false', prompt)
        self.assertIn('"D1P3"', prompt)
        self.assertIn('"academie": "Paris"', prompt)


class EnumerationInfinitifs(unittest.TestCase):
    def test_liste_de_gestes_a_l_infinitif_coupee(self):
        t = ("Adapter l'épreuve si l'inaptitude est partielle, renvoyer le candidat à une évaluation différée si l'inaptitude l'empêche de terminer, "
             "permettre une certification sur deux épreuves si la troisième est impossible, permettre une certification sur une seule épreuve si deux sont impossibles, "
             "ne pas formuler de proposition de note si les éléments sont trop réduits.")
        self.assertGreater(len(t), sa.MAX_CHARS)
        parts = sa._split_long([{'texte': t, 'passages': [1]}])
        self.assertEqual(len(parts), 5)
        self.assertTrue(parts[4]['texte'].startswith('Ne pas formuler'))


class ToleranceContexte(unittest.TestCase):
    """Essai à l'aveugle : refus injustifiés corrigés, vrais refus maintenus."""
    def test_nombre_present_dans_la_question_accepte(self):
        src = "Définir en équipe les critères et les repères de conversion des niveaux de maîtrise."
        q = "Comment obtenir une note sur 20 à partir de quatre niveaux ?"
        self.assertEqual(sa.unsupported("Définissez en équipe les repères de conversion en note sur 20.", src, q), [])
        self.assertIn('nombre:15', sa.unsupported("Définissez les repères en 15 jours.", src, q))

    def test_outil_nomme_dans_l_intitule_du_passage_accepte(self):
        src = "Ouvrir [Dossiers] > [Dossier EPS], préparer les APSA et les périodes."
        self.assertEqual(sa.unsupported("Dans iPackEPS, ouvrez [Dossiers] > [Dossier EPS].", src, '', 'iPackEPS : programmation annuelle'), [])
        self.assertTrue(sa.unsupported("Dans Pronote, ouvrez [Dossiers] > [Dossier EPS].", src, '', 'iPackEPS : programmation annuelle'))

    def test_incertitude_jugee_sur_la_phrase_source_la_plus_proche(self):
        src = ("Une partie des données est conservée à la rentrée : listes APSA, configuration des classes. "
               "Un bouton « dupliquer » reste à vérifier auprès du support.")
        self.assertEqual(sa.unsupported("Une partie des données, listes APSA et configuration des classes, est conservée à la rentrée.", src), [])
        self.assertIn('modalite:incertitude_effacee', sa.unsupported("Utilisez le bouton « dupliquer » du support.", src))


class PhrasesMultiples(unittest.TestCase):
    def test_element_contenant_plusieurs_phrases_redecoupe(self):
        texte = ("Pour suivre les résultats sur plusieurs années, utilisez le logiciel de vie scolaire pour les notes et les bulletins. "
                 "Le suivi pluriannuel n'est pas une fonction de l'onglet Scolarité d'iPackEPS, qui décrit la scolarité et non un historique de notes. "
                 "iPackEPS ne calcule pas les moyennes de classe et ne conserve pas de carnet de notes.")
        self.assertGreater(len(texte), sa.MAX_CHARS)
        parts = sa._split_long([{'texte': texte, 'passages': [1]}])
        self.assertEqual(len(parts), 3)
        self.assertTrue(parts[2]['texte'].startswith('iPackEPS ne calcule'))



class InterlocuteurDeLaQuestion(unittest.TestCase):
    def test_interlocuteur_present_dans_la_question_admis(self):
        src = "La neutralisation exige une absence justifiée à chacune des deux épreuves, validée par l'autorité académique."
        q = "On peut neutraliser une absence sans certificat avec l'accord du chef d'établissement ?"
        self.assertEqual(sa.unsupported("Non, même avec l'accord du chef d'établissement, sans absence justifiée validée par l'autorité académique.", src, q), [])
        self.assertTrue(sa.unsupported("Demandez à la DEC.", src, q))


if __name__ == '__main__':
    unittest.main()


class PorteeAcademiquePhraseVoisine(unittest.TestCase):
    SRC = ("Réponse directe — un bug ou un blocage d'iPackEPS non résolu : le correspondant académique iPackEPS ; "
           "à Aix-Marseille : ipackeps@ac-aix-marseille.fr, en précisant l'établissement et son UAI, le menu concerné et le message d'erreur exact.")

    def test_regle_nationale_voisine_d_une_adresse_academique_acceptee(self):
        self.assertEqual(sa.unsupported("Pour un bug ou un blocage d'iPackEPS non résolu, contactez le correspondant académique iPackEPS.", self.SRC), [])

    def test_consigne_academique_sans_academie_refusee(self):
        self.assertIn('portee:aix-marseille', sa.unsupported(
            "Précisez l'établissement et son UAI, le menu concerné et le message d'erreur exact.", self.SRC))

    def test_academie_nommee_dans_la_question_suffit(self):
        self.assertEqual(sa.unsupported("Précisez l'établissement et son UAI, le menu concerné et le message d'erreur exact.",
                                        self.SRC, question="À qui m'adresser dans l'académie d'Aix-Marseille si j'ai un bug ?"), [])


class AcademieUtilisateur(unittest.TestCase):
    P = [('Inscription', "À Aix-Marseille, cochez « APTE » dans Cyclades, y compris si un certificat médical atteste une inaptitude.")]
    PH = [{'texte': "Cochez « APTE » dans Cyclades, y compris si un certificat médical atteste une inaptitude.", 'passages': [1]}]

    def run_sa(self, academy):
        audit = {}
        sa.short_answer(_llm({'phrases': self.PH}), tracer=lambda l, a, stage: l, audit=audit,
                        question='Comment inscrire un élève inapte ?', passages=self.P, academy=academy)
        return audit['short_answer']

    def test_collegue_d_aix_recoit_la_consigne_d_aix(self):
        self.assertEqual(len(self.run_sa('Aix-Marseille')['kept']), 1)

    def test_collegue_d_une_autre_academie_reste_protege(self):
        self.assertIn('portee:aix-marseille', self.run_sa('Lille')['rejected'][0]['raisons'])

    def test_exemple_json_montre_plusieurs_phrases(self):
        self.assertGreaterEqual(sa.build_prompt('q', self.P).count('"texte"'), 3)


class ConditionDejaDansLaQuestion(unittest.TestCase):
    BR = ("Si le type de groupe « section sportive scolaire » n’est pas proposé alors que « sport-études » l’est, "
          "ne pas créer un groupe sport-études pour contourner le blocage : les deux dispositifs sont distincts.")

    def test_condition_decrite_par_la_question_acceptee(self):
        q = "Je n'arrive pas à créer mes groupes de section sportive, je n'ai que « sport étude » dans la liste."
        self.assertEqual(sa.unsupported("Ne créez pas un groupe sport-études pour contourner le blocage.", self.BR, q), [])

    def test_condition_absente_de_la_question_toujours_refusee(self):
        self.assertIn('modalite:condition_perdue',
                      sa.unsupported("Ne créez pas un groupe sport-études pour contourner le blocage.", self.BR, "Comment créer un groupe ?"))


class CitationDeLaQuestion(unittest.TestCase):
    def test_expression_citee_par_la_question_acceptee(self):
        src = "Un bug ou un blocage d'iPackEPS non résolu : le correspondant académique iPackEPS."
        q = "iPackEPS indique que des fichiers sont « non importés » ou « non valides ». Qui contacter ?"
        self.assertEqual(sa.unsupported("Pour des fichiers « non importés », contactez le correspondant académique iPackEPS.", src, q), [])

    def test_citation_inventee_toujours_refusee(self):
        src = "Un bug d'iPackEPS : le correspondant académique iPackEPS."
        self.assertTrue(any(r.startswith('citation:') for r in sa.unsupported("Cliquez sur « Réparer ».", src, "Qui contacter ?")))


class ConsignesInternes(unittest.TestCase):
    SRC = "Ajout d'un collègue : distinguer sa présence dans l'équipe et son affectation à une classe. Ne pas inventer de délai garanti ou de droit administrateur."

    def test_consigne_au_redacteur_refusee(self):
        self.assertIn('forme:consigne_interne', sa.unsupported("Il est important de ne pas inventer de délai garanti ou de droit administrateur.", self.SRC))
        self.assertIn('forme:consigne_interne', sa.unsupported("Le corpus ne documente pas de délai.", "Le corpus ne documente pas de délai."))

    def test_conseil_utile_accepte(self):
        self.assertEqual(sa.unsupported("Distinguez sa présence dans l'équipe et son affectation à une classe.", self.SRC), [])


class NombresEtPremisses(unittest.TestCase):
    def test_nombre_ecrit_en_lettres_dans_la_source(self):
        self.assertEqual(sa.unsupported("Les 3 heures d'AS sont comprises.", "les trois heures d'association sportive sont comprises", "combien d'heures d'AS ?"), [])

    def test_sigle_de_la_question_absent_des_passages_refuse(self):
        self.assertIn('premisse:PDF/A', sa.unsupported("Il doit être déposé au format PDF/A dans iPackEPS.",
                                                       "Déposer le projet EPS dans iPackEPS.", "Faut-il le format PDF/A dans iPackEPS ?"))

    def test_sigle_courant_accepte(self):
        self.assertEqual(sa.unsupported("Le TZR assure le service de la personne remplacée.",
                                        "le titulaire assure le service de la personne remplacée", "Je suis TZR : qui fixe mon service ?"), [])


class SigleOrdinaireDeLaQuestion(unittest.TestCase):
    def test_vtt_de_la_question_accepte(self):
        self.assertEqual(sa.unsupported("Le chef d'établissement peut refuser la sortie VTT.",
                                        "Le chef d'établissement autorise ou refuse la sortie.", "Mon chef refuse ma sortie VTT, en a-t-il le droit ?"), [])


class EtapesNumerotees(unittest.TestCase):
    def test_manipulation_rendue_en_liste_numerotee(self):
        rt = load_runtime(); dr = rt.documentary_review
        docs = dr.mark_excerpt("[Dossier EPS] > [APSA] : déclarer les APSA certificatives.\n\n[Dossier Certificatif] > [Protocole] : compléter les dates.",
                               path='data/exemple.txt', title='Protocoles')
        ids = [s['id'] for s in dr.source_packets(docs)[0]['passages']][-2:]
        llm = _llm({'principal': 'D1', 'complements': [], 'passages': ids},
                   {'phrases': [{'texte': "[Dossier EPS] > [APSA] : déclarez les APSA certificatives.", 'passages': [1], 'etape': True},
                                {'texte': "[Dossier Certificatif] > [Protocole] : complétez les dates.", 'passages': [2], 'etape': True}]})
        audit = {}
        out = rt.exact_source_answer.exact_answer(llm, reviewer=dr, tracer=lambda l, a, stage: l, documents=docs,
            question='Comment remplir mes protocoles ?', public='Lycée Général & Techno', mode='ipack', academy='Aix-Marseille',
            audit=audit, synthesis=True)
        self.assertIn('<ol', out)
        self.assertEqual(out.count('<li'), 2)
        self.assertIn('<strong>[Dossier EPS]</strong>', out)


class CorrectifsLotB26(unittest.TestCase):
    """Lot de 50 rejoué au format pas à pas : derniers refus et dérapages corrigés."""
    P = [('SHN', "Un sportif de haut niveau peut bénéficier d'un régime particulier, sur proposition du comité de pilotage "
                 "et sous réserve de validation par le recteur. En CCF, trois épreuves de trois champs différents, avec 20/20 sur la spécialité.")]

    def run_sa(self, phrases, question='Un sportif de haut niveau a-t-il un régime particulier ?', passages=None, academy=None):
        audit = {}
        out = sa.short_answer(_llm({'phrases': phrases}), tracer=lambda l, a, stage: l, audit=audit,
                              question=question, passages=passages or self.P, academy=academy)
        return out, audit['short_answer']

    def test_phrase_longue_sans_coupure_acceptee_jusqu_a_la_limite(self):
        long = ("Ce régime est accordé sur proposition du comité de pilotage et sous réserve de validation par le recteur, "
                "le sportif devant justifier son statut au moment de l'inscription, en CCF avec trois épreuves de trois champs différents "
                "et une note de 20/20 sur la spécialité, ce qui concerne l'enseignement commun d'EPS du baccalauréat général et technologique")
        self.assertGreater(len(long), sa.MAX_CHARS)
        self.assertLess(len(long), sa.MAX_CHARS_HARD)
        out, rep = self.run_sa([{'texte': long, 'passages': [1]}])
        self.assertNotIn(['forme'], [r['raisons'] for r in rep['rejected']])

    def test_reserve_dite_dans_une_autre_phrase_suffit(self):
        out, rep = self.run_sa([{'texte': "Oui, un sportif de haut niveau peut bénéficier d'un régime particulier.", 'passages': [1]},
                                {'texte': "Ce régime est accordé sous réserve de validation par le recteur.", 'passages': [1]}])
        self.assertEqual(len(rep['kept']), 2)
        self.assertLess(out.index('peut bénéficier'), out.index('sous réserve'))

    def test_reserve_absente_partout_reste_refusee(self):
        out, rep = self.run_sa([{'texte': "Un sportif de haut niveau bénéficie d'un régime particulier.", 'passages': [1]}])
        self.assertEqual(rep['status'], 'nothing_kept')
        self.assertIn('modalite:incertitude_effacee', rep['rejected'][0]['raisons'])

    def test_conclusion_appliquee_a_la_situation_refusee(self):
        src = "L'enseignant apprécie la situation pour renvoyer l'élève à une évaluation différée ou noter sur une seule activité."
        self.assertIn('modalite:conclusion_ajoutee', sa.unsupported(
            "L'évaluation différée n'est possible que si la pratique reste possible, ce qui n'est pas le cas ici.", src))

    def test_oui_retire_devant_une_generalisation(self):
        P = [('Lot', "Seul le chef d'établissement peut déverrouiller un lot dans Santorin.")]
        out, rep = self.run_sa([{'texte': "Oui, seul le chef d'établissement peut déverrouiller le lot dans Santorin.", 'passages': [1]}],
                               question='Peut-on conclure que tous les chefs d’établissement peuvent toujours le déverrouiller ?', passages=P)
        self.assertTrue(rep['kept'][0]['texte'].startswith('Seul le chef'))

    def test_consigne_d_aix_situee_quand_l_academie_n_est_pas_precisee(self):
        P = [('Remplacer', "À Aix-Marseille, créer le nouveau protocole dans [Dossiers] > [Dossier certificatif].")]
        out, rep = self.run_sa([{'texte': "[Dossiers] > [Dossier certificatif] : créer le nouveau protocole.", 'passages': [1], 'etape': True}],
                               question='Comment remplacer une APSA ?', passages=P)
        self.assertEqual(rep['status'], 'rendered')
        self.assertTrue(rep['kept'][0]['texte'].startswith('À Aix-Marseille, [Dossiers]'))


class Dates(unittest.TestCase):
    """Les dates sont le point faible : jour, mois, année et statut (échéance ou historique) contrôlés."""
    import datetime
    TODAY = datetime.date(2026, 10, 26)

    def r(self, phrase, src, q=''):
        return sa._date_reasons(sa._compact(phrase), sa._compact(src), q, today=self.TODAY)

    def test_date_absente_de_la_fiche_refusee(self):
        self.assertIn('date:absente:15 mars', self.r("Déposez le dossier avant le 15 mars.", "Déposer le dossier avant le 13 novembre 2026."))

    def test_annee_changee_refusee(self):
        self.assertTrue(any(x.startswith('date:annee_changee') for x in
                            self.r("La CAHPN se réunit le 13 novembre 2026.", "CAHPN GT/pro le 13 novembre 2025.")))

    def test_echeance_passee_refusee(self):
        self.assertTrue(any(x.startswith('date:echeance_passee') for x in
                            self.r("Faites la demande au plus tard le 30 mai.", "Demande d'activité établissement au plus tard le 30 mai 2026.")))

    def test_echeance_a_venir_acceptee(self):
        self.assertEqual(self.r("Déposez le dossier avant le 13 novembre 2026.", "Déposer le dossier avant le 13 novembre 2026."), [])

    def test_date_historique_presentee_sans_le_dire_refusee(self):
        src = "Calendrier historique du BA : CAHPN le 13 novembre 2025. Ces dates ne sont pas des échéances."
        self.assertTrue(any(x.startswith('date:historique') for x in self.r("La CAHPN a lieu le 13 novembre.", src)))
        self.assertEqual([x for x in self.r("Pour la session 2026, la CAHPN était le 13 novembre 2025.", src)
                          if x.startswith('date:historique')], [])

    def test_premier_du_mois(self):
        self.assertEqual(self.r("Session ouverte le 1er juin 2027.", "Ouverture le 1er juin 2027."), [])
