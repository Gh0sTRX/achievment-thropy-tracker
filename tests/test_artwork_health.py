import io
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from atlas.core import Library
from atlas import artwork,media_sync

class ArtworkHealthTests(unittest.TestCase):
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
