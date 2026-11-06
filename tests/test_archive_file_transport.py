"""Raw archive transfer retains values that browser JSON parsing can round."""
import json,tempfile,threading,unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from atlas.server import LocalApp
from atlas import archive

class ArchiveFileTransportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.app=LocalApp(self.tmp.name);self.thread=threading.Thread(target=self.app.serve_forever,daemon=True);self.thread.start()
  self.s=self.app.controller.store
  self.s.library['games']=[{'id':'transport-game','platform':'xbox','name':'Synthetic','test_large_integer':9007199254740993}]
  self.s.library['achievements']=[];self.s.state['ui']['font_scale']=1.0;self.s.save()
 def tearDown(self):self.app.shutdown();self.app.server_close();self.thread.join();self.tmp.cleanup()
 def post(self,path,body,confirmed=False,token=True,origin=None):
  headers={'Content-Type':'application/json'}
  if token:headers['X-Atlas-Token']=self.app.token
  if confirmed:headers['X-Atlas-Archive-Confirm']='restore'
  if origin:headers['Origin']=origin
  with urlopen(Request(self.app.url+path,data=body,headers=headers)) as r:return r.read()
 def test_raw_file_roundtrip_preserves_hash_and_large_integer(self):
  raw=self.post('api/archive/export',b'{}');self.assertIn(b'9007199254740993',raw);self.assertRegex(raw,rb'"font_scale"\s*:\s*1\.0')
  self.s.library['games'][0]['name']='changed';self.s.save()
  self.post('api/archive/restore',raw,confirmed=True)
  self.assertEqual(self.s.library['games'][0]['name'],'Synthetic');self.assertEqual(self.s.library['games'][0]['test_large_integer'],9007199254740993)
 def test_raw_restore_still_requires_confirmation_token_and_origin(self):
  raw=self.post('api/archive/export',b'{}');before=self.s.library_path.read_bytes()
  for options,code in [({},400),({'confirmed':True,'token':False},403),({'confirmed':True,'origin':'https://evil.example'},403)]:
   with self.subTest(options=options),self.assertRaises(HTTPError) as error:self.post('api/archive/restore',raw,**options)
   self.assertEqual(error.exception.code,code);self.assertEqual(self.s.library_path.read_bytes(),before)
 def test_corruption_and_browser_numeric_rounding_do_not_bypass_hash(self):
  document=json.loads(self.post('api/archive/export',b'{}'));before=self.s.library_path.read_bytes()
  document['data']['state']['ui']['font_scale']=1
  with self.assertRaises(ValueError):archive.verify_archive(document)
  with self.assertRaises(HTTPError):self.post('api/archive/restore',json.dumps(document).encode(),confirmed=True)
  self.assertEqual(self.s.library_path.read_bytes(),before)
 def test_original_wrapped_api_remains_compatible(self):
  document=json.loads(self.post('api/archive/export',b'{}'))
  self.post('api/archive/restore',json.dumps({'archive':document,'confirm':True}).encode())
  self.assertEqual(self.s.library['games'][0]['test_large_integer'],9007199254740993)
