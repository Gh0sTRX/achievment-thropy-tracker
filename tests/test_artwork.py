import unittest
from atlas.artwork import safe_url,suffix
class ArtTests(unittest.TestCase):
    def test_allowlist(self):
        self.assertTrue(safe_url('https://cdn2.steamgriddb.com/asset.png'))
        self.assertTrue(safe_url('https://store-images.s-microsoft.com/image.jpg'))
        self.assertFalse(safe_url('https://xboxlive.com.evil.example/'))
        self.assertFalse(safe_url('http://localhost/private'))
        self.assertFalse(safe_url('https://127.0.0.1/private'))
        self.assertFalse(safe_url('https://user:pass@xboxlive.com/image.jpg'))
    def test_signature(self):
        self.assertEqual(suffix(b'\x89PNG\r\n\x1a\nabc'),'.png')
        self.assertEqual(suffix(b'NOT IMAGE'),None)
if __name__=='__main__':unittest.main()
class LocalArtTests(unittest.TestCase):
    def test_custom_reset_does_not_restore_another_edition_source(self):
        import base64
        from tempfile import TemporaryDirectory
        from atlas.server import Controller
        with TemporaryDirectory() as root:
            c=Controller(root)
            g={'id':'xbox:12','platform':'xbox','platform_edition':'windows','cover_url':'local','artwork_meta':{'cover':{'game_id':'xbox:12','platform':'xbox','platform_edition':'360','provider':'xbox','source_url':'https://xboxlive.com/old-edition'}}}
            c.store.library['games']=[g]
            c.upload_art({'game_id':g['id'],'kind':'cover','image':base64.b64encode(self.image_bytes()).decode()})
            c.reset_art({'game_id':g['id'],'kind':'cover'})
            self.assertEqual(g['cover_url'],'')

    def test_reset_after_custom_file_restores_cached_provider_source(self):
        import base64
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from atlas.server import Controller
        from atlas import artwork,media_sync
        with TemporaryDirectory() as root:
            c=Controller(root);g={'id':'xbox:12','platform':'xbox','platform_edition':'360','cover_url':'https://xboxlive.com/cover'}
            c.store.library['games']=[g]
            with patch.object(artwork,'fetch',return_value=(self.image_bytes(),'image/png')):media_sync.download(c.store)
            c.upload_art({'game_id':g['id'],'kind':'cover','image':base64.b64encode(self.image_bytes()).decode()})
            c.reset_art({'game_id':g['id'],'kind':'cover'})
            self.assertEqual(g['cover_url'],'https://xboxlive.com/cover')

    def test_manual_provider_selection_recovers_exact_image_after_cache_loss(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from atlas.server import Controller
        from atlas import artwork,media_sync
        with TemporaryDirectory() as root:
            c=Controller(root);g={'id':'xbox:12','platform':'xbox','platform_edition':'360','title_id':'12'}
            c.store.library['games']=[g]
            url='https://cdn2.steamgriddb.com/selected.png'
            c.store.live_artwork[g['id']]=[{'kind':'cover','url':url,'source_url':'https://www.steamgriddb.com/','provider_id':'1'}]
            with patch.object(artwork,'fetch',return_value=(self.image_bytes(),'image/png')):c.select_art({'game_id':g['id'],'kind':'cover','url':url})
            artwork.cached(c.store.root,'cover',g['id']).unlink()
            with patch.object(artwork,'fetch',return_value=(self.image_bytes(),'image/png')) as request:r=media_sync.download(c.store)
            self.assertEqual(r['downloaded'],1);request.assert_called_once_with(url)

    def image_bytes(self):
        import io
        from PIL import Image
        output=io.BytesIO();Image.new('RGB',(320,180),(150,60,40)).save(output,format='PNG')
        return output.getvalue()

    def test_validated_cache_and_corrupt_replacement(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from atlas import artwork
        with TemporaryDirectory() as root:
            meta=artwork.store_bytes(root,'hero','game123',self.image_bytes())
            self.assertEqual((meta['width'],meta['height']),(320,180))
            path=artwork.cached(Path(root),'hero','game123');before=path.read_bytes()
            with self.assertRaises(ValueError):artwork.store_bytes(root,'hero','game123',b'\x89PNG\r\n\x1a\nbroken')
            self.assertEqual(path.read_bytes(),before)
            artwork.remove_cached(root,'hero','game123')
            self.assertIsNone(artwork.cached(Path(root),'hero','game123'))

    def test_oversized_and_unknown_type_rejected(self):
        import io
        from PIL import Image
        from tempfile import TemporaryDirectory
        from atlas import artwork
        out=io.BytesIO();Image.new('RGB',(8193,1)).save(out,format='PNG')
        with TemporaryDirectory() as root:
            for kind,data in [('hero',out.getvalue()),('hero',b'<svg></svg>'),('../escape',self.image_bytes())]:
                with self.assertRaises(ValueError):artwork.store_bytes(root,kind,'game123',data)

    def test_local_art_survives_sync_and_reset_restores_provider(self):
        import base64
        from tempfile import TemporaryDirectory
        from atlas.server import Controller
        from atlas.core import game_id
        with TemporaryDirectory() as root:
            c=Controller(root);gid=game_id('xbox','123')
            g={'id':gid,'title_id':'123','name':'Fixture game','platform':'xbox','platform_edition':'one','cover_url':'https://xboxlive.com/cover.png','hero_url':''}
            snap={'id':'1','username':'FixturePlayer','platform':'xbox','games':[g], 'achievements':[], 'synced_at':'2026-11-03'}
            c.store.apply_public_profile(snap)
            c.upload_art({'game_id':gid,'kind':'cover','image':base64.b64encode(self.image_bytes()).decode()})
            c.theme_art({'game_id':gid,'theme':'ember','x':75,'y':32})
            c.store.apply_public_profile(snap)
            game=c.store.library['games'][0]
            self.assertEqual(game['cover_url'],'local')
            self.assertEqual(game['artwork_meta']['cover']['provider'],'user_file')
            self.assertEqual(game['art_theme']['x'],75)
            c.reset_art({'game_id':gid,'kind':'cover'})
            self.assertEqual(game['cover_url'],'https://xboxlive.com/cover.png')

    def test_source_index_has_11_distinct_providers(self):
        from atlas.artwork import sources
        index=sources()['providers']
        self.assertEqual(len(index),11)
        self.assertEqual(len({x['id'] for x in index}),11)
        self.assertTrue(all(x['url'].startswith('https://') for x in index))

    def test_no_guessing_game_match(self):
        from tempfile import TemporaryDirectory
        from atlas.server import Controller
        with TemporaryDirectory() as root:
            c=Controller(root)
            c.store.library['games']=[{'id':'game123','name':'Edition','platform':'xbox'}]
            with self.assertRaisesRegex(ValueError,'eşleşmesini onayla'):
                c.get_art_choices({'game_id':'game123','sgdb_id':123})

class ProviderChoicesTests(unittest.TestCase):
    def test_logo_candidates_keep_safe_thumbnails_and_rate_limits(self):
        from unittest.mock import patch
        from urllib.error import HTTPError
        from atlas import artwork
        calls=[]
        def records(path,key):
            calls.append(path)
            return [{'id':1,'url':'https://cdn2.steamgriddb.com/ok.png','thumb':'http://localhost/private'}]
        with patch.object(artwork,'sgdb_json',side_effect=records):
            result=artwork.candidates(42,'not-real')
        self.assertEqual([r['kind'] for r in result],['cover','hero','logo'])
        self.assertIn('logos/game/42',calls);self.assertTrue(all(r['thumb']==r['url'] for r in result))
        for code in (403,429):
            with patch.object(artwork,'sgdb_json',side_effect=HTTPError('https://www.steamgriddb.com',code,'blocked',{},None)):
                with self.assertRaises(HTTPError):artwork.candidates(42,'not-real')
