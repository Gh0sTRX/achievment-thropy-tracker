import asyncio
from contextlib import asynccontextmanager
from enum import Enum
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from atlas import public_profiles as public, guides
from atlas.core import Library
from atlas.server import Controller


def snapshot(platform='xbox', player='1', earned=False):
    g = public.game(platform, 'title1', 'Same Game', 'one')
    a = public.achievement(g, {'id': '0', 'name': 'First', 'unlocked': earned,
        'description': 'Finish the chapter', 'gamerscore': 10})
    return {'platform': platform, 'id': player, 'username': 'Player'+player,
            'synced_at': '2026-01-01', 'games': [g], 'achievements': [a]}


class PublicStorageTests(unittest.TestCase):
    def test_two_platforms_and_players_stay_separate(self):
        with TemporaryDirectory() as root:
            store = Library(root)
            store.apply_public_profile(snapshot(earned=True))
            store.apply_public_profile(snapshot('psn'))
            self.assertEqual(len(store.library['games']), 2)
            store.apply_public_profile(snapshot(player='2'))
            xbox = next(a for a in store.library['achievements'] if a['platform']=='xbox')
            self.assertFalse(xbox['unlocked'])
            store.apply_public_profile(snapshot(player='1'))
            xbox = next(a for a in store.library['achievements'] if a['platform']=='xbox')
            self.assertTrue(xbox['unlocked'])
            self.assertEqual(len(Library(root).library['games']), 2)

    def test_guides_survive_switch_and_unlocks_not_revoked(self):
        with TemporaryDirectory() as root:
            store = Library(root)
            store.apply_public_profile(snapshot(earned=True))
            store.library['achievements'][0]['guide']={'steps':['Do this']}
            store.apply_public_profile(snapshot(player='2'))
            store.apply_public_profile(snapshot())
            self.assertTrue(store.library['achievements'][0]['unlocked'])
            self.assertEqual(store.library['achievements'][0]['guide']['steps'], ['Do this'])

    def test_unconfigured_service_does_not_start_or_change_library(self):
        with TemporaryDirectory() as root, patch.dict('os.environ', {}, clear=True):
            controller=Controller(root)
            before=json.dumps(controller.store.library)
            with self.assertRaises(ValueError):
                controller.public_sync({'platform':'psn','username':'Player1'})
            self.assertEqual(before,json.dumps(controller.store.library))

    def test_failure_preserves_library(self):
        import time
        with TemporaryDirectory() as root, patch.dict('os.environ', {'ATLAS_PSN_NPSSO':'test'}), patch.object(public,'fetch',side_effect=ValueError('Private profile')):
            controller=Controller(root)
            before=json.dumps(controller.store.library)
            controller.public_sync({'platform':'psn','username':'Player1'})
            deadline=time.monotonic()+2
            while controller.public_guard.locked() and time.monotonic()<deadline:
                time.sleep(.005)
            self.assertFalse(controller.public_guard.locked())
            self.assertEqual(before,json.dumps(controller.store.library))
            self.assertEqual(controller.store.status['public_job']['error'],'Private profile')


class ProviderTests(unittest.TestCase):
    def test_validates_ids(self):
        self.assertEqual(public.validate('xbox',' Gh0sTRX55 '),'Gh0sTRX55')
        self.assertEqual(public.validate('psn','Gh0sTRX55'),'Gh0sTRX55')
        for platform,name in [('psn','../etc'),('other','Player'),('xbox','https://foo')]:
            with self.assertRaises(ValueError):public.validate(platform,name)

    def test_pagination_and_loop_detection(self):
        calls=[]
        pages=iter([{'titles':[1],'pagingInfo':{'continuationToken':'opaque+/='}}, {'titles':[2]}])
        async def get(url,**kwargs):
            calls.append(kwargs['params'].copy())
            payload=next(pages)
            return SimpleNamespace(raise_for_status=lambda:None,json=lambda:payload)
        client=SimpleNamespace(session=SimpleNamespace(get=get))
        self.assertEqual(asyncio.run(public._pages(client,'https://example.test',{},'titles')),[1,2])
        self.assertEqual(calls[1]['continuationToken'],'opaque+/=')
        pages=iter([{'titles':[],'continuationToken':'again'}]*2)
        with self.assertRaises(ValueError):asyncio.run(public._pages(client,'https://example.test',{},'titles'))

    def test_psn_uses_target_and_all_groups_with_progress(self):
        class Platform(Enum): PS4='PS4'
        title=SimpleNamespace(np_communication_id='NPWR00001_00', title_platform={Platform.PS4}, title_name='Game', title_icon_url='https://image.api.playstation.com/cover.png')
        trophy=SimpleNamespace(trophy_id=0,earned=True,earned_date_time=None,trophy_name='First',trophy_detail='Finish',trophy_icon_url='https://image.api.playstation.com/trophy.png',trophy_group_id='001',trophy_type=SimpleNamespace(value='bronze'),progress=None,trophy_progress_target_value=None)
        calls=[]
        def trophies(*args,**kwargs):calls.append(kwargs);return [trophy]
        user=SimpleNamespace(account_id='12',online_id='Player1',trophy_titles=lambda **k:[title],trophies=trophies)
        sdk=SimpleNamespace(PSNAWP=lambda secret:SimpleNamespace(user=lambda **k:user))
        with patch.dict('sys.modules', {'psnawp_api':sdk}), patch.dict('os.environ',{'ATLAS_PSN_NPSSO':'test'}):
            result=public.fetch('psn','Player1')
        self.assertEqual(result['achievements'][0]['trophy_type'],'bronze')
        self.assertTrue(result['achievements'][0]['unlocked'])
        self.assertEqual(calls[0]['trophy_group_id'],'all')
        self.assertTrue(calls[0]['include_progress'])

    def test_sdk_error_does_not_expose_credentials(self):
        with patch.object(public,'_psn',side_effect=RuntimeError('secret-token')):
            with self.assertRaises(ValueError) as exc:public.fetch('psn','Player1')
        self.assertNotIn('secret-token',str(exc.exception))


