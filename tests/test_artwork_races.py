import base64
import io
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from atlas import artwork
from atlas.server import Controller


class ArtworkRaceTests(unittest.TestCase):
    def png(self,color):
        out=io.BytesIO();Image.new('RGB',(12,12),color).save(out,format='PNG');return out.getvalue()

    def controller(self,root):
        c=Controller(root);g={'id':'xbox:12','name':'Game','platform':'xbox','title_id':'12','platform_edition':'360','devices':['xbox360']}
        c.store.library['games']=[g]
        c.store.live_artwork[g['id']]=[{'kind':'cover','url':'https://cdn2.steamgriddb.com/cover'}]
        return c,g

    def test_late_remote_response_preserves_new_user_file(self):
        with TemporaryDirectory() as root:
            c,g=self.controller(root);saved=[]
            def fetch(url):
                c.upload_art({'game_id':g['id'],'kind':'cover','image':base64.b64encode(self.png('blue')).decode()})
                saved.append(artwork.cached(c.store.root,'cover',g['id']).read_bytes())
                return self.png('red'),'image/png'
            with patch.object(artwork,'fetch',side_effect=fetch):
                with self.assertRaises(ValueError):c.select_art({'game_id':g['id'],'kind':'cover','url':'https://cdn2.steamgriddb.com/cover'})
            self.assertEqual(g['artwork_meta']['cover']['provider'],'user_file')
            self.assertEqual(artwork.cached(c.store.root,'cover',g['id']).read_bytes(),saved[0])

    def test_late_choices_reject_in_place_edition_change(self):
        with TemporaryDirectory() as root:
            c,g=self.controller(root)
            def choices(*args):g['platform_edition']='windows';return []
            with patch.object(artwork,'candidates',side_effect=choices):
                with self.assertRaises(ValueError):c.get_art_choices({'game_id':g['id'],'confirmed':True,'sgdb_id':1})
            self.assertNotIn('artwork_match',g)

    def test_late_selection_rejects_replaced_profile_record(self):
        with TemporaryDirectory() as root:
            c,g=self.controller(root)
            def fetch(url):c.store.library['games']=[dict(g)];return self.png('red'),'image/png'
            with patch.object(artwork,'fetch',side_effect=fetch):
                with self.assertRaises(ValueError):c.select_art({'game_id':g['id'],'kind':'cover','url':'https://cdn2.steamgriddb.com/cover'})
            self.assertIsNone(artwork.cached(c.store.root,'cover',g['id']))
