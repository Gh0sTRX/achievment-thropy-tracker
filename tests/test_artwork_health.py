import io
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from atlas.core import Library
from atlas import artwork,media_sync

class ArtworkHealthTests(unittest.TestCase):
    def test_valid_bytes_bound_to_other_title_are_not_applied_or_deleted(self):
        with TemporaryDirectory() as root:
            store=Library(root);g={'id':'csv:1','platform':'xbox','title_id':'new','platform_edition':'360','cover_url':'local','artwork_meta':{'cover':{'game_id':'csv:1','platform':'xbox','title_id':'old','platform_edition':'360','provider':'Xbox TitleHub','source_url':'https://xboxlive.com/old'}}};store.library['games']=[g]
            data=io.BytesIO();Image.new('RGB',(12,12)).save(data,format='PNG');artwork.store_bytes(store.root,'cover',g['id'],data.getvalue());path=artwork.cached(store.root,'cover',g['id']);before=path.read_bytes()
            self.assertEqual(media_sync.health(store)['cached']['cover'],0)
            self.assertEqual(media_sync.health(store)['issues'][0]['assets']['cover']['state'],'identity_mismatch')
            with patch.object(artwork,'fetch') as fetch:media_sync.download(store);fetch.assert_not_called()
            self.assertEqual(path.read_bytes(),before)
            g['artwork_meta']['cover']['provider']='user_file'
            self.assertEqual(media_sync.health(store)['cached']['cover'],1)
    def test_decoded_cache_wins_over_old_error_and_corruption_is_distinct(self):
        with TemporaryDirectory() as root:
            store=Library(root);g={'id':'xbox:1','platform':'xbox','cover_url':'local','artwork_download':{'cover':{'state':'blocked','code':403}}};store.library['games']=[g]
            data=io.BytesIO();Image.new('RGB',(12,12)).save(data,format='PNG');artwork.store_bytes(store.root,'cover',g['id'],data.getvalue())
            a=media_sync.health(store)['issues'][0]['assets']['cover'];self.assertEqual(a['state'],'cached');self.assertIsNone(a['code'])
            artwork.cached(store.root,'cover',g['id']).write_bytes(b'corrupt')
            self.assertEqual(media_sync.health(store)['issues'][0]['assets']['cover']['state'],'invalid_cache')
    def test_icon_only_gaps_and_single_game_scope_are_visible(self):
        with TemporaryDirectory() as root:
            store=Library(root);store.library['games']=[{'id':'g1','platform':'xbox'},{'id':'g2','platform':'psn'}]
            store.library['achievements']=[{'id':'a1','game_id':'g1','icon_url':'https://xboxlive.com/icon','icon_download':{'state':'blocked','code':429}}]
            data=io.BytesIO();Image.new('RGB',(12,12)).save(data,format='PNG')
            for kind in ('cover','hero','banner','logo','screenshot'):artwork.store_bytes(store.root,kind,'g1',data.getvalue())
            h=media_sync.health(store,game_id='g1');self.assertEqual(h['games'],1);self.assertEqual(h['issues'][0]['missing'],['icon'])
            self.assertEqual(h['issues'][0]['assets']['icon']['http_codes'],[429]);self.assertEqual(h['issues'][0]['assets']['icon']['blocked'],1)
    def test_same_local_id_with_changed_title_cannot_recover_old_image(self):
        with TemporaryDirectory() as root:
            store=Library(root)
            store.library['games']=[{'id':'csv:1','platform':'xbox','title_id':'new','platform_edition':'360','cover_url':'local','artwork_meta':{'cover':{'game_id':'csv:1','platform':'xbox','title_id':'old','platform_edition':'360','provider':'Xbox TitleHub','source_url':'https://xboxlive.com/old'}}}]
            with patch.object(artwork,'fetch') as fetch:media_sync.download(store);fetch.assert_not_called()
            issue=media_sync.health(store)['issues'][0]
            self.assertEqual(issue['assets']['cover']['state'],'identity_mismatch')
            self.assertTrue(issue['assets']['cover']['action'])

    def test_health_explains_missing_cache_source_and_blocked_assets(self):
        with TemporaryDirectory() as root:
            store=Library(root)
            g={'id':'csv:1','name':'Minecraft: Xbox 360 Edition','platform':'xbox','title_id':'12','platform_edition':'360','cover_url':'local','hero_url':'https://xboxlive.com/hero','artwork_meta':{'cover':{'game_id':'csv:1','platform':'xbox','title_id':'12','platform_edition':'360','provider':'Xbox TitleHub','source_url':'https://xboxlive.com/cover'}},'artwork_download':{'hero':{'state':'blocked','code':403}}}
            store.library['games']=[g];store.library['achievements']=[{'id':'a1','game_id':'csv:1','platform':'xbox'}]
            assets=media_sync.health(store)['issues'][0]['assets']
            self.assertEqual(assets['cover']['state'],'missing_cache');self.assertTrue(assets['cover']['source_available'])
            self.assertEqual(assets['hero']['code'],403);self.assertEqual(assets['logo']['state'],'missing_source')
            self.assertEqual(assets['icon']['missing'],1)
            self.assertTrue(all(x['reason'] and x['action'] for x in assets.values()))
    def test_health_sources_obey_download_edition_and_user_file_rules(self):
        with TemporaryDirectory() as root:
            store=Library(root)
            game={'id':'xbox:1','platform':'xbox','platform_edition':'360','cover_url':'local'}
            store.library['games']=[game]
            metadata={'game_id':'xbox:1','platform':'xbox','platform_edition':'windows','provider':'xbox','source_url':'https://xboxlive.com/cover'}
            game['artwork_meta']={'cover':metadata}
            self.assertEqual(media_sync.health(store)['valid_source_urls']['cover'],0)
            with patch.object(artwork,'fetch') as fetch:media_sync.download(store);fetch.assert_not_called()
            metadata['platform_edition']='360'
            self.assertEqual(media_sync.health(store)['valid_source_urls']['cover'],1)
            metadata['provider']='user_file'
            game['art_candidates']=[{'kind':'cover','url':'https://xboxlive.com/cover'}]
            self.assertEqual(media_sync.health(store)['valid_source_urls']['cover'],0)
    def test_health_and_download_both_exclude_retained_apps(self):
        with TemporaryDirectory() as root:
            store=Library(root)
            store.library['games']=[{'id':'app','name':'Netflix','platform':'xbox','cover_url':'https://xboxlive.com/cover'}]
            store.library['achievements']=[{'id':'app:1','game_id':'app','icon_url':'https://xboxlive.com/icon'}]
            self.assertEqual(media_sync.health(store)['games'],0)
            self.assertEqual(media_sync.health(store)['achievements'],0)
            self.assertEqual(media_sync.download(store)['planned'],0)
            self.assertEqual(len(store.library['games']),1)
    def test_candidates_are_not_downloaded_coverage_and_all_kinds_cache(self):
        image=io.BytesIO();Image.new('RGB',(20,20)).save(image,format='PNG')
        with TemporaryDirectory() as root:
            store=Library(root)
            store.library['games']=[{'id':'xbox:1','name':'One','title_id':'1','platform':'xbox','art_candidates':[{'kind':kind,'url':'https://xboxlive.com/'+kind+'.png'} for kind in ('cover','hero','banner','logo','screenshot')]}]
            self.assertEqual(sum(media_sync.health(store)['cached'].values()),0)
            with patch.object(artwork,'fetch',return_value=(image.getvalue(),'image/png')):
                result=media_sync.download(store)
            self.assertEqual(result['downloaded'],5)
            self.assertEqual(sum(media_sync.health(store)['cached'].values()),5)
            with patch.object(artwork,'fetch') as fetch:
                media_sync.download(store)
                fetch.assert_not_called()