class GuideTests(unittest.TestCase):
    def test_sources_and_translation_are_saved(self):
        a=snapshot()['achievements'][0]
        replies=[{'web':{'results':[{'url':'https://example.org/guide','title':'Guide','description':'Finish chapter one'}]}},
                 {'choices':[{'message':{'content':json.dumps({'description_tr':'Bölümü bitir','steps':['İlk bölümü tamamla'],'limitations':'','source_indices':[0]})}}]}]
        with patch.dict('os.environ',{'BRAVE_SEARCH_API_KEY':'test','OPENAI_API_KEY':'test'}), patch.object(guides,'_json',side_effect=replies):
            result=guides.create(a)
        self.assertEqual(result['status'],'generated')
        self.assertEqual(result['sources'][0]['url'],'https://example.org/guide')
        self.assertEqual(result['fingerprint'],guides.fingerprint(a))

    def test_unsupported_steps_not_shown(self):
        a=snapshot()['achievements'][0]
        replies=[{'web':{'results':[{'url':'https://example.org','description':'Snippet'}]}},
                 {'choices':[{'message':{'content':json.dumps({'steps':['Invented'],'source_indices':[999]})}}]}]
        with patch.dict('os.environ',{'BRAVE_SEARCH_API_KEY':'test','OPENAI_API_KEY':'test'}),patch.object(guides,'_json',side_effect=replies):
            result=guides.create(a)
        self.assertEqual(result['steps'],[])
        self.assertEqual(result['status'],'insufficient_sources')

class XboxTargetTests(unittest.TestCase):
    def test_all_requests_use_target_not_service_account(self):
        calls=[]
        async def profile_by_name(name):
            self.assertEqual(name,'Player1')
            return {'profileUsers':[{'id':'222','settings':[{'id':'Gamertag','value':'Player1'}]}]}
        async def get(url, **kwargs):
            calls.append((url,kwargs))
            if '/history/titles' in url:
                raw={'titles':[{'titleId':123,'name':'Game'}] if kwargs['headers']['x-xbl-contract-version']=='2' else []}
            else:
                raw={'achievements':[{'id':'1','name':'First','progressState':'Achieved','description':'Finish','rewards':[],'mediaAssets':[]}]}
            return SimpleNamespace(raise_for_status=lambda:None,json=lambda:raw)
        client=SimpleNamespace(profile=SimpleNamespace(get_profile_by_gamertag=profile_by_name),session=SimpleNamespace(get=get))
        @asynccontextmanager
        async def service(path):yield client,'111'
        with patch.dict('os.environ',{'ATLAS_XBOX_TOKEN_FILE':'/unused'}),patch.object(public.xbox,'authenticated_client',service):
            identity, games, items=asyncio.run(public._xbox('Player1',lambda *args:None))
        self.assertEqual(identity['id'],'222')
        self.assertEqual(len(items),1)
        self.assertTrue(all('/xuid(222)/' in url for url,_ in calls))
        self.assertTrue(items[0]['unlocked'])

