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
