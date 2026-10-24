import unittest
from exact_source_answer import complete_selection_contracts


class SelectionContractsTests(unittest.TestCase):
    def decision(self):
        return dict(id='D1', path='data/examens/audit_faq_2026_10_12/f4_procedure_verifiee.txt', title='Décision', passages=[
            dict(id='D1P1', text='Si tout le groupe est erroné : opération A.', scope={'level':'logiciel'}),
            dict(id='D1P2', text='Si les protocoles sont déjà validés : opération B.', scope={'level':'academique','academy':'Aix-Marseille'}),
            dict(id='D1P3', text='Si seuls quelques élèves sont concernés : opération C.', scope={'level':'logiciel'})])

    def contact(self):
        return dict(id='D2', path='data/ipack/qui_contacter_assistance_ipackeps.txt', title='Contacts', passages=[
            dict(id='D2P1', text='La DEC (division des examens) : données des candidats.'),
            dict(id='D2P2', text='Informations spécifiques de contact de la DEC : coordonnées non fournies.')])

    def test_unspecified_decision_restores_declared_branches_and_scopes(self):
        p=self.decision(); report={}
        selected, focus=complete_selection_contracts([p],[p],['D1P2'],'Erreur de groupe dans Cyclades',report)
        self.assertEqual(focus,['D1P1','D1P2','D1P3'])
        self.assertEqual(selected,[p])
        self.assertEqual(p['passages'][1]['scope']['academy'],'Aix-Marseille')
        self.assertEqual(report['selection_contracts'][0]['origin'],'code')
        self.assertFalse(report['selection_contracts'][0]['applicability_proven'])

    def test_explicit_discriminants_leave_model_choice_unchanged(self):
        p=self.decision()
        for detail in ['validés','non validés','quelques élèves','tout le groupe']:
            with self.subTest(detail=detail):
                _,focus=complete_selection_contracts([p],[p],['D1P2'],'Erreur groupe protocole '+detail,{})
                self.assertEqual(focus,['D1P2'])

    def test_selected_explanation_alone_also_restores_declared_decision(self):
        p=self.decision()
        p['passages'].insert(0,dict(id='D1P0',text='Le champ est grisé.'))
        _,focus=complete_selection_contracts([p],[p],['D1P0'],'Erreur groupe Cyclades',{})
        self.assertEqual(focus,['D1P0','D1P1','D1P2','D1P3'])

    def test_document_without_focused_passage_does_not_trigger_decision(self):
        p=self.decision()
        _,focus=complete_selection_contracts([p],[p],['D9P1'],'Erreur groupe Cyclades',{})
        self.assertEqual(focus,['D9P1'])

    def test_no_general_completion_of_other_sections_or_unknown_sources(self):
        p=self.decision();p['path']='data/autre.txt'
        _,focus=complete_selection_contracts([p],[p],['D1P2'],'Erreur groupe Cyclades',{})
        self.assertEqual(focus,['D1P2'])
        p=self.decision();p['passages'][2]['section']='Autre situation'
        _,focus=complete_selection_contracts([p],[p],['D1P2'],'Erreur groupe Cyclades',{})
        self.assertEqual(focus,['D1P2'])

    def test_incomplete_or_ambiguous_contract_has_no_effect(self):
        for change in ['missing','duplicate']:
            p=self.decision()
            if change=='missing':p['passages'].pop()
            else:p['passages'].append(dict(p['passages'][0],id='D1P4'))
            _,focus=complete_selection_contracts([p],[p],['D1P2'],'Erreur groupe Cyclades',{})
            self.assertEqual(focus,['D1P2'])

    def test_contact_request_retains_contact_and_limit_instead_of_neighbour(self):
        c=self.contact();d=self.decision();report={}
        selected,focus=complete_selection_contracts([d,c],[d],['D1P2'],'Quel service à la DEC pour une inscription ?',report)
        self.assertEqual(selected,[c]);self.assertEqual(focus,['D2P1','D2P2'])
        self.assertEqual(report['selection_contracts'][0]['removed'],['D1P2'])

    def test_compound_contact_request_keeps_diagnostic(self):
        c=self.contact();d=self.decision()
        selected,focus=complete_selection_contracts([d,c],[d],['D1P2'],
            'Comment corriger une inscription et qui contacter à la DEC ?',{})
        self.assertEqual(selected,[c,d]);self.assertEqual(focus,['D2P1','D2P2','D1P2'])

    def test_no_contact_contract_for_procedure_or_other_contact(self):
        c=self.contact();d=self.decision()
        for q in ['Comment corriger les données DEC ?', 'Qui contacter pour mon accès iPackEPS ?']:
            selected,focus=complete_selection_contracts([d,c],[d],['D1P2'],q,{})
            self.assertEqual(selected,[d]);self.assertEqual(focus,['D1P2'])


if __name__=='__main__':unittest.main()