class ConnectionSyncTests(unittest.TestCase):
    def test_reconnect_automatically_imports_remote_library(self):
        import time
        from atlas import xbox
        with TemporaryDirectory() as root, patch.object(xbox,'account_info',return_value=None):
            async def info():return {'gamertag':'Player1','xuid':'1'}
            with patch.object(xbox,'account_info',info),patch.object(public,'readiness',return_value={'xbox':True,'psn':False}),patch.object(public,'fetch',return_value=snapshot(earned=True)):
                c=Controller(root)
                c.xbox_reconnect()
                deadline=time.monotonic()+2
                while c.public_guard.locked() and time.monotonic()<deadline:time.sleep(.005)
                self.assertEqual(len(c.store.library['achievements']),1)
                self.assertTrue(c.store.library['achievements'][0]['unlocked'])
                self.assertEqual(c.data_status()['state'],'stored')

    def test_connected_without_data_is_not_reported_as_synced(self):
        with TemporaryDirectory() as root:
            c=Controller(root);c.store.status['connected']=True
            self.assertEqual(c.data_status()['state'],'empty')
            self.assertIn('henüz',c.data_status()['message'])

    def test_saved_oauth_session_is_available_for_username_lookup(self):
        from atlas import xbox
        with patch.dict('os.environ',{'ATLAS_XBOX_TOKEN_FILE':''}),patch.object(xbox,'has_tokens',return_value=True):
            self.assertTrue(public.readiness()['xbox'])

    def test_empty_remote_result_is_not_a_successful_sync(self):
        with patch.object(public,'_psn',return_value=({'id':'1','username':'Player1'},[],[])):
            with self.assertRaisesRegex(ValueError,'alınamadı'):public.fetch('psn','Player1')

class IdentifierRegressionTests(unittest.TestCase):
    def test_zero_and_missing_name_and_explicit_aliases(self):
        from atlas.xbox import normalize_achievements
        records=normalize_achievements({'achievements':[
            {'id':0,'name':'','unlocked':True,'gamerscore':5},
            {'achievementId':12,'name':'Actual achievement','unlocked':False},
        ]},True)
        self.assertEqual([a['id'] for a in records],['0','12'])
        self.assertTrue(records[0]['unlocked'])
        self.assertIn('adı alınamadı',records[0]['name'])

    def test_bad_game_does_not_discard_valid_game(self):
        calls=[]
        async def profile(name):return {'profileUsers':[{'id':'222','settings':[{'id':'Gamertag','value':'Player1'}]}]}
        async def get(url,**kw):
            if '/history/titles' in url:
                raw={'titles':[{'titleId':1,'name':'Valid'},{'titleId':2,'name':'Missing ID'}] if kw['headers']['x-xbl-contract-version']=='1' else []}
            elif kw['params']['titleId']=='1':raw={'achievements':[{'id':0,'name':'Real','unlocked':True}]}
            else:raw={'achievements':[{'name':'No ID','unlocked':False}]}
            return SimpleNamespace(raise_for_status=lambda:None,json=lambda:raw)
        client=SimpleNamespace(profile=SimpleNamespace(get_profile_by_gamertag=profile),session=SimpleNamespace(get=get))
        @asynccontextmanager
        async def service(path):yield client,'111'
        with patch.dict('os.environ',{'ATLAS_XBOX_TOKEN_FILE':'unused'}),patch.object(public.xbox,'authenticated_client',service):
            result=public.fetch('xbox','Player1')
        self.assertEqual(len(result['games']),1)
        self.assertEqual(result['achievements'][0]['provider_id'],'0')
        self.assertEqual(result['failed_title_ids'],['2'])
        self.assertEqual(result['warnings'][0]['game'],'Missing ID')

    def test_partial_sync_preserves_old_failed_game_for_same_player(self):
        from copy import deepcopy
        with TemporaryDirectory() as root:
            store=Library(root)
            first=snapshot()
            second=deepcopy(first['games'][0]);second['id']='secondgame';second['title_id']='title2'
            item=deepcopy(first['achievements'][0]);item['id']='xbox:title2:0';item['game_id']='secondgame';item['unlocked']=True
            first['games'].append(second);first['achievements'].append(item)
            store.apply_public_profile(first)
            partial=snapshot();partial['failed_title_ids']=['title2'];partial['warnings']=[{'title_id':'title2','game':'Second','reason':'missing ID'}]
            store.apply_public_profile(partial)
            self.assertEqual(len(store.library['games']),2)
            self.assertTrue(next(a for a in store.library['achievements'] if a['id']=='xbox:title2:0')['unlocked'])
            self.assertEqual(len(store.state['sync_warnings']),1)
            partial['id']='another-player';partial['username']='AnotherPlayer';store.apply_public_profile(partial)
            self.assertEqual(len(store.library['games']),1)
