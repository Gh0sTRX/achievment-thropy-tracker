import gzip
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from atlas.server import LocalApp,accepts_gzip
from atlas.core import Library

class TransferTests(unittest.TestCase):
    def setUp(self):
        self.root=tempfile.TemporaryDirectory();self.app=LocalApp(self.root.name)
        self.store=self.app.controller.store
        self.store.library['games']=[{'id':'xgame','name':'Example','platform':'xbox','title_id':'1'}]
        self.store.library['achievements']=[{'id':'xa','game_id':'xgame','game_name':'Example','name':'One','platform':'xbox','points':20,'unlocked':False,'description':'Provider metadata '*1000}]
        self.store.save()
        self.thread=threading.Thread(target=self.app.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.app.shutdown();self.app.server_close();self.thread.join();self.root.cleanup()
    def get(self,token=None,encoding=None):
        headers={}
        if token:headers['X-Atlas-Library-Token']=token
        if encoding:headers['Accept-Encoding']=encoding
        with urlopen(Request(self.app.url+'api/data',headers=headers)) as response:
            raw=response.read();heads=dict(response.headers)
            decoded=gzip.decompress(raw) if response.headers.get('Content-Encoding')=='gzip' else raw
        return json.loads(decoded),heads,len(raw)
    def post(self,path,data,token=True):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Atlas-Token']=self.app.token
        with urlopen(Request(self.app.url+path,data=json.dumps(data).encode(),headers=headers)) as response:return json.load(response)
    def test_full_legacy_and_state_only_partial_preserve_reports(self):
        full,_,_=self.get();token=full['library_token']
        self.assertEqual(len(token),64);self.assertFalse(full['library_unchanged'])
        self.post('api/pin',{'id':'xa','pinned':True})
        partial,_,_=self.get(token)
        self.assertIsNone(partial['library']['library']);self.assertTrue(partial['library_unchanged'])
        self.assertEqual(partial['library_token'],token);self.assertEqual(partial['library']['state']['pins'],['xa'])
        self.assertGreater(partial['revision'],full['revision'])
        legacy,_,_=self.get();self.assertIsNotNone(legacy['library']['library'])
        self.assertEqual(partial['platform_reports'],legacy['platform_reports'])
    def test_note_and_achievement_changes_force_full_snapshot(self):
        full,_,_=self.get();token=full['library_token']
        self.post('api/game/notes',{'game_id':'xgame','notes':'Retain this note'})
        changed,_,_=self.get(token)
        self.assertFalse(changed['library_unchanged']);self.assertNotEqual(changed['library_token'],token)
        self.assertEqual(changed['library']['library']['games'][0]['notes'],'Retain this note')
        token=changed['library_token'];self.store.library['achievements'][0]['unlocked']=True;self.store.save()
        changed,_,_=self.get(token);self.assertFalse(changed['library_unchanged'])
        self.assertTrue(changed['library']['library']['achievements'][0]['unlocked'])
    def test_partial_avoids_library_deepcopy_and_hash_recalculation(self):
        token=self.store.content_token()
        import copy
        def clone(value):
            if value is self.store.library:raise AssertionError('Full library was copied')
            return copy.deepcopy(value)
        with patch('atlas.core.deepcopy',side_effect=clone),patch('atlas.journal.content_token',side_effect=AssertionError('Hash repeated')):
            result=self.app.controller.status(token)
            self.assertTrue(result['library_unchanged'])
    def test_gzip_and_explicit_identity_roundtrip(self):
        plain,_,plain_size=self.get()
        packed,headers,size=self.get(encoding='br, gzip;q=1')
        self.assertEqual(plain,packed);self.assertEqual(headers['Content-Encoding'],'gzip')
        self.assertEqual(headers['Vary'],'Accept-Encoding');self.assertEqual(int(headers['Content-Length']),size)
        self.assertLess(size,plain_size//3)
        _,headers,_=self.get(encoding='gzip;q=0, *;q=1');self.assertNotIn('Content-Encoding',headers)
    def test_unknown_token_and_origin_guard(self):
        result,_,_=self.get('stale-token');self.assertFalse(result['library_unchanged'])
        with self.assertRaises(HTTPError) as error:urlopen(Request(self.app.url+'api/data',headers={'Origin':'https://evil.example','Accept-Encoding':'gzip'}))
        self.assertEqual(error.exception.code,403)
    def test_restore_and_restart_token_semantics(self):
        before=self.store.content_token();document=self.store.export_archive()
        self.store.library['games'][0]['notes']='Changed';self.store.save()
        self.assertNotEqual(self.store.content_token(),before)
        self.store.restore_archive(document)
        self.assertEqual(self.store.content_token(),before)
        restarted=Library(self.root.name)
        self.assertEqual(restarted.library,self.store.library)
        self.assertEqual(len(restarted.content_token()),64)
        # A restore may normalize JSON key order. A conservative token change is safe;
        # persisted records must stay identical and old clients can always request full data.
    def test_failed_save_does_not_advertise_unsaved_content(self):
        before=self.store.content_token();self.store.library['games'][0]['notes']='Unsaved'
        with patch('atlas.journal.save_pair',side_effect=OSError('disk full')),self.assertRaises(OSError):self.store.save()
        self.assertEqual(self.store.content_token(),before)
    def test_art_health_button_post_works_and_still_requires_token(self):
        with self.assertRaises(HTTPError) as error:self.post('api/art/health',{},token=False)
        self.assertEqual(error.exception.code,403)
        health=self.post('api/art/health',{});self.assertEqual(health['games'],1)
        self.assertEqual(health['missing']['cover'],1)

class EncodingTests(unittest.TestCase):
    def test_content_negotiation(self):
        for header in ('gzip','br, gzip','*;q=.5','gzip;q=0.3'):
            self.assertTrue(accepts_gzip(header),header)
        for header in ('','xgzip','gzip;q=0','gzip;q=0, *;q=1','gzip;q=nan','gzip;q=2','gzip;q=bad'):
            self.assertFalse(accepts_gzip(header),header)
