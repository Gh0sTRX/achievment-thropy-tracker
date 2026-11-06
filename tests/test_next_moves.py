import unittest
from copy import deepcopy
from datetime import date
from atlas.recommendations import next_moves


class NextMoveTests(unittest.TestCase):
    def sample(self):
        games=[{'id':str(i),'name':'Edition','platform':'xbox','platform_edition':str(i)} for i in range(5)]
        items=[{'id':f'{i}:{j}','game_id':str(i),'name':'Target','source':'CSV','unlocked':j<3,'unlock_time':''} for i in range(5) for j in range(4)]
        return {'games':games,'achievements':items,'complete_export':False}

    def test_max_three_distinct_editions_pin_first_and_no_mutation(self):
        lib=self.sample();before=deepcopy(lib)
        result=next_moves(lib,['4:3'],today=date(2026,11,6))
        self.assertEqual(len(result),3);self.assertEqual(result[0]['achievement_id'],'4:3')
        self.assertEqual(len({r['game_id'] for r in result}),3);self.assertEqual(lib,before)
        self.assertTrue(all('Kaynak: CSV' in r['reasons'] for r in result))
        self.assertTrue(all(any('kısmi/bilinmiyor' in x for x in r['reasons']) for r in result))

    def test_points_rarity_description_do_not_rank(self):
        lib=self.sample();before=next_moves(lib)
        for a in lib['achievements']:a.update(points=99999,ratio=.01,description='Easy')
        after=next_moves(lib)
        self.assertEqual([x['achievement_id'] for x in before],[x['achievement_id'] for x in after])
        self.assertEqual([x['reasons'] for x in before],[x['reasons'] for x in after])

    def test_only_earned_valid_recent_dates_count(self):
        for stamp,earned,expected in [('2026-11-01',True,True),('2026-11-01T23:30:00+03:00',True,True),('03/04/2026',True,False),('2026-11-07',True,False),('2026-01-01',True,False),('2026-11-01',False,False)]:
            lib=self.sample();lib['games']=lib['games'][:1];lib['achievements']=lib['achievements'][:4]
            for a in lib['achievements']:a['unlocked']=False
            lib['achievements'][0].update(unlocked=earned,unlock_time=stamp)
            result=next_moves(lib,today=date(2026,11,6))
            self.assertEqual(bool(result),expected,stamp)
            if result:self.assertTrue(result[0]['signals']['recent_unlock'])

    def test_blocked_and_earned_targets_not_suggested_even_if_pinned(self):
        lib=self.sample()
        for a in lib['achievements']:
            if not a['unlocked']:a['flag']=True
        self.assertEqual(next_moves(lib,[a['id'] for a in lib['achievements']]),[])
