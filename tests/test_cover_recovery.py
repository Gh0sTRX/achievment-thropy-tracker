"""Synthetic provider metadata only: not live-account acceptance."""
import asyncio
from contextlib import asynccontextmanager, AsyncExitStack
from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import tracemalloc
from types import SimpleNamespace
import unittest
from unittest.mock import patch, AsyncMock
from urllib.error import HTTPError
from PIL import Image
from atlas import artwork, cover_recovery as recovery, media_sync
from atlas.core import Library


def image():
    out=io.BytesIO();Image.new('RGB',(16,24),(40,80,130)).save(out,format='PNG');return out.getvalue()


def game(n=1,platform='pc',devices=None,edition=None):
    devices=devices or ['pc'];edition=edition or ('steam' if platform=='pc' else '-'.join(devices))
    return dict(id=f'{platform}:{n}:{edition}',title_id=str(n),name='SYNTHETIC FIXTURE',platform=platform,
                provider='steam' if platform=='pc' else platform,devices=devices,platform_edition=edition,notes='KEEP')


class CoverRecoveryTests(unittest.TestCase):
    def test_steam_identity_download_restart_and_idempotence(self):
        with TemporaryDirectory() as root, patch.object(artwork,'fetch',return_value=(image(),'image/png')) as request:
            store=Library(root);g=game();store.library['games']=[g]
            store.library['achievements']=[dict(id='a',game_id=g['id'],platform='pc',unlocked=True,unlock_time='2026-10-01T00:00:00Z')]
            store.state['pins']=['a'];before=deepcopy(store.library['achievements'])
            report=recovery.discover(store)
            self.assertEqual(report['discovered'],1)
            self.assertEqual(media_sync.download(store,covers_only=True)['downloaded'],1)
            after=Library(root)
            self.assertIsNotNone(artwork.game_cached(after.root,after.library['games'][0],'cover'))
            self.assertEqual(media_sync.download(after,covers_only=True)['cached'],1)
            self.assertEqual(recovery.discover(after)['skipped'],1)
            request.assert_called_once()
            self.assertEqual(after.library['achievements'],before);self.assertEqual(after.state['pins'],['a'])
            self.assertEqual(after.library['games'][0]['notes'],'KEEP')

    def test_xbox_session_title_id_and_device_mismatch(self):
        client=SimpleNamespace(titlehub=SimpleNamespace(get_title_info=AsyncMock(return_value={'titles':[{
            'titleId':'12','devices':['Xbox360'],'displayImage':'https://xboxlive.com/cover.png'}]})))
        sessions=[]
        @asynccontextmanager
        async def auth(*args):
            sessions.append(args);yield client,'123'
        with TemporaryDirectory() as root, patch.object(recovery.xbox,'authenticated_client',auth), patch.object(recovery.settings,'get',return_value='token'),patch.object(recovery.xbox,'has_tokens',return_value=True):
            store=Library(root);store.library['games']=[game(12,'xbox',['xbox360'],'360'),game(12,'xbox',['xboxone'])]
            r=recovery.discover(store)
            self.assertEqual(r['discovered'],1);self.assertEqual(r['no_source'],1);self.assertEqual(len(sessions),1)
            self.assertEqual(len(media_sync.game_sources(store.library['games'][0],'cover')),1)
            self.assertEqual(media_sync.game_sources(store.library['games'][1],'cover'),[])
            # Changing edition makes a discovered candidate ineligible, including after reload.
            store.library['games'][0]['devices']=['windows']
            self.assertEqual(media_sync.game_sources(store.library['games'][0],'cover'),[])

    def test_psn_catalogue_matches_np_and_exact_platform(self):
        from types import ModuleType
        sdk=ModuleType('psnawp_api');calls=[]
        title=lambda tid,ds:SimpleNamespace(np_communication_id=tid,title_platform=[SimpleNamespace(value=d) for d in ds],title_icon_url='https://image.api.playstation.com/cover.png')
        class User:
            account_id='42'
            def trophy_titles(self,limit=None):
                calls.append(1);return iter([title('NP1',['PS3']),title('NP2',['PSVITA']),title('NP3',['PS4']),title('NP4',['PS5'])])
        sdk.PSNAWP=lambda secret:SimpleNamespace(user=lambda **k:User())
        with TemporaryDirectory() as root,patch.dict('sys.modules',{'psnawp_api':sdk}),patch.object(recovery.settings,'get',return_value='SESSION'):
            store=Library(root);store.state['public_profiles']={'psn':{'id':'42','username':'SYNTHETIC'}}
            store.library['games']=[]
            for i,ds in enumerate(('ps3','psvita','ps4','ps5')):
                g=game(i,'psn',[ds],ds.upper());g['title_id']='NP'+str(i+1);store.library['games'].append(g)
            wrong=game(90,'psn',['ps5']);wrong['title_id']='NP1';store.library['games'].append(wrong)
            report=recovery.discover(store)
            self.assertEqual(report['discovered'],4);self.assertEqual(report['no_source'],1);self.assertEqual(calls,[1])

    def test_name_only_csv_candidates_require_confirmation_and_persist(self):
        with TemporaryDirectory() as root,patch.object(artwork,'search_game',return_value=[{'id':22,'name':'SYNTHETIC candidate'}]) as search,patch.object(artwork,'candidates') as choices:
            store=Library(root);g=game(4,'xbox',['xbox360'],'360');g.pop('title_id');store.library['games']=[g];store.steamgriddb_key='memory-only'
            self.assertEqual(recovery.discover(store)['pending'],1)
            self.assertEqual(recovery.discover(store)['pending'],1);search.assert_called_once();choices.assert_not_called()
            self.assertEqual(media_sync.game_sources(g,'cover'),[])
            self.assertNotIn('title_id',g)
            disk=Library(root);self.assertIsNone(disk.steamgriddb_key)
            self.assertEqual(disk.library['games'][0]['cover_discovery']['candidates'][0]['id'],22)
            self.assertEqual(media_sync.cover_inventory(store)['pending_approval'],1)
            self.assertEqual(media_sync.cover_inventory(store,state='pending')['queue_total'],1)
            self.assertEqual(media_sync.cover_inventory(store,state='available')['queue_total'],0)
            with self.assertRaises(ValueError):media_sync.cover_inventory(store,state='bogus')

    def test_confirmed_supplementary_mapping_is_bound_to_edition(self):
        with TemporaryDirectory() as root,patch.object(artwork,'candidates',return_value=[{'kind':'cover','url':'https://cdn2.steamgriddb.com/grid.png'}]) as choices,patch.object(recovery.settings,'get',return_value=''),patch.object(recovery.xbox,'has_tokens',return_value=False):
            store=Library(root);g=game(5,'xbox',['xbox360'],'360');store.library['games']=[g];store.steamgriddb_key='memory-only'
            g['artwork_match']=dict(provider='SteamGridDB',provider_id='55',confirmed=True,game_id=g['id'],platform='xbox',title_id='5',platform_edition='360',devices=['xbox360'])
            self.assertEqual(recovery.discover(store)['discovered'],1);choices.assert_called_once_with('55','memory-only')
            g['platform_edition']='xboxone';self.assertFalse(recovery.bound_match(g))
            self.assertEqual(media_sync.game_sources(g,'cover'),[])

    def test_user_override_and_profile_switch_during_request_are_preserved(self):
        for mode in ('override','profile','replace'):
            with self.subTest(mode=mode),TemporaryDirectory() as root:
                store=Library(root);g=game();store.library['games']=[g]
                async def official(_self,_game):
                    if mode=='override':g['artwork_meta']={'cover':{'provider':'user_file'}}
                    elif mode=='profile':store.state['public_profiles']={'xbox':{'id':'changed'}}
                    else:store.library['games']=[deepcopy(g)]
                    return [{'kind':'cover','url':'https://xboxlive.com/cover.png'}],''
                with patch.object(recovery.Sources,'official',official):r=recovery.discover(store)
                self.assertEqual(r['skipped'],1);self.assertNotIn('cover_discovery',store.library['games'][0])

    def test_cancel_preserves_completed_and_rate_limit_stops_provider_calls(self):
        with TemporaryDirectory() as root:
            store=Library(root);store.library['games']=[game(i+1) for i in range(5)]
            done=[]
            def progress(n,total,msg):done.append(n)
            r=recovery.discover(store,progress,lambda:len(done)>1)
            self.assertTrue(r['cancelled']);self.assertEqual(r['discovered'],1)
            self.assertEqual(Library(root).library['games'][0]['cover_discovery']['state'],'discovered')
        with TemporaryDirectory() as root,patch.object(artwork,'search_game',side_effect=HTTPError('https://example.com/SECRET',429,'SECRET',{},None)) as search:
            store=Library(root);store.steamgriddb_key='SECRET';store.library['games']=[dict(game(i),platform='unknown') for i in range(3)]
            r=recovery.discover(store);search.assert_called_once();self.assertEqual(r['failed'],1)
            self.assertNotIn('SECRET',json.dumps(store.library));self.assertEqual(media_sync.cover_inventory(store)['failed'],1)

    def test_mixed_library_sizes_and_negative_cache_bound_queries(self):
        metrics={}
        variants=[('xbox',['xbox360'],'360'),('xbox',['xboxone'],'xboxone'),('xbox',['xboxseries'],'xboxseries'),('psn',['ps3'],'PS3'),('psn',['psvita'],'PSVITA'),('psn',['ps4'],'PS4'),('psn',['ps5'],'PS5'),('pc',['pc'],'steam'),('xbox',[],'csv')]
        with patch.object(recovery.settings,'get',return_value=''),patch.object(recovery.xbox,'has_tokens',return_value=False):
            for count in (20,100,500,1000):
                with self.subTest(count=count),TemporaryDirectory() as root:
                    store=Library(root);store.library['games']=[]
                    for i in range(count):
                        p,ds,ed=variants[i%len(variants)];g=game(i+1,p,ds,ed)
                        if ed=='csv':g.pop('title_id');g['devices']=[]
                        store.library['games'].append(g)
                    before=deepcopy(store.library['games']);tracemalloc.start();start=time.perf_counter()
                    report=recovery.discover(store)
                    with patch.object(artwork,'fetch',return_value=(image(),'image/png')) as fetch:
                        downloaded=media_sync.download(store,covers_only=True)
                        self.assertEqual(downloaded['downloaded'],count//9)
                        self.assertEqual(fetch.call_count,count//9)
                        repeat=recovery.discover(store)
                        self.assertEqual(repeat['discovered'],0)
                    inventory=media_sync.cover_inventory(store)
                    self.assertEqual(inventory['total_games'],count);self.assertEqual(inventory['covered'],count//9)
                    self.assertLessEqual(len(inventory['items']),20)
                    self.assertEqual([g['notes'] for g in store.library['games']],[g['notes'] for g in before])
                    peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
                    metrics[count]=dict(peak_traced_bytes=peak,seconds=round(time.perf_counter()-start,4),discovered=report['discovered'],covered=inventory['covered'],no_source=report['no_source'])
        Path('work/audit').mkdir(parents=True,exist_ok=True)
        Path('work/audit/cover-recovery-synthetic.json').write_text(json.dumps({'synthetic_only':True,'scenarios':metrics},indent=2))

    def test_discovery_and_confirmed_art_survive_same_profile_sync(self):
        with TemporaryDirectory() as root:
            store=Library(root);g=game();snapshot=dict(platform='pc',provider='steam',id='76561198000000000',username='Synthetic',synced_at='2026-11-06',games=[g],achievements=[])
            store.apply_public_profile(deepcopy(snapshot))
            self.assertEqual(recovery.discover(store)['discovered'],1)
            original=deepcopy(store.library['games'][0]['cover_discovery'])
            store.apply_public_profile(deepcopy(snapshot))
            current=store.library['games'][0]
            self.assertEqual(current['cover_discovery'],original)
            self.assertEqual(len(media_sync.game_sources(current,'cover')),1)
            current['platform_edition']='other-edition'
            self.assertEqual(media_sync.game_sources(current,'cover'),[])

    def test_failed_official_url_offers_unconfirmed_supplementary_candidate(self):
        with TemporaryDirectory() as root,patch.object(artwork,'search_game',return_value=[{'id':9,'name':'Synthetic candidate'}]):
            store=Library(root);g=game();store.library['games']=[g];store.steamgriddb_key='memory-only'
            self.assertEqual(recovery.discover(store)['discovered'],1)
            g['artwork_download']={'cover':{'state':'failed','code':404}}
            self.assertEqual(recovery.discover(store)['pending'],1)
            self.assertEqual(g['cover_discovery']['candidates'][0]['id'],9)
            self.assertNotIn('artwork_match',g)

    def test_wrong_provider_and_ambiguous_editions_do_not_get_steam_art(self):
        with TemporaryDirectory() as root,patch.object(recovery.settings,'get',return_value=''),patch.object(recovery.xbox,'has_tokens',return_value=False):
            store=Library(root)
            store.library['games']=[dict(game(),provider='unknown'),dict(game(2),platform_edition='windows'),dict(game(3),steam_appid='999'),dict(game(4),title_id='١٢')]
            self.assertEqual(recovery.discover(store)['no_source'],4)
            self.assertTrue(all(not media_sync.game_sources(g,'cover') for g in store.library['games']))

    def test_download_rejects_device_change_or_replaced_profile_during_fetch(self):
        for change in ('devices','profile','replace'):
            with self.subTest(change=change),TemporaryDirectory() as root:
                store=Library(root);g=game();store.library['games']=[g];recovery.discover(store)
                def fetch(*args):
                    if change=='devices':g['devices'].append('other-device')
                    elif change=='profile':store.state['public_profiles']={'pc':{'id':'other'}}
                    else:store.library['games']=[deepcopy(g)]
                    return image(),'image/png'
                with patch.object(artwork,'fetch',side_effect=fetch):result=media_sync.download(store,covers_only=True)
                self.assertEqual(result['downloaded'],0);self.assertEqual(result['skipped'],1)
                self.assertIsNone(artwork.cached(store.root,'cover',g['id']))


    def test_metadata_cache_cannot_transfer_steam_cover_to_another_pc_provider(self):
        for order in (False,True):
            with self.subTest(order=order),TemporaryDirectory() as root:
                store=Library(root)
                valid=game(12)
                other=dict(game(12),id='other:12',provider='unknown')
                conflict=dict(game(12),id='conflicting:12',steam_appid='999')
                store.library['games']=[valid,other,conflict] if order else [other,conflict,valid]
                result=recovery.discover(store)
                self.assertEqual(result['discovered'],1);self.assertEqual(result['no_source'],2)
                self.assertTrue(media_sync.game_sources(valid,'cover'))
                self.assertEqual(media_sync.game_sources(other,'cover'),[])
                self.assertEqual(media_sync.game_sources(conflict,'cover'),[])
