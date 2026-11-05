import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from atlas import steam,public_profiles
from test_steam import responses,SID

class SteamSchemaCacheTests(unittest.TestCase):
    def test_warm_cache_skips_only_schema_and_preserves_fresh_player_state(self):
        with TemporaryDirectory() as root:
            cache={'schema_root':root};earned=1;calls=[]
            def request(*args,**kw):
                calls.append(args[1]);result=responses(*args,**kw)
                if args[1]=='GetPlayerAchievements':result['playerstats']['achievements'][0]['achieved']=earned
                return result
            with patch.object(steam,'request',side_effect=request):
                first=public_profiles.fetch('pc',SID,cache=cache)
                self.assertTrue(first['achievements'][0]['unlocked']);self.assertEqual(len(calls),3)
                calls.clear();earned=0
                second=public_profiles.fetch('pc',SID,cache=cache)
                self.assertFalse(second['achievements'][0]['unlocked'])
                self.assertEqual(calls,['GetOwnedGames','GetPlayerAchievements'])
            saved=json.loads((Path(root)/'10-english.json').read_text())
            self.assertNotIn(SID,json.dumps(saved));self.assertNotIn('unlocktime',json.dumps(saved))
    def test_expiry_force_corruption_and_future_timestamp_refetch(self):
        with TemporaryDirectory() as root:
            cache={'schema_root':root};path=Path(root)/'10-english.json'
            with patch.object(steam,'request',side_effect=responses):public_profiles.fetch('pc',SID,cache=cache)
            original=path.read_text()
            for scenario in ('expired','future','corrupt','force','wrong-app','version','bad-schema'):
                path.write_text(original);data=json.loads(original)
                if scenario=='expired':data['fetched_at']=0
                if scenario=='future':data['fetched_at']=10**12
                if scenario=='wrong-app':data['appid']='20'
                if scenario=='version':data['version']=99
                if scenario=='bad-schema':data['schema']=[]
                path.write_text('not-json' if scenario=='corrupt' else json.dumps(data))
                with self.subTest(scenario=scenario),patch.object(steam,'request',side_effect=responses) as request:
                    public_profiles.fetch('pc',SID,cache=cache,force=scenario=='force')
                    self.assertEqual(sum(c.args[1]=='GetSchemaForGame' for c in request.call_args_list),1)
    def test_new_player_api_name_refreshes_schema_once(self):
        from copy import deepcopy
        with TemporaryDirectory() as root:
            cache={'schema_root':root}
            with patch.object(steam,'request',side_effect=responses):public_profiles.fetch('pc',SID,cache=cache)
            def request(*args,**kw):
                data=responses(*args,**kw)
                if args[1]=='GetSchemaForGame':
                    row=deepcopy(data['game']['availableGameStats']['achievements'][0]);row['name']='NEW_API';data['game']['availableGameStats']['achievements'].append(row)
                if args[1]=='GetPlayerAchievements':data['playerstats']['achievements'].append({'apiname':'NEW_API','achieved':0})
                return data
            with patch.object(steam,'request',side_effect=request) as call:
                result=public_profiles.fetch('pc',SID,cache=cache)
                self.assertEqual(len(result['achievements']),2)
                self.assertEqual(sum(c.args[1]=='GetSchemaForGame' for c in call.call_args_list),1)
    def test_cache_write_failure_does_not_break_profile(self):
        with TemporaryDirectory() as root,patch.object(steam,'request',side_effect=responses),patch('atlas.core.atomic_write',side_effect=OSError('disk full')):
            result=public_profiles.fetch('pc',SID,cache={'schema_root':root})
            self.assertEqual(len(result['achievements']),1)
    def test_empty_schema_is_not_negative_cached(self):
        def request(*args,**kw):
            if args[1]=='GetSchemaForGame':return {'game':{'gameName':'No achievements'}}
            return responses(*args,**kw)
        with TemporaryDirectory() as root,patch.object(steam,'request',side_effect=request) as call:
            for _ in range(2):public_profiles.fetch('pc',SID,cache={'schema_root':root})
            self.assertEqual(sum(c.args[1]=='GetSchemaForGame' for c in call.call_args_list),2)
    def test_invalid_appid_cannot_create_cache_path(self):
        for value in ('../outside','0','4294967296'):
            with self.subTest(value=value),self.assertRaises(ValueError):steam.schema_for(value)

    def test_hundred_game_request_budget(self):
        def request(*args,**kw):
            if args[1]=='GetOwnedGames':return {'response':{'game_count':100,'games':[{'appid':i,'name':'Game '+str(i)} for i in range(1,101)]}}
            return responses(*args,**kw)
        with TemporaryDirectory() as root,patch.object(steam,'request',side_effect=request) as call:
            cache={'schema_root':root}
            first=public_profiles.fetch('pc',SID,cache=cache);cold=call.call_count;call.reset_mock()
            second=public_profiles.fetch('pc',SID,cache=cache);warm=call.call_count
            self.assertEqual((cold,warm),(201,101))
            self.assertEqual(len(first['achievements']),100);self.assertEqual(first['achievements'],second['achievements'])
            self.assertEqual(sum(c.args[1]=='GetPlayerAchievements' for c in call.call_args_list),100)
