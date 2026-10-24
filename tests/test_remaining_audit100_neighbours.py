"""Sélection des procédures existantes et exactitude des contacts, sans appel distant."""
import unittest
from pathlib import Path
import knowledge_catalog as kc
import test_documentation as routing
from documentary_review import (context_document_mismatch, mark_excerpt, source_packets,
                                review_exam_answer, validate_claims)
from test_documentary_review import FakeLLM

class RemainingAuditNeighbours(unittest.TestCase):
    def setUp(self):
        self.h=routing.DocumentationTests();self.h.setUp()
    def route(self,q,mode='examens',public='Lycée Général & Techno'):
        return self.h.route(q,public,mode)[0]

    def test_personal_mission_document_not_creation_or_transport(self):
        q='Où télécharger mon ordre de mission dans Imag’in pour aller au centre d’examen ?'
        text=self.route(q)
        self.assertIn('imagin_consulter_sa_convocation.txt',text)
        self.assertIn('duplicata',text)
        self.assertNotIn('texte_transport_des_eleves.txt',text)
        self.assertNotIn('imagin_consulter_sa_convocation.txt',self.route('Créer les missions CCF dans Imag’in pour mes collègues ?'))

    def test_candidate_documents_not_protocol_export_or_appeal(self):
        for q in ['Où consulter la convocation d’un candidat libre dans Cyclades ?', 'Quand les élèves reçoivent-ils leur relevé de notes dans Cyclades ?']:
            text=self.route(q)
            self.assertIn('cyclades_documents_candidat.txt',text)
            self.assertNotIn('calendrier_certificatif_aix_marseille.txt',text)
        self.assertIn('contestation_note.txt',self.route('Après le jury, erreur de report de note : que faire ?'))
        self.assertNotIn('cyclades_documents_candidat.txt',self.route('Comment contester une erreur sur mon relevé de notes ?'))

    def test_certificate_form_has_existing_national_model(self):
        text=self.route('Le formulaire académique de certificat médical est-il le seul modèle accepté ?', 'textes')
        self.assertIn('arrete_1989_certificat_inaptitude.txt',text)
        self.assertIn('papier à en-tête',text)
        self.assertIn('dispense_inaptitude_presence_cours.txt', self.route('Élève dispensé : doit-il venir en cours ?', 'textes'))

    def test_after_harmonisation_is_not_open_lot_edit(self):
        text=self.route('La commission d’harmonisation est terminée : qui peut modifier une note Santorin ?')
        self.assertIn('harmonisation_cloture_remontee.txt',text)
        self.assertNotIn('santorin_corriger_une_note.txt',text)
        self.assertIn('santorin_corriger_une_note.txt', self.route('J’ai tapé une mauvaise note dans mon lot Santorin : comment corriger une note ?'))
        closed=self.route('Santorin : serveur fermé, des notes restent à saisir')
        self.assertIn('harmonisation_cloture_remontee.txt',closed)

    def test_commission_document_deposit_keeps_pv_distinct(self):
        text=self.route('Où déposer les documents pour les cas particuliers de la commission ?', 'textes')
        self.assertIn('ipack_071',text)
        self.assertIn('Dépôt des documents pour la commission',text)
        self.assertNotIn('ipack_071',self.route('Où transmettre le procès-verbal de commission ?', 'textes'))

    def test_missing_pupils_is_not_missing_school_or_foreign_access(self):
        text=self.route('Aucun élève dans cet établissement, comment importer ?', 'ipack','Collège (DNB)')
        self.assertIn('classes_actualiser_configurer_organiser_importer.txt',text)
        self.assertNotIn('ipack_015',text)
        text=self.route('Mes élèves réorientés n’apparaissent pas dans la liste iPackEPS', 'ipack')
        self.assertIn('classes_actualiser_configurer_organiser_importer.txt',text)
        self.assertNotIn('cyclades_candidats_absents.txt',text)
        self.assertIn('cyclades_candidats_absents.txt',self.route('Inscription tardive : candidat absent de la liste Cyclades'))
        text=self.route('Accès iPackEPS pour nos enseignants CFA, MFR et AEFE ?', 'ipack')
        self.assertNotIn('centres_etrangers_blocage_non_resolu.txt',text)

    def test_unknown_widget_does_not_receive_dossier_instructions(self):
        q='Première connexion : installer le widget Pratic Plus ?'
        self.assertNotIn('ordre_premiere_connexion',self.route(q,'ipack'))
        self.assertFalse(kc.documented_response(q,'Lycée Général & Techno','ipack')[0])
        self.assertTrue(context_document_mismatch(q,'Lycée Général & Techno','ipack',{'title':'Première connexion','text':'Remplir ma fiche professeur.'}))
        self.assertFalse(context_document_mismatch(q,'Lycée Général & Techno','ipack',{'title':'Portail','text':'Widget Pratic Plus : la source décrit son installation.'}))

    def test_unrelated_ipack_perimeter_removed_before_exam_generation(self):
        q='Comment consulter mon relevé de notes Cyclades ?'
        wrong=mark_excerpt(Path('data/commun/audit60/ipack_perimetre.txt').read_text(),path='data/commun/audit60/ipack_perimetre.txt')
        path='data/examens/audit100_2026_10_20/cyclades_documents_candidat.txt'
        right=mark_excerpt(Path(path).read_text(),path=path)
        llm=FakeLLM([{'claims':[]}]);audit={}
        review_exam_answer(llm,question=q,public='Lycée Général & Techno',mode='examens',documents=wrong+'\n'+right,audit=audit)
        self.assertIn('D1',audit['excluded_situation_documents'])
        self.assertNotIn('D2',audit['excluded_situation_documents'])
        self.assertNotIn('carnet de notes',str(llm.prompts))
        self.assertIn('Mes documents',str(llm.prompts))
        self.assertFalse(context_document_mismatch('Comment saisir mes notes iPackEPS ?', 'Lycée Général & Techno','ipack',{'path':'data/commun/audit60/ipack_perimetre.txt'}))

    def test_email_must_be_exactly_in_selected_evidence(self):
        text='Pour obtenir une aide technique, contacter support@exemple.fr avec le menu concerné.'
        packets=source_packets(mark_excerpt(text,path='guide.txt',title='Assistance'))
        span=packets[0]['passages'][0]
        def claim(email):return {'claims':[{'section':'etape','text':f'Pour une aide technique, contacter {email} avec le menu concerné.','evidence':[{'document_id':'D1','passage_ids':[span['id']]}]}]}
        ok,err=validate_claims(claim('support@exemple.fr'),packets)
        self.assertTrue(ok);self.assertFalse(err)
        ok,err=validate_claims(claim('support@ac-exemple.fr'),packets)
        self.assertFalse(ok)
        self.assertIn('adresse électronique',str(err))
        other=mark_excerpt('Autre contact : support@ac-exemple.fr pour une autre opération.',path='autre.txt')
        self.assertFalse(validate_claims(claim('support@ac-exemple.fr'),source_packets(mark_excerpt(text,path='guide.txt')+'\n'+other))[0])

    def test_minimum_epreuves_keeps_normal_case_and_medical_exceptions(self):
        text=self.route('Quel minimum d’épreuves au baccalauréat EPS en CCF ?')
        self.assertIn('gt_regles_decisives.txt',text)
        self.assertIn('gt_inaptitude_possibilites_ccf.txt',text)
        self.assertIn('trois épreuves',text)
        self.assertIn('note unique',text)
        self.assertNotIn('gt_inaptitude_possibilites_ccf.txt',self.route('Quel minimum d’épreuves au CAP ?','examens','Lycée Pro / CAP'))

    def test_collective_closure_keeps_temporary_and_long_term_distinct(self):
        text=self.route('Fermeture du plateau sportif : peut-on saisir une dispense collective ?')
        self.assertIn('fermeture_collective.txt',text)
        self.assertIn('fermeture d’un jour'.replace('’',"'"),text)
        self.assertIn('durablement fermée',text)
        self.assertNotIn('fermeture_collective.txt',self.route('Un seul élève sans piscine : déclarer CE ?'))

    def test_referentiel_and_evaluator_do_not_change_object(self):
        text=self.route('Comment valider une déclinaison AFLP déposée dans iPackEPS ?','ipack')
        self.assertIn('dossier_certificatif_lycee_gt.txt',text)
        self.assertIn('Dépôt Référentiels Certificatifs',text)
        text=self.route('Mon évaluateur est en maladie : comment modifier cet enseignant dans Cyclades ?')
        self.assertIn('reaffecter_evaluateur_cyclades.txt',text)

    def test_pv_and_activity_change_keep_qualified_sources(self):
        text=self.route('Transmettre les procès-verbaux de la commission : quel circuit ?','textes')
        self.assertIn('pv_ccf_prudence.txt',text)
        self.assertIn('consigne locale',text)
        text=self.route('Modifier une APSA du protocole après le verrouillage des vœux ?','textes')
        self.assertIn('remplacer_activite_protocole_valide.txt',text)
        self.assertIn('prévenir',text)

    def test_generic_mission_enrichment_does_not_invent_santorin(self):
        generic=kc.enrich('Télécharger mon ordre de mission dans Imag’in')
        self.assertNotIn('santorin',generic)
        self.assertIn('convocation',generic)
        ccf=kc.enrich('Pas de mission CCF dans Imag’in')
        self.assertIn('santorin',ccf)
        self.assertIn('gt_inaptitude_possibilites_ccf.txt',self.route('Quel minimum d’épreuves au bac ?'))

    def test_generic_groups_and_edits_do_not_become_santorin(self):
        for q in ['Il manque des élèves dans mon groupe iPackEPS', 'Un élève est dans un mauvais groupe EPS', 'Je ne peux plus modifier ma fiche professeur']:
            enriched=kc.enrich(q)
            self.assertNotIn('santorin',enriched)
            self.assertNotIn('mauvais lot',enriched)
            self.assertNotIn('deverrouiller lot',enriched)
        self.assertIn('santorin',kc.enrich('Il manque des élèves dans mon lot'))
        self.assertIn('deverrouiller lot',kc.enrich('Je ne peux plus modifier mon lot Santorin'))
        self.assertNotIn('mauvais lot',kc.enrich('Un élève est dans un autre groupe Cyclades'))
        self.assertIn('mauvais lot',kc.enrich('Un élève est dans un autre groupe Santorin'))
