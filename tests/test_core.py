import tempfile
import unittest
from pathlib import Path
from atlas.core import Library,build_library,parse_csv_text,game_id,normalize

class CoreTests(unittest.TestCase):
    EARN='GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,UnlockDate\nGame A,A,https://www.trueachievements.com/a123/a-achievement,20,23,1.15,,2026-01-01\n'
    LOCK='GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,Unachieveable\nGame A,B,https://www.trueachievements.com/a124/b-achievement,50,100,2.0,,\nGame A,C,https://www.trueachievements.com/a125/c-achievement,25,100,4.0,,True\n'
    def test_parse(self):
        x=build_library(self.EARN,self.LOCK,'PublicGamer')
        self.assertEqual(len(x['games']),1)
        self.assertEqual(len(x['achievements']),3)
        self.assertEqual(sum(a['unlocked'] for a in x['achievements']),1)
        self.assertEqual(sum(a['flag'] for a in x['achievements']),1)
    def test_no_invented_icons(self):
        x=build_library(self.EARN,self.LOCK)
        self.assertTrue(all(a['icon_url']=='' for a in x['achievements']))
    def test_state_persists(self):
        with tempfile.TemporaryDirectory() as td:
            a=Library(td);a.import_csv(self.EARN,self.LOCK,'PublicGamer')
            self.assertEqual(len(a.library['achievements']),3)
            a.set_pin('ta:124',True)
            b=Library(td);self.assertIn('ta:124',b.state['pins'])
            self.assertEqual(len(b.library['achievements']),3)
    def test_earned_not_revoked(self):
        with tempfile.TemporaryDirectory() as td:
            a=Library(td);a.import_csv(self.EARN,self.LOCK,'PublicGamer')
            # prior earned remains earned even if later locked CSV temporarily lists it
            a.import_csv('',self.LOCK+self.EARN.split('\n')[1].replace('2026-01-01','')+'\n','PublicGamer')
            self.assertTrue(next(x for x in a.library['achievements'] if x['id']=='ta:123')['unlocked'])
    def test_scope_exact_match(self):
        with tempfile.TemporaryDirectory() as td:
            a=Library(td);a.import_csv(self.EARN,self.LOCK)
            gid=a.library['games'][0]['id']
            result=a.apply_live_game(gid,[{'name':'B','gamerscore':50,'unlocked':True,'icon':'https://xboxlive.com/any.png','progress_current':3,'progress_target':5}])
            self.assertEqual(result['updated'],1)
            self.assertTrue(next(x for x in a.library['achievements'] if x['id']=='ta:124')['unlocked'])
    def test_xss_name_is_data(self):
        x=self.EARN.replace('Game A','<script>evil</script>')
        lib=build_library(x,self.LOCK)
        self.assertEqual(len(lib['games']),2)
    def test_no_account_mixing(self):
        with tempfile.TemporaryDirectory() as td:
            a=Library(td);a.state['linked_profile']={'gamertag':'Different'}
            with self.assertRaises(ValueError):a.import_csv(self.EARN,self.LOCK,'PublicGamer')
if __name__=='__main__':unittest.main()
class EmptyAndMigrationTests(unittest.TestCase):
    def test_new_library_has_no_fictional_data(self):
        with tempfile.TemporaryDirectory() as td:
            a=Library(td)
            self.assertEqual(a.library['games'],[])
            self.assertEqual(a.library['achievements'],[])

    def test_old_demo_removed_without_losing_session_or_real_rows(self):
        import json
        from fixtures import make_sample
        with tempfile.TemporaryDirectory() as td:
            demo=make_sample()
            real=build_library(CoreTests.EARN,CoreTests.LOCK,'Player')
            demo['games']+=real['games'];demo['achievements']+=real['achievements']
            Path(td,'library.json').write_text(json.dumps(demo))
            Path(td,'state.json').write_text(json.dumps({'pins':['demo:0:0','ta:124'],'linked_profile':{'gamertag':'Player','xuid':'222'}}))
            a=Library(td)
            self.assertEqual(len(a.library['games']),1)
            self.assertEqual(len(a.library['achievements']),3)
            self.assertEqual(a.state['linked_profile']['xuid'],'222')
            self.assertEqual(a.state['pins'],['ta:124'])
            self.assertTrue(Path(td,'migration-v06-demo-backup.json').exists())
            self.assertEqual(len(Library(td).library['achievements']),3)
