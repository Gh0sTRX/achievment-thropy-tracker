import unittest
from fixtures import make_sample
from atlas.recommendations import rank,insights

class RecommendTests(unittest.TestCase):
    def test_no_fake_progress(self):
        recommendations=rank(make_sample())
        self.assertTrue(recommendations)
        self.assertTrue(all(x['is_measured'] is False and x['progress'] is None for x in recommendations))
    def test_flagged_never_suggested(self):
        x=make_sample()
        for a in x['achievements']:
            if not a['unlocked']:a['flag']=True
        self.assertEqual(rank(x),[])
    def test_measured_progress(self):
        x=make_sample()
        target=next(a for a in x['achievements'] if not a['unlocked'])
        target['progress_current']=9;target['progress_target']=10
        rec=rank(x)
        self.assertTrue(any(r['achievement_id']==target['id'] and r['is_measured'] and r['progress']==.9 for r in rec))
    def test_pin_changes_priority(self):
        x=make_sample();target=next(a for a in x['achievements'] if not a['unlocked'])
        base={z['achievement_id']:z['score'] for z in rank(x,limit=50)}
        after={z['achievement_id']:z['score'] for z in rank(x,pins=[target['id']],limit=50)}
        self.assertAlmostEqual(after[target['id']]-base[target['id']],24)
    def test_insights_grouped(self):
        x=make_sample();r=insights(x)
        self.assertTrue('almost_done' in r and 'most_score' in r and 'at_risk' in r)
if __name__=='__main__':unittest.main()