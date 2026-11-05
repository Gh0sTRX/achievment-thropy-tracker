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
