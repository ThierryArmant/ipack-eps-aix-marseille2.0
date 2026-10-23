import unittest
from documentary_review import filter_diploma_passages, validate_claims

class DiplomaPassageFilterTests(unittest.TestCase):
    def setUp(self):
        self.packet = {'id':'D1','path':'data/example.txt','text':'original intact', 'passages':[
            {'id':'D1P1','text':'Au bac GT, vérifier la première valeur et la répartition.'},
            {'id':'D1P2','text':'Au bac professionnel ou au CAP uniquement, vérifier le choix.'},
            {'id':'D1P3','text':'Si le lot est verrouillé, demander à la direction.'}]}
    def select(self, question='', public='Lycée Général & Techno'):
        audit={};result=filter_diploma_passages([self.packet],question,public,audit)
        return [p['id'] for p in result[0]['passages']],audit,result
    def test_gt_keeps_full_gt_and_common_passages(self):
        ids,audit,result=self.select()
        self.assertEqual(ids,['D1P1','D1P3'])
        self.assertEqual(audit['excluded_diploma_passages'][0]['passage_id'],'D1P2')
        self.assertIs(result[0]['passages'][0],self.packet['passages'][0])
        self.assertEqual(len(self.packet['passages']),3)
    def test_question_diploma_overrides_selector(self):
        self.assertEqual(self.select('Au bac professionnel, que faire ?')[0],['D1P2','D1P3'])
    def test_pro_cap_keeps_compatible_branch(self):
        self.assertEqual(self.select(public='Lycée Pro / CAP')[0],['D1P2','D1P3'])
    def test_comparison_unknown_and_mixed_preserved(self):
        for q,pub in [('Comparer bac GT et bac pro','Lycée Général & Techno'),('','Non précisé')]:
            self.assertEqual(len(self.select(q,pub)[0]),3)
        self.packet['passages'][1]['text']='Au bac professionnel, une action.\nUne étape commune sans portée explicite.'
        self.assertEqual(len(self.select()[0]),3)
