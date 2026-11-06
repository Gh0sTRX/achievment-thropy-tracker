import unittest
from atlas import sync_control


class ReuseIdentityTests(unittest.TestCase):
    def test_edition_and_device_changes_force_fetch_and_groups_are_preserved(self):
        summary={'lastUnlock':'2026-11-06','currentAchievements':1,'totalAchievements':1}
        old={'id':'psn:1','platform':'psn','title_id':'NP1','platform_edition':'PS4','devices':['ps4'],'api_generation':'psn:1','trophy_groups':[{'id':'001','name':'DLC'}]}
        sync_control.mark(old,summary)
        item={'id':'psn:1:1','game_id':'psn:1','unlocked':True,'unlock_time':'2026-11-06'}
        cache={'id':'player','games':[old],'achievements':[item]}
        token=sync_control.context.set({'stop':lambda:False,'force':False,'cache':cache})
        try:
            for changes in ({'platform':'xbox'},{'title_id':'NP2'},{'platform_edition':'PS5'},{'devices':['ps5']}):
                changed={**old,**changes};self.assertIsNone(sync_control.reuse(changed,summary,'player'),changes)
            current={k:v for k,v in old.items() if k!='trophy_groups'}
            rows=sync_control.reuse(current,summary,'player')
            self.assertEqual(rows,[item]);self.assertEqual(current['trophy_groups'],old['trophy_groups'])
            current['trophy_groups'][0]['name']='changed';rows[0]['unlocked']=False
            self.assertEqual(old['trophy_groups'][0]['name'],'DLC');self.assertTrue(item['unlocked'])
        finally:sync_control.context.reset(token)
