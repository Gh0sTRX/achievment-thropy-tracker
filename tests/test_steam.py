import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from atlas import steam,public_profiles,sync_control
from atlas.core import Library
SID='76561198000000000'

def responses(interface,method,version='v1',**params):
    if method=='ResolveVanityURL':return {'response':{'success':1,'steamid':SID}}
    if method=='GetOwnedGames':return {'response':{'game_count':1,'games':[{'appid':10,'name':'Same Name'}]}}
    if method=='GetSchemaForGame':return {'game':{'gameName':'Same Name','availableGameStats':{'achievements':[{'name':'API_FIRST','displayName':'First','description':'Do it','hidden':1,'icon':'https://cdn.akamai.steamstatic.com/icon.jpg','icongray':'https://cdn.akamai.steamstatic.com/gray.jpg'}]}}}
    if method=='GetPlayerAchievements':return {'playerstats':{'success':True,'steamID':SID,'achievements':[{'apiname':'API_FIRST','achieved':1,'unlocktime':1700000000}]}}
    raise AssertionError(method)

class SteamTests(unittest.TestCase):
    def test_official_id_schema_and_no_gamerscore(self):
        with patch.object(steam,'request',side_effect=responses):result=public_profiles.fetch('pc','https://steamcommunity.com/id/AtlasTest')
        a=result['achievements'][0];g=result['games'][0]
        self.assertEqual(result['id'],SID);self.assertEqual(a['id'],'steam:10:API_FIRST')
        self.assertEqual(g['id'],'steam:10');self.assertEqual(a['points'],0);self.assertEqual(a['trophy_type'],'')
        self.assertTrue(a['is_secret']);self.assertTrue(a['unlock_time'].endswith('+00:00'))
        self.assertEqual(g['steam_appid'],'10');self.assertEqual(len(g['art_candidates']),4)
    def test_missing_player_id_is_not_locked_or_earned(self):
        def request(*args,**kwargs):
            data=responses(*args,**kwargs)
            if args[1]=='GetPlayerAchievements':data['playerstats'].pop('steamID')
            return data
        with patch.object(steam,'request',side_effect=request),self.assertRaisesRegex(ValueError,'önceki arşiv'):public_profiles.fetch('pc',SID)
    def test_private_does_not_create_empty_snapshot(self):
        with patch.object(steam,'request',return_value={'response':{}}),self.assertRaisesRegex(ValueError,'gizli'):public_profiles.fetch('pc',SID)
    def test_rate_limit_aborts_instead_of_committing_partial(self):
        def request(*args,**kwargs):
            if args[1]=='GetPlayerAchievements':raise steam.SteamError('Rate limited',429)
            return responses(*args,**kwargs)
        with patch.object(steam,'request',side_effect=request),self.assertRaises(ValueError):public_profiles.fetch('pc',SID)
    def test_partial_failure_preserves_old_game_and_other_pc_provider(self):
        with patch.object(steam,'request',side_effect=responses):old=public_profiles.fetch('pc',SID)
        with TemporaryDirectory() as root:
            store=Library(root);store.apply_public_profile(old)
            store.library['games'].append({'id':'xbox:10','title_id':'10','platform':'xbox','name':'Same Name'})
            store.library['games'].append({'id':'gog:10','platform':'pc','provider':'gog','name':'Same Name'})
            def request(*args,**kwargs):
                if args[1]=='GetOwnedGames':return {'response':{'game_count':2,'games':[{'appid':10,'name':'Same Name'},{'appid':20,'name':'No Trophies'}]}}
                if str(kwargs.get('appid'))=='10':raise steam.SteamError('Network')
                if args[1]=='GetSchemaForGame':return {'game':{'gameName':'No Trophies'}}
                return responses(*args,**kwargs)
            with patch.object(steam,'request',side_effect=request):new=public_profiles.fetch('pc',SID)
            store.apply_public_profile(new)
            self.assertEqual({g['id'] for g in store.library['games']},{'steam:10','steam:20','gog:10','xbox:10'})
            self.assertEqual(len(store.library['games']),4,'same numeric title ID must not duplicate another platform')
            self.assertTrue(store.library['achievements'][0]['unlocked'])
    def test_cancel_between_requests(self):
        stopped=False
        def request(*args,**kwargs):
            nonlocal stopped
            data=responses(*args,**kwargs);stopped=True;return data
        with patch.object(steam,'request',side_effect=request),self.assertRaises(sync_control.Cancelled):public_profiles.fetch('pc',SID,stop=lambda:stopped)
    def test_validation_rejects_other_hosts_and_credentials(self):
        for value in ['https://evil.com/id/Atlas','https://steamcommunity.com@evil.com/id/a','https://steamcommunity.com/profiles/nope','123','https://steamcommunity.com/id/test?key=secret']:
            with self.subTest(value=value),self.assertRaises(ValueError):steam.validate(value)
    def test_transport_failure_does_not_leak_key(self):
        from urllib.error import URLError
        with patch.object(steam.settings,'get',return_value='SENSITIVE'),patch.object(steam,'build_opener') as opener:
            opener.return_value.open.side_effect=URLError('https://example/?key=SENSITIVE')
            with self.assertRaises(ValueError) as error:steam.request('IPlayerService','GetOwnedGames',steamid=SID)
        self.assertNotIn('SENSITIVE',str(error.exception))
