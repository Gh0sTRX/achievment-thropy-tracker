import asyncio
import io
from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from PIL import Image
from atlas import editions, public_profiles as public, media_sync, artwork, guides
from atlas.core import Library


class EditionTests(unittest.TestCase):
    def test_minecraft_device_editions_keep_distinct_identity(self):
        results=[]
        for tid,device in [('1','Xbox360'),('2','Windows10'),('3','iOS'),('4','Android')]:
            devices=editions.xbox_devices({'name':'Minecraft'},{'devices':[device]},'2')
            g=editions.apply(public.game('xbox',tid,'Minecraft','unknown'),devices)
            results.append(g)
            a=public.achievement(g,{'id':'0','name':'Actual','unlocked':False})
            self.assertEqual(a['devices'],devices)
        self.assertEqual(len({g['id'] for g in results}),4)
        self.assertEqual([g['devices'][0] for g in results],['xbox360','windows','ios','android'])

    def test_psn_devices_and_shared_sets_are_not_duplicated(self):
        for device in ['ps3','ps4','ps5','psvita']:
            g=editions.apply(public.game('psn','NPWR_'+device,'Same game',device),[device])
            self.assertEqual(g['device_label'],editions.LABELS[device])
            self.assertFalse(g['shared_achievement_list'])
        shared=editions.apply(public.game('psn','NPWR_SHARED','Shared game','PS3,PS4'),['ps3','ps4'])
        self.assertTrue(shared['shared_achievement_list'])
        self.assertEqual(shared['devices'],['ps3','ps4'])

    def test_bare_name_does_not_invent_mobile_or_pc_edition(self):
        self.assertEqual(editions.xbox_devices({'name':'Minecraft'},{},'2'),[])
        self.assertEqual(editions.xbox_devices({'name':'Minecraft for Android'},{},'2'),['android'])

    def test_guide_cache_and_query_distinguish_device(self):
        a={'id':'1','name':'Actual','game_name':'Minecraft','description':'Condition','device_label':'iOS','platform_edition':'ios'}
        b={**a,'device_label':'Android','platform_edition':'android'}
        self.assertNotEqual(guides.fingerprint(a),guides.fingerprint(b))


class LegacyProgressTests(unittest.TestCase):
    def test_legacy_catalog_and_earned_list_are_joined(self):
        async def profile(name):return {'profileUsers':[{'id':'222','settings':[{'id':'Gamertag','value':'Player1'}]}]}
        calls=[]
        async def get(url,**kw):
            calls.append(url)
            if '/history/titles' in url:
                raw={'titles':[{'titleId':1297290392,'name':'Legacy','platforms':[1]}] if kw['headers']['x-xbl-contract-version']=='1' else []}
            elif '/titleachievements' in url:
                raw={'achievements':[{'id':1,'name':'First','unlocked':False,'imageId':3},{'id':2,'name':'Second','unlocked':False,'imageId':4}]}
            else:raw={'achievements':[{'id':2,'unlocked':True,'timeUnlocked':'2026-01-01'}]}
            return SimpleNamespace(raise_for_status=lambda:None,json=lambda:raw)
        client=SimpleNamespace(profile=SimpleNamespace(get_profile_by_gamertag=profile),session=SimpleNamespace(get=get))
        @asynccontextmanager
        async def auth(path):yield client,'111'
        with patch.dict('os.environ',{'ATLAS_XBOX_TOKEN_FILE':'unused'}),patch.object(public.xbox,'authenticated_client',auth):
            result=public.fetch('xbox','Player1')
        self.assertEqual([a['unlocked'] for a in result['achievements']],[False,True])
        self.assertEqual(result['games'][0]['devices'],['xbox360'])
        self.assertTrue(result['achievements'][0]['icon_candidate'].startswith('https://image-ssl.xboxlive.com/'))
        self.assertEqual(result['achievements'][0]['icon_url'],'')
        self.assertTrue(any('/titleachievements' in u for u in calls))
        self.assertTrue(any(u.endswith('/achievements') for u in calls))

    def test_auto_media_only_exposes_decoded_legacy_icon(self):
        data=io.BytesIO();Image.new('RGB',(16,16),(10,20,30)).save(data,format='PNG')
        with TemporaryDirectory() as root:
            store=Library(root)
            store.library['games']=[{'id':'game1','title_id':'1','name':'Legacy','platform':'xbox','cover_url':'https://xboxlive.com/cover.png','art_candidates':[{'kind':'logo','url':'https://xboxlive.com/logo.png','provider':'Xbox'}]}]
            store.library['achievements']=[{'id':'xbox:1:1','game_id':'game1','name':'First','icon_url':'','icon_candidate':artwork.legacy_icon_url(1,3)}]
            with patch.object(artwork,'fetch',return_value=(data.getvalue(),'image/png')):
                report=media_sync.download(store)
            self.assertEqual(report['downloaded'],3)
            self.assertTrue(store.library['achievements'][0]['icon_url'])
            self.assertEqual(store.library['games'][0]['logo_url'],'local')
            self.assertIsNotNone(artwork.cached(store.root,'icon','xbox:1:1'))