class ConfirmedArtworkMatchTests(unittest.TestCase):
    def test_confirmed_game_mapping_survives_sync_without_cross_edition_copy(self):
        from atlas.server import Controller
        from atlas import public_profiles as public
        with TemporaryDirectory() as root:
            c=Controller(root)
            def snapshot():
                g=public.game('xbox','123','Edition','360')
                a=public.achievement(g,{'id':'1','name':'One','unlocked':False})
                return {'platform':'xbox','id':'player1','username':'Player1','synced_at':'2026-11-05','games':[g],'achievements':[a]}
            c.store.apply_public_profile(snapshot());gid=c.store.library['games'][0]['id']
            choices=[{'kind':'hero','url':'https://cdn2.steamgriddb.com/hero.png','provider_id':'asset9','rights_note':'Community'}]
            with patch.object(artwork,'candidates',return_value=choices):
                c.get_art_choices({'game_id':gid,'sgdb_id':77,'confirmed':True})
            c.store.apply_public_profile(snapshot())
            game=c.store.library['games'][0]
            self.assertEqual(game['artwork_match']['provider_id'],'77')
            self.assertEqual(game['art_candidates'][0]['confirmed_game_id'],gid)
            other=snapshot();other['games'][0]['platform_edition']='windows'
            c.store.apply_public_profile(other)
            self.assertFalse(c.store.library['games'][0].get('art_candidates'))

class MediaRetryTests(unittest.TestCase):
    def test_transient_retry_but_no_rate_limit_or_invalid_image_retry(self):
        from urllib.error import HTTPError
        with patch('atlas.media_sync.time.sleep'),patch('atlas.media_sync.time.monotonic',side_effect=[0,1]):
            call=unittest.mock.Mock(side_effect=[HTTPError('https://xboxlive.com/image',502,'bad',{},None),'ok'])
            self.assertEqual(media_sync.media_request(call,lambda:False),'ok')
            self.assertEqual(call.call_count,2)
        for failure in [HTTPError('https://xboxlive.com/image',429,'limit',{},None),ValueError('invalid bytes')]:
            call=unittest.mock.Mock(side_effect=failure)
            with self.assertRaises(type(failure)):media_sync.media_request(call,lambda:False)
            self.assertEqual(call.call_count,1)

class SteamArtworkIdentityTests(unittest.TestCase):
    def test_api_names_keep_distinct_safe_cache_paths(self):
        self.assertNotEqual(artwork.cache_token('steam:10:API/a'),artwork.cache_token('steam:10:API_a'))
        self.assertNotEqual(artwork.cache_token('steam:10:API.a'),artwork.cache_token('steam:20:API.a'))
        self.assertNotIn('/',artwork.cache_token('steam:10:../../API'))
        self.assertEqual(artwork.cache_token('xbox:1:1'),'xbox_1_1')
