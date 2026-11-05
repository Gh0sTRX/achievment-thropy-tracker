import io,tempfile,unittest
from unittest.mock import patch
from urllib.error import HTTPError
from PIL import Image
from atlas.core import Library
from atlas import artwork,media_sync,enrichment

class MediaTruthTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=Library(self.tmp.name)
  self.g={'id':'xbox:1','name':'CSV Game','platform':'xbox','title_id':'12','platform_edition':'360','devices':['xbox360'],'notes':'keep'}
  self.a={'id':'ta:1','game_id':'xbox:1','platform':'xbox','name':'One','points':20,'unlocked':True,'unlock_time':'2026-01-01','description':'old','icon_url':''}
  self.s.library['games']=[self.g];self.s.library['achievements']=[self.a];self.s.state['pins']=['ta:1'];self.s.save()
  f=io.BytesIO();Image.new('RGB',(12,12)).save(f,format='PNG');self.png=f.getvalue()
 def totals(self,r):self.assertEqual(r['planned'],sum(r[k] for k in ('downloaded','cached','missing_source','failed','blocked','skipped','cancelled')))
 def test_csv_zero_images_and_cached_without_url(self):
  r=media_sync.download(self.s);self.totals(r);self.assertEqual(r['downloaded'],0);self.assertEqual(r['missing_source'],6);self.assertEqual(r['attempted'],0)
  artwork.store_bytes(self.s.root,'icon','ta:1',self.png)
  r=media_sync.download(self.s);self.totals(r);self.assertEqual(r['cached'],1);self.assertEqual(media_sync.health(self.s)['cached_icons'],1)
 def test_decoded_not_fake_cache(self):
  p=self.s.root/'artwork';p.mkdir();(p/'icon_ta_1.png').write_bytes(b'not an image')
  self.assertIsNone(artwork.cached(self.s.root,'icon','ta:1'));self.assertEqual(media_sync.health(self.s)['cached_icons'],0)
 def test_failures_are_not_missing_sources_and_secrets_redacted(self):
  self.g['cover_url']='https://xboxlive.com/image'
  for code in (401,403,429,404):
   with patch.object(artwork,'fetch',side_effect=HTTPError('https://xboxlive.com/?token=SECRET',code,'SECRET',{},None)):
    r=media_sync.download(self.s)
   self.totals(r);self.assertEqual(r['attempted'],1);self.assertEqual(r['blocked' if code!=404 else 'failed'],1);self.assertNotIn('SECRET',str(r))
 def test_download_provenance_skip_cache_and_cancel(self):
  self.a['icon_url']='https://xboxlive.com/icon'
  with patch.object(artwork,'fetch',return_value=(self.png,'image/png')):r=media_sync.download(self.s)
  self.totals(r);self.assertEqual(r['downloaded'],1);self.assertEqual(self.a['icon_meta']['provider'],'xbox')
  with patch.object(artwork,'fetch') as fetch:r=media_sync.download(self.s);fetch.assert_not_called()
  self.totals(r);self.assertEqual(r['cached'],1)
  r=media_sync.download(self.s,stop=lambda:True);self.totals(r);self.assertEqual(r['cancelled'],6)
 def test_explicit_enrichment_preserves_identity_date_pin_notes(self):
  remote={'id':'99','name':'One','gamerscore':20,'description':'official','icon':'https://xboxlive.com/icon','unlocked':False}
  pairs=enrichment.proposals(self.g,[self.a],[remote]);batch={'game':dict(self.g),'pairs':pairs}
  enrichment.apply(self.s,batch,['ta:1']);self.assertEqual(self.a['description'],'official');self.assertTrue(self.a['unlocked']);self.assertEqual(self.a['unlock_time'],'2026-01-01');self.assertEqual(self.s.state['pins'],['ta:1']);self.assertEqual(self.g['notes'],'keep')
  self.g['platform_edition']='windows'
  with self.assertRaises(ValueError):enrichment.apply(self.s,batch,['ta:1'])
 def test_ambiguous_enrichment_not_proposed(self):
  remote={'id':'99','name':'One','gamerscore':20}
  self.assertEqual(enrichment.proposals(self.g,[self.a],[remote,{**remote,'id':'100'}]),[])
