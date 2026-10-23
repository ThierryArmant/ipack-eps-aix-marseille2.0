import unittest
from admin_retest_113_live import provider_for_replay

class ReplayProviderTests(unittest.TestCase):
    def test_private_waiting_batch_can_force_openai(self):
        self.assertEqual(provider_for_replay({'is_admin':True,'audit113_batch':
            {'waiting':True,'provider':'openai'}},'albert'),'openai')

    def test_override_cannot_affect_regular_questions_or_non_admin(self):
        for state in ({}, {'is_admin':True}, {'is_admin':False,'audit113_batch':{'waiting':True,'provider':'openai'}},
                      {'is_admin':True,'audit113_batch':{'waiting':False,'provider':'openai'}}):
            self.assertEqual(provider_for_replay(state,'albert'),'albert')

class ReplayAcademyTests(unittest.TestCase):
    def test_explicit_row_academy_preserved_for_technical_context(self):
        from admin_retest_113_live import academy_for_replay
        state={'is_admin':True,'audit113_batch':{'waiting':True,'index':0,'rows':[
               {'mode':'ipack','question':'Retrouver le dossier EPS','academie':'Grenoble'}]}}
        self.assertEqual(academy_for_replay(state,'Non précisée'),'Grenoble')
        state['audit113_batch']['rows'][0]={'mode':'ipack','question':"Je travaille à Dijon, comment consulter le dossier ?",'academie':'Grenoble'}
        self.assertEqual(academy_for_replay(state,'Non précisée'),'Dijon')

    def test_normal_sessions_and_missing_context_remain_unchanged(self):
        from admin_retest_113_live import academy_for_replay
        for state in [{}, {'is_admin':True},
                      {'is_admin':False,'audit113_batch':{'waiting':True,'index':0,'rows':[{'academie':'Grenoble'}]}},
                      {'is_admin':True,'audit113_batch':{'waiting':False,'index':0,'rows':[{'academie':'Grenoble'}]}},
                      {'is_admin':True,'audit113_batch':{'waiting':True,'index':1,'rows':[{'academie':'Grenoble'}]}}]:
            self.assertEqual(academy_for_replay(state,'Créteil'),'Créteil')


class ReplayAcademyIsolationTests(unittest.TestCase):
    def state(self, row):
        return {'is_admin':True, 'academie_memorisee':'Créteil', 'audit113_batch':{
            'waiting':True, 'index':0, 'rows':[row]}}

    def test_blank_row_ignores_previous_academy_and_notice(self):
        from admin_retest_113_live import academy_context_for_replay
        for academy in ('Créteil','La Réunion','Aix-Marseille'):
            self.assertEqual(academy_context_for_replay(self.state({'academie':'','question':'Où est le lot ?'}),
                             academy, 'Ancien avertissement'), ('Non précisée',''))

    def test_explicit_question_scope_survives_previous_session_and_csv(self):
        from admin_retest_113_live import academy_for_replay
        for question in ('Quelle note finale à Aix-Marseille ?',
                         'Cyclades Aix-Marseille 2026 : appliquer un tutoriel Strasbourg 2024 ?',
                         'Quelles dates à Aix-Marseille, et les aménagements ?',
                         'Je travaille à Dijon, où est le dossier ?'):
            expected = 'Dijon' if 'Dijon' in question else 'Aix-Marseille'
            self.assertEqual(academy_for_replay(self.state({'question':question,'academie':'Créteil'}),
                             'La Réunion'), expected)

    def test_reference_academy_is_not_user_context(self):
        from admin_retest_113_live import academy_for_replay
        self.assertEqual(academy_for_replay(self.state({'question':'Le guide Strasbourg 2024 suffit-il ?',
                         'academie':''}), 'Créteil'), 'Non précisée')

    def test_row_order_does_not_change_resolved_context(self):
        from admin_retest_113_live import academy_for_replay
        rows = [{'question':'Où est le lot ?','academie':''},
                {'question':'Où est le lot ?','academie':'Créteil'},
                {'question':'Quelle note à Aix-Marseille ?','academie':''}]
        expected = ['Non précisée','Créteil','Aix-Marseille']
        for previous in ('Créteil','La Réunion'):
            self.assertEqual([academy_for_replay(self.state(row),previous) for row in rows], expected)
            self.assertEqual([academy_for_replay(self.state(row),previous) for row in reversed(rows)], list(reversed(expected)))
