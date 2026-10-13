import unittest
from response_cache import AnswerCache, answer_key


class ResponseCacheTests(unittest.TestCase):
    def key(self, question='Une question ?', **changes):
        args=dict(academy='Aix-Marseille',public='GT',mode='examens',version='v1',model='mini',knowledge='k1')
        args.update(changes)
        return answer_key(question,**args)

    def test_same_question_reuses_copy_without_model_or_shared_mutation(self):
        cache=AnswerCache()
        cache.put(self.key(),{'messages':[{'content':'Réponse validée'}]})
        hit=cache.get(self.key('  UNE  question ? '))
        self.assertIsNotNone(hit)
        hit['messages'][0]['content']='modifié'
        self.assertEqual(cache.get(self.key())['messages'][0]['content'],'Réponse validée')

    def test_every_material_context_change_misses(self):
        cache=AnswerCache()
        cache.put(self.key(),{'answer':'old'})
        for changes in ({'academy':'Créteil'},{'public':'Pro'},{'version':'v2'},{'model':'other'},
                        {'knowledge':'k2'},{'mode':'ipack'},{'selected_context':['ipack','GT']}):
            self.assertIsNone(cache.get(self.key(**changes)))

    def test_numbers_accents_and_negation_do_not_collide(self):
        for a,b in [('une épreuve','deux épreuves'),('15 jours','5 jours'),('il peut','il ne peut pas'),('été','ete')]:
            self.assertNotEqual(self.key(a),self.key(b))

    def test_lru_is_bounded(self):
        cache=AnswerCache(capacity=2)
        cache.put('a',1);cache.put('b',2);cache.get('a');cache.put('c',3)
        self.assertIsNone(cache.get('b'))
        self.assertEqual(cache.get('a'),1)


if __name__=='__main__':
    unittest.main()
