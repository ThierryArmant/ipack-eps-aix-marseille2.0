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
