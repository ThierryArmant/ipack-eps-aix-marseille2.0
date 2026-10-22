import unittest
from claim_guards import evidence_relation_errors
from documentary_review import context_document_mismatch, situation_mismatch, optional_unsupported_referral


def claim(text, proof):
    return {'section':'decision','text':text,'evidence':[{'quote':proof}]}

class ApplicabilityTests(unittest.TestCase):
    def test_negative_export_is_not_a_refusal_of_admission(self):
        proof="Non : exporter le fichier ne crée pas l'inscription. Faire vérifier la candidature par la direction."
        self.assertTrue(evidence_relation_errors([claim("Le candidat ne peut pas être admis à l'épreuve.",proof)],'Peut-on accueillir ce candidat ?'))
        self.assertFalse(evidence_relation_errors([claim("L'export ne crée pas l'inscription.",proof)],'Comment exporter ?'))
        self.assertFalse(evidence_relation_errors([claim("Le candidat ne peut pas être admis.","Le candidat ne peut pas être admis sans confirmation du service.")],'Peut-on accueillir ce candidat ?'))
        self.assertFalse(evidence_relation_errors([claim("Les passages ne permettent pas de confirmer son admission.",proof)],'Peut-on accueillir ce candidat ?'))

    def test_protected_right_needs_its_own_proof(self):
        proof="L'indemnité varie selon la distance et la nature du remplacement."
        self.assertTrue(evidence_relation_errors([claim('Un temps de trajet protégé est accordé.',proof)],'Trajet entre sites ?'))
        self.assertTrue(evidence_relation_errors([claim('Si les transports ne permettent pas la liaison, un temps de trajet protégé est accordé.',proof)],'Trajet entre sites ?'))
        self.assertFalse(evidence_relation_errors([claim('Un temps de trajet protégé est accordé.','Le temps de trajet est protégé selon les modalités suivantes.')],'Trajet entre sites ?'))

    def test_conditions_do_not_cross_alternatives(self):
        proof="L'enseignant peut soit organiser une évaluation différée ; soit retenir les notes déjà obtenues pour une certification réduite."
        self.assertTrue(evidence_relation_errors([claim("L'évaluation différée est possible uniquement si des notes ont déjà été obtenues.",proof)],'Quand organiser le différé ?'))
        self.assertFalse(evidence_relation_errors([claim("L'enseignant peut organiser une évaluation différée.",proof)],'Quand organiser le différé ?'))
        direct="L'évaluation différée est possible uniquement si des notes ont déjà été obtenues."
        self.assertFalse(evidence_relation_errors([claim(direct,direct)],'Quand organiser le différé ?'))

    def test_exception_on_deferred_does_not_apply_to_terminal_exam(self):
        proof="Il n'est pas prévu d'épreuve ponctuelle de remplacement. Une évaluation différée peut être organisée en cas de force majeure."
        self.assertTrue(evidence_relation_errors([claim("Il n'existe pas d'épreuve ponctuelle de remplacement, sauf en cas de force majeure.",proof)],'Quand programmer le différé ?'))

    def test_software_scope_must_address_the_named_object(self):
        self.assertTrue(evidence_relation_errors([claim('Les curseurs ne sont pas gérés dans cet outil.','Les notes ne sont pas saisies dans cet outil.')],'Où sont les curseurs ?'))
        self.assertFalse(evidence_relation_errors([claim('Les curseurs ne sont pas gérés dans cet outil.','Les curseurs ne sont pas gérés dans cet outil.')],'Où sont les curseurs ?'))

    def test_optional_proof_does_not_establish_compulsory_exam(self):
        proof="Les épreuves optionnelles sont réservées aux candidats individuels, en complément de l'épreuve obligatoire ponctuelle."
        self.assertTrue(evidence_relation_errors([claim('Les candidats scolarisés ne peuvent pas passer le ponctuel.',proof)],'Qui relève du ponctuel ?'))
        self.assertFalse(evidence_relation_errors([claim('Les candidats individuels passent cette épreuve optionnelle.',proof)],'Qui relève de cette option ?'))
        self.assertFalse(evidence_relation_errors([claim('Sélectionner cette option pour créer le dossier.', 'Sélectionner cette option pour créer le dossier.')],'Comment préparer le ponctuel ?'))

    def test_single_grade_not_presumed_for_recording_incapacity(self):
        c=claim("L'enseignant peut conserver la note unique.","La certification sur une note unique dépend de l'appréciation de l'enseignant.")
        self.assertTrue(evidence_relation_errors([c],"Une inaptitude partielle est enregistrée : où saisir les résultats ?"))
        self.assertFalse(evidence_relation_errors([c],"Après deux DI et une seule note, où saisir le résultat ?"))
        c['text']="Si une seule note est disponible, l'enseignant apprécie la certification sur note unique."
        self.assertFalse(evidence_relation_errors([c],"Une inaptitude partielle est enregistrée : où saisir les résultats ?"))

    def test_preselection_excludes_wrong_regime_and_keeps_comparative(self):
        def mismatch(q,title,text=''):
            return context_document_mismatch(q,'Lycée voie générale','examens',{'title':title,'path':'guide.txt','text':text})
        self.assertTrue(mismatch('Quels candidats passent le ponctuel ?','Épreuve optionnelle ponctuelle'))
        self.assertFalse(mismatch('Quels candidats passent l’option au ponctuel ?','Épreuve optionnelle ponctuelle'))
        self.assertFalse(mismatch('Quels candidats passent le ponctuel ?','Épreuves obligatoires et facultatives'))
        self.assertFalse(mismatch('Comment configurer le CCF ?','Option interactive : mode certification'))
        self.assertTrue(mismatch('Inaptitude partielle enregistrée : où saisir les résultats ?','DI + DI + note unique'))
        self.assertFalse(mismatch('DI + DI + une note : comment saisir ?','DI + DI + note unique'))

    def test_generic_perimeter_does_not_prove_technical_object(self):
        p={'title':'Carnet de notes','path':'guide.txt','text':'Aucune note saisie.'}
        self.assertTrue(context_document_mismatch('Les curseurs sont-ils à jour ?','Lycée','ipack',p))
        p['text']='Les curseurs sont décrits dans le référentiel.'
        self.assertFalse(context_document_mismatch('Les curseurs sont-ils à jour ?','Lycée','ipack',p))

    def test_numeric_entry_is_not_count_of_completed_evaluations(self):
        self.assertFalse(situation_mismatch('Comment saisir une note sur vingt ?',"Aucune note ne se saisit dans cet outil."))
        self.assertTrue(situation_mismatch('Un élève inapte a deux notes acquises.',"Une seule note est obtenue par cet élève."))
        self.assertFalse(situation_mismatch('Trois notes de CCF au DNB ?',"Le cas deux dispenses et une note du lycée ne s'applique pas au DNB ; ne pas transformer les notes en DI."))

    def test_optional_contact_does_not_block_valid_steps(self):
        r={'errors':['passage cité sans rapport avec l’affirmation : choisir le passage qui l’énonce'],
           'claim':{'section':'limite','text':"Si le problème persiste, il est conseillé de contacter le référent du dossier."}}
        accepted=[{'section':'etape','text':'Ouvrir le dossier puis vérifier les rubriques.'}]
        self.assertTrue(optional_unsupported_referral(r,'Comment compléter le dossier ?',accepted))
        self.assertTrue(optional_unsupported_referral(r,'Un message qui me bloque : comment compléter le dossier ?',accepted))
        self.assertFalse(optional_unsupported_referral(r,'Qui contacter si le dossier reste bloqué ?',accepted))
        self.assertFalse(optional_unsupported_referral(r,'Comment compléter le dossier ?',[]))
        r['claim']['text']='Si le problème persiste, il faut contacter le référent du dossier.'
        self.assertFalse(optional_unsupported_referral(r,'Comment compléter le dossier ?',accepted))

    def test_relation_failure_triggers_repair_before_display(self):
        from documentary_review import review_exam_answer, mark_excerpt
        from test_documentary_review import FakeLLM
        proof="Non : refaire l'export ne crée pas de candidat inscrit. La direction doit vérifier l'inscription du candidat à l'épreuve."
        def c(text):
            return {'section':'decision','text':text,'evidence':[{'document_id':'D1','passage_ids':['D1P1']} ]}
        model=FakeLLM([{'claims':[c("Un candidat absent de l'inscription à l'épreuve ne peut pas être accepté.")]},
                       {'claims':[c("La direction doit vérifier l'inscription du candidat à l'épreuve.")]}])
        audit={}
        answer=review_exam_answer(model,question="Peut-on accepter un candidat absent de la liste ?",public='Lycée voie générale',mode='examens',documents=mark_excerpt(proof,title='Vérification des inscriptions'),audit=audit)
        self.assertEqual(len(model.prompts),2)
        self.assertTrue(audit['repair_successful'])
        self.assertNotIn('ne peut pas être accepté',answer)
        self.assertIn('vérifier',answer)

    def test_optional_unproved_contact_is_omitted_without_new_generation(self):
        from documentary_review import review_exam_answer, mark_excerpt
        from test_documentary_review import FakeLLM
        proof='Pour compléter le dossier, ouvrir le module et vérifier les rubriques.'
        model=FakeLLM([{'claims':[
            {'section':'etape','text':proof,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]},
            {'section':'limite','text':'Si le problème persiste, il est conseillé de contacter le référent du dossier.',
             'evidence':[{'document_id':'D1','passage_ids':['D1P2']}]}]}])
        audit={}
        answer=review_exam_answer(model,question='Comment compléter le dossier ?',public='Collège',mode='ipack',documents=mark_excerpt(proof+'\n\nLa réunion de rentrée est prévue sur le calendrier.',title='Compléter le dossier'),audit=audit)
        self.assertEqual(len(model.prompts),1)
        self.assertFalse(audit['repair_performed'])
        self.assertEqual(len(audit['excluded_unsupported_optional_referrals']),1)
        self.assertIn('vérifier les rubriques',answer)
        self.assertNotIn('contacter',answer)

    def test_admission_decision_cannot_escape_by_rephrasing(self):
        proof="Refaire l'export ne crée pas de candidat. Faire vérifier l'inscription et l'identité par la direction."
        for text in ["Il n'est pas possible d'accepter ce candidat.",
                     "Il n’est pas possible d’accepter ce candidat. Avant toute décision, vérifier son inscription.",
                     "L'admission du candidat est refusée.",
                     "Le candidat peut être accepté le jour de l'épreuve.",
                     "Il est possible d'admettre ce candidat après vérification."]:
            with self.subTest(text=text):
                self.assertTrue(evidence_relation_errors([claim(text,proof)],'Un candidat manque : que faire ?'))
        self.assertFalse(evidence_relation_errors([claim("Faire vérifier l'inscription par la direction avant toute décision.",proof)],'Un candidat manque : que faire ?'))

    def test_repair_rephrasing_unsupported_admission_still_fails(self):
        from documentary_review import review_exam_answer, mark_excerpt
        from test_documentary_review import FakeLLM
        proof="Refaire l'export ne crée pas de candidat inscrit. Faire vérifier son inscription à l'épreuve par la direction."
        def c(text):
            return {'section':'decision','text':text,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}
        writer=FakeLLM([{'claims':[c("Non, le candidat inscrit à l'épreuve ne peut pas être accepté.")]},
                        {'claims':[c("Il n'est pas possible d'accepter le candidat inscrit à l'épreuve.")]}])
        audit={}
        with self.assertRaises(ValueError):
            review_exam_answer(writer,question='Peut-on accepter ce candidat ?',public='Lycée voie générale',mode='examens',documents=mark_excerpt(proof,title='Inscription du candidat'),audit=audit)
        self.assertTrue(audit['repair_performed'])
        self.assertFalse(audit['repair_successful'])
        self.assertTrue(audit['final_rejections'])

    def test_export_fiche_no_longer_has_a_detached_negative_answer(self):
        from pathlib import Path
        text=Path('data/examens/cyclades_candidats_absents.txt').read_text()
        self.assertNotIn("Non : refaire",text)
        self.assertIn("Refaire l'export iPackEPS ne crée pas un candidat",text)

    def test_admission_guard_does_not_turn_certificate_acceptance_into_entry(self):
        c=claim("Pour accepter un certificat médical, il doit être établi par un médecin.",
                "Le certificat médical doit être établi par un médecin.")
        self.assertFalse(evidence_relation_errors([c],"Comment accepter le certificat d'un élève ?"))

    def test_verification_before_decision_is_not_an_admission_decision(self):
        proof="Faire vérifier l'inscription et l'identité auprès du secrétariat et de la direction. Si une régularisation est nécessaire, la direction contacte le service des examens."
        for text in [
            "Si un candidat n'apparaît pas sur la liste, il est nécessaire de vérifier son inscription auprès de la direction avant de décider de son acceptation.",
            "Avant d'accepter un candidat, il faut vérifier son inscription auprès de la direction.",
            "La décision d'acceptation dépend de la vérification de l'inscription. Si une régularisation est nécessaire, la direction doit contacter le service des examens."]:
            self.assertFalse(evidence_relation_errors([claim(text,proof)],'Peut-on accepter le candidat ?'),text)
        for text in [
            "Il n'est pas possible d'accepter ce candidat. Avant toute décision, vérifier son inscription.",
            "Avant d'accepter le candidat, vérifier son inscription ; ensuite il peut être accepté.",
            "Vérifier l'inscription avant de décider. Le candidat peut être accepté."]:
            self.assertTrue(evidence_relation_errors([claim(text,proof)],'Peut-on accepter le candidat ?'),text)

    def test_prudent_verification_reaches_display_without_repair(self):
        from documentary_review import review_exam_answer, mark_excerpt
        from test_documentary_review import FakeLLM
        proof="Faire vérifier l'inscription et l'identité auprès du secrétariat et de la direction. Si une régularisation est nécessaire, la direction contacte le service des examens."
        text="Il est nécessaire de vérifier l'inscription du candidat auprès du secrétariat et de la direction avant de décider de son acceptation."
        writer=FakeLLM([{'claims':[{'section':'etape','text':text,'evidence':[{'document_id':'D1','passage_ids':['D1P1']}]}]}]);audit={}
        answer=review_exam_answer(writer,question='Peut-on accepter un candidat absent de la liste ?',public='Lycée voie générale',mode='examens',documents=mark_excerpt(proof,title='Vérification de candidature'),audit=audit)
        self.assertEqual(len(writer.prompts),1)
        self.assertFalse(audit['repair_performed'])
        self.assertIn('vérifier',answer)
