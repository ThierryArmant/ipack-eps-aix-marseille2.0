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
                      {'is_admin':True,'audit113_batch':{'waiting':True,'index':1,'rows':[{'academie':'Grenoble'}]}},
                      {'is_admin':True,'audit113_batch':{'waiting':True,'index':0,'rows':[{'academie':''}]}}]:
            self.assertEqual(academy_for_replay(state,'Créteil'),'Créteil')
