import json
import tempfile
import threading
import unittest
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from atlas.server import LocalApp

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=LocalApp(self.tmp.name)
        self.thread=threading.Thread(target=self.app.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.app.shutdown();self.app.server_close();self.tmp.cleanup()
    def test_health_and_html(self):
        with urlopen(self.app.url+'api/data') as r:
            x=json.load(r)
        self.assertEqual(len(x['library']['library']['games']),0)
        with urlopen(self.app.url) as r:
            html=r.read().decode()
        self.assertIn('Achievement Atlas',html)
        self.assertNotIn('__TOKEN__',html)
    def test_profile_action_requires_configuration_and_token(self):
        from unittest.mock import patch
        with patch.dict('os.environ', {'ATLAS_PSN_NPSSO':'','ATLAS_XBOX_TOKEN_FILE':'','BRAVE_SEARCH_API_KEY':'','OPENAI_API_KEY':''}):
            body=json.dumps({'platform':'psn','username':'Player1'}).encode()
            req=Request(self.app.url+'api/profiles/sync',data=body,headers={'Content-Type':'application/json','X-Atlas-Token':self.app.token},method='POST')
            with self.assertRaises(HTTPError) as ctx:urlopen(req)
            self.assertEqual(ctx.exception.code,400)
            error=json.loads(ctx.exception.read())['error']
            self.assertIn('kurulmamış',error)
            with urlopen(self.app.url+'api/data') as r:data=json.load(r)
            self.assertEqual(data['providers'],{'psn':False,'xbox':False})
            self.assertFalse(data['guides_ready'])

    def test_post_requires_token(self):
        req=Request(self.app.url+'api/pin',data=b'{"id":"demo:0:0","pinned":true}',headers={'Content-Type':'application/json'},method='POST')
        with self.assertRaises(HTTPError) as ctx:urlopen(req)
        self.assertEqual(ctx.exception.code,403)
    def test_import_end_to_end(self):
        body=json.dumps({'earned':'GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,UnlockDate\nDemo,First,https://www.trueachievements.com/a456/first-achievement,50,70,1.4,,2026-01-01\n','locked':'GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,Unachieveable\nDemo,Second,https://www.trueachievements.com/a457/second-achievement,40,60,1.5,,\n','gamertag':'Test'}).encode()
        req=Request(self.app.url+'api/import',data=body,headers={'Content-Type':'application/json','X-Atlas-Token':self.app.token},method='POST')
        with urlopen(req) as r:result=json.load(r)
        self.assertEqual(result['achievements'],2)
        with urlopen(self.app.url+'api/data') as r:data=json.load(r)
        self.assertEqual(data['library']['library']['gamertag'],'Test')
if __name__=='__main__':unittest.main()
class PlatformReportTests(unittest.TestCase):
    def test_psn_trophies_do_not_become_xbox_gamerscore(self):
        from atlas.server import Controller
        with tempfile.TemporaryDirectory() as root:
            c=Controller(root)
            c.store.library['games']=[{'id':'xgame','name':'Xbox','platform':'xbox'},{'id':'pgame','name':'PSN','platform':'psn'}]
            c.store.library['achievements']=[{'id':'xa','game_id':'xgame','name':'Actual','points':30,'unlocked':False}, {'id':'pa','game_id':'pgame','name':'Actual trophy','points':0,'unlocked':False}]
            reports=c.status()['platform_reports']
            self.assertEqual([a['achievement_id'] for a in reports['xbox']['recommendations']],['xa'])
            self.assertEqual([a['achievement_id'] for a in reports['psn']['recommendations']],['pa'])
            self.assertEqual(reports['pc']['recommendations'],[])
