import io
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch
from PIL import Image
from atlas import artwork, media_sync
from atlas.server import Controller


class XboxArtworkMappingTests(unittest.TestCase):
    def test_reported_categories_are_safe_distinct_and_not_invented(self):
        images=[{'imageType':kind,'uri':'https://xboxlive.com/'+kind} for kind in ('BoxArt','Logo','Background','Banner','Screenshot')]
        images += [images[0],None,{'imageType':'Logo','uri':'https://untrusted.example/logo'}, {'imageType':'Unknown','uri':'https://xboxlive.com/unknown'}]
        found=artwork.xbox_title_candidates({'images':images})
        self.assertEqual([x['kind'] for x in found],['cover','logo','hero','banner','screenshot'])
        self.assertTrue(all(x['provider']=='Xbox TitleHub' for x in found))
        for value in (None,{},'bad',[]):
            self.assertEqual(artwork.xbox_title_candidates({'images':value}),[])

    def test_confirmed_csv_mapping_caches_reported_assets_and_preserves_user_data(self):
        with tempfile.TemporaryDirectory() as root:
            c=Controller(root)
            g={'id':'csv','name':'Minecraft','platform':'xbox','notes':'keep'}
            a={'id':'ta:1','game_id':'csv','platform':'xbox','unlocked':True,'unlock_time':'2020-01-01'}
            c.store.library['games']=[g];c.store.library['achievements']=[a];c.store.state['pins']=['ta:1']
            candidate={'titleId':'12','name':'Minecraft','platform':'360','devices':['Xbox360'],'images':[
                {'imagePurpose':'BoxArt','url':'https://xboxlive.com/cover'},
                {'type':'Logo','uri':'https://xboxlive.com/logo'},
                {'imageType':'Background','uri':'https://xboxlive.com/hero'}]}
            c.active_matches=[candidate]
            before=deepcopy(g)
            with self.assertRaises(ValueError):c.xbox_map({'game_id':'csv','title_id':'12','edition':'360'})
            self.assertEqual(g,before)
            c.xbox_map({'game_id':'csv','title_id':'12','edition':'360','confirmed':True})
            self.assertEqual({x['kind'] for x in g['art_candidates']},{'cover','logo','hero'})
            self.assertTrue(all(x['confirmed_game_id']=='csv' and x['provider_id']=='12' for x in g['art_candidates']))
            png=io.BytesIO();Image.new('RGB',(12,12)).save(png,format='PNG')
            # A user-provided logo must take precedence over a remote candidate.
            artwork.store_bytes(c.store.root,'logo','csv',png.getvalue())
            g['logo_url']='local';g['artwork_meta']={'logo':{'provider':'user_file'}}
            with patch.object(artwork,'fetch',return_value=(png.getvalue(),'image/png')) as fetch:
                result=media_sync.download(c.store,game_id='csv')
            self.assertEqual(result['downloaded'],2);self.assertEqual(result['cached'],1)
            self.assertEqual(fetch.call_count,2)
            self.assertEqual(g['artwork_meta']['logo']['provider'],'user_file')
            self.assertEqual(g['notes'],'keep');self.assertEqual(a['unlock_time'],'2020-01-01');self.assertEqual(c.store.state['pins'],['ta:1'])
            self.assertFalse(g.get('banner_url'));self.assertFalse(g.get('screenshot_url'))

