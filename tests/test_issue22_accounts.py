import json,os,tempfile,unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from atlas.server import Controller
from atlas import accounts,settings,public_profiles as public,media_sync,recommendations

class AccountsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.env=patch.dict(os.environ,{},clear=False);self.env.start();self.addCleanup(self.env.stop)
  for k in settings.FIELDS:os.environ.pop(k,None)
  self.c=Controller(self.tmp.name)
 def test_setup_consent_secrets_and_configured_not_authenticated(self):
  with self.assertRaises(ValueError):self.c.provider_setup({'platform':'psn','username':'PsnPlayer','secret':'a'*64})
  r=self.c.provider_setup({'platform':'psn','username':'PsnPlayer','secret':'a'*64,'consent':True})
  access=accounts.snapshot(self.c.store);self.assertEqual(access['psn']['state'],'configured');self.assertEqual(access['pc']['state'],'not_configured');self.assertNotIn('a'*64,json.dumps(self.c.status()))
  self.assertEqual(self.c.store.state['provider_inputs'],{'psn':'PsnPlayer'});self.assertFalse(settings.status()['auto_guides'])
 def test_test_connection_is_not_profile_or_paid_guide_sync(self):
  self.c.provider_setup({'platform':'pc','username':'SteamPlayer','secret':'b'*32})
  before=deepcopy(self.c.store.library)
  with patch('atlas.accounts.probe',return_value={'id':'76561198000000000','username':'SteamPlayer'}),patch('atlas.guides.create') as guide,patch('atlas.public_profiles.fetch') as fetch:
   r=self.c.provider_test({'platform':'pc','username':'SteamPlayer'})
  self.assertEqual(r['state'],'verified');self.assertEqual(before,self.c.store.library);guide.assert_not_called();fetch.assert_not_called();self.assertEqual(accounts.snapshot(self.c.store)['psn']['state'],'not_configured')
 def test_expired_private_rate_limit_and_redaction(self):
  self.c.provider_setup({'platform':'pc','username':'SteamPlayer','secret':'b'*32})
  for code,state in [(401,'expired'),(403,'expired'),(429,'rate_limited')]:
   with patch('atlas.accounts.probe',side_effect=HTTPError('https://service/?key=SECRET',code,'SECRET',{},None)):
    r=self.c.provider_test({'platform':'pc','username':'SteamPlayer'})
   self.assertEqual(r['state'],state);self.assertNotIn('SECRET',json.dumps(r))
  with patch('atlas.accounts.probe',side_effect=ValueError('Oyun ayrıntıları gizli')):self.assertEqual(self.c.provider_test({'platform':'pc','username':'SteamPlayer'})['state'],'private')
 def test_official_steam_probe_and_unofficial_psn_probe_use_authorized_provider(self):
  with patch('atlas.steam.request',side_effect=[{'response':{'success':1,'steamid':'76561198000000000'}},{'response':{'game_count':0}}]) as request:
   self.assertEqual(accounts.probe('pc','Vanity')['id'],'76561198000000000');self.assertEqual(request.call_count,2)
  user=SimpleNamespace(account_id='psn-account',online_id='PsnPlayer',trophy_titles=lambda limit:iter([]))
  fake=SimpleNamespace(PSNAWP=lambda secret:SimpleNamespace(user=lambda online_id:user))
  with patch.dict('sys.modules',{'psnawp_api':fake}):self.assertEqual(accounts.probe('psn','PsnPlayer')['id'],'psn-account')
 def test_history_platform_and_all_failed_titles_preserved(self):
  self.c.record_activity('psn','profile',{'message':'Partial','report':{'failed_titles':[{'game':'Game '+str(i)} for i in range(4)]}})
  self.c.record_activity('pc','media',{'message':'Stopped','cancelled':True})
  events=self.c.store.state['activity_history'];self.assertEqual(len(events[0]['report']['failed_titles']),4);self.assertEqual(events[1]['platform'],'pc');self.assertTrue(events[1]['cancelled'])
 def test_apps_preserved_but_not_recommended_or_downloaded(self):
  s=self.c.store;s.library['games']=[{'id':'app1','name':'Internet Explorer','platform':'xbox','cover_url':'https://xboxlive.com/a'}];s.library['achievements']=[{'id':'app-ach','game_id':'app1','name':'App item','platform':'xbox','points':0,'unlocked':False}]
  with patch('atlas.artwork.fetch') as fetch:r=media_sync.download(s)
  fetch.assert_not_called();self.assertEqual(r['planned'],0);self.assertEqual(recommendations.rank(s.library),[]);self.assertEqual(len(s.library['games']),1)
 def test_csv_records_notes_pins_and_dates_survive_first_same_account_sync(self):
  s=self.c.store;s.library['gamertag']='Player';s.library['games']=[{'id':'csv-game','name':'CSV','platform':'xbox','notes':'keep'}];s.library['achievements']=[{'id':'ta:1','game_id':'csv-game','name':'Old','source':'trueachievements_csv','platform':'xbox','unlocked':True,'unlock_time':'2020-01-01'}];s.state['pins']=['ta:1'];s.save()
  g=public.game('xbox','12','New API title','360');a=public.achievement(g,{'id':'1','name':'New','unlocked':False})
  snapshot={'platform':'xbox','id':'123','username':'Player','synced_at':'2026-11-05','games':[g],'achievements':[a]}
  before=deepcopy(s.library)
  with self.assertRaises(ValueError):s.apply_public_profile({**snapshot,'username':'OtherPlayer'})
  self.assertEqual(s.library,before);s.apply_public_profile(snapshot)
  self.assertIn('ta:1',s.state['pins']);self.assertEqual(next(x for x in s.library['games'] if x['id']=='csv-game')['notes'],'keep');self.assertEqual(next(x for x in s.library['achievements'] if x['id']=='ta:1')['unlock_time'],'2020-01-01')
 def test_title_candidates_require_confirmed_edition_and_do_not_cross_platform(self):
  self.c.store.library['games']=[{'id':'csv','name':'Minecraft','platform':'xbox','notes':'keep'}]
  self.c.active_matches=[{'titleId':'12','name':'Minecraft','platform':'360','devices':['Xbox360'],'cover_url':'https://xboxlive.com/cover'},{'titleId':'12','name':'Minecraft','platform':'one'}]
  with self.assertRaises(ValueError):self.c.xbox_map({'game_id':'csv','title_id':'12','edition':'360'})
  self.c.xbox_map({'game_id':'csv','title_id':'12','edition':'360','confirmed':True})
  g=self.c.store.library['games'][0];self.assertEqual(g['platform_edition'],'360');self.assertEqual(g['devices'],['xbox360']);self.assertEqual(g['notes'],'keep')
 def test_enrichment_rejects_other_authenticated_account(self):
  self.c.store.library['gamertag']='CSVPlayer';self.c.store.library['games']=[{'id':'csv','name':'Game','platform':'xbox','title_id':'12','platform_edition':'360'}]
  with patch('atlas.xbox.account_info',return_value={'xuid':'123','gamertag':'OtherPlayer'}),patch('atlas.xbox.title_achievements') as fetch:
   with self.assertRaises(ValueError):self.c.preview_enrichment({'game_id':'csv'})
  fetch.assert_not_called()
