"""Synthetic offline archive acceptance; never contacts real provider accounts."""
import hashlib
import io
import json
import tempfile
import time
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from atlas import archive,artwork,recommendations
from atlas.core import Library
from atlas.server import Controller

EARNED='GameName,AchievementName,AchievementPageURL,Gamerscore,UnlockDate\nOffline Game,First,https://www.trueachievements.com/a456/first-achievement,20,2026-01-01\n'
LOCKED='GameName,AchievementName,AchievementPageURL,Gamerscore\nOffline Game,Second,https://www.trueachievements.com/a457/second-achievement,30\n'

class OfflineArchiveContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.store=Library(self.root)
  self.store.import_csv(EARNED,LOCKED,'SyntheticXbox')
 def add_profiles(self):
  self.store.state['public_profiles']={
   'xbox':{'id':'xuid-fixture','username':'SyntheticXbox'},
   'psn':{'id':'psn-fixture','username':'SyntheticPSN'},
   'pc':{'id':'76561198000000000','username':'SyntheticSteam','provider':'steam'}}
 def test_all_supported_profile_types_roundtrip(self):
  self.add_profiles();document=self.store.export_archive()
  self.store.restore_archive(document);fresh=Library(self.root)
  self.assertEqual(fresh.state['public_profiles'],self.store.state['public_profiles'])
  self.assertEqual(set(fresh.state['public_profiles']),{'xbox','psn','pc'})
 def test_portable_names_and_scoped_warnings_survive_without_access_secrets(self):
  self.store.state.update(provider_inputs={'xbox':'SyntheticXbox','psn':'SyntheticPSN','pc':'SyntheticSteam'},
   sync_warnings_by_platform={'pc':[{'game':'Synthetic Game','reason':'Private'}]},
   provider_access={'pc':{'state':'verified','secret':'NEVER_EXPORT'}},oauth_token='NEVER_EXPORT')
  document=self.store.export_archive();state=archive.verify_archive(document)['state']
  self.assertEqual(state.get('provider_inputs'),self.store.state['provider_inputs'])
  self.assertEqual(state.get('sync_warnings_by_platform'),self.store.state['sync_warnings_by_platform'])
  self.assertNotIn('provider_access',state);self.assertNotIn('NEVER_EXPORT',json.dumps(document))
 def test_offline_repeat_import_restart_restore_preserves_records_and_local_image(self):
  with patch('socket.create_connection',side_effect=AssertionError('Network is forbidden')):
   game=self.store.library['games'][0];game['notes']='Keep this offline note'
   image=io.BytesIO();Image.new('RGB',(16,16)).save(image,format='PNG');artwork.store_bytes(self.root,'cover',game['id'],image.getvalue());game['cover_url']='local'
   image_path=artwork.cached(self.root,'cover',game['id']);image_hash=hashlib.sha256(image_path.read_bytes()).hexdigest()
   self.store.set_pin('ta:457',True);self.store.save();before=deepcopy(self.store.library)
   self.store.import_csv(EARNED,LOCKED,'SyntheticXbox');self.assertEqual(self.store.library['games'][0]['notes'],'Keep this offline note')
   self.assertEqual({a['id'] for a in self.store.library['achievements']},{'ta:456','ta:457'})
   fresh=Library(self.root);document=fresh.export_archive();archive.verify_archive(document)
   fresh.library['games'][0]['notes']='changed';fresh.save();fresh.restore_archive(document);reopened=Library(self.root)
   self.assertEqual(reopened.library['games'][0]['notes'],before['games'][0]['notes']);self.assertEqual(reopened.state['pins'],['ta:457'])
   self.assertEqual(next(a for a in reopened.library['achievements'] if a['id']=='ta:456')['unlock_time'],'2026-01-01')
   self.assertEqual(hashlib.sha256(image_path.read_bytes()).hexdigest(),image_hash)
   self.assertTrue(recommendations.rank(reopened.library,reopened.state['pins']))
 def test_recovery_backup_accepts_steam_profile_in_existing_state(self):
  document=self.store.export_archive();self.add_profiles();self.store.save();self.store.restore_archive(document)
  copies=list((self.root/'recovery').glob('pre-restore-*.json'));self.assertEqual(len(copies),1)
  recovered=archive.verify_archive(json.loads(copies[0].read_text()))
  self.assertEqual(recovered['state']['public_profiles']['pc']['provider'],'steam')
 def test_failed_online_attempt_keeps_offline_library_usable(self):
  controller=Controller(self.root);controller.store.set_pin('ta:457',True)
  before=deepcopy(controller.store.library)
  with patch('atlas.public_profiles.readiness',return_value={'xbox':True,'psn':False,'pc':False}),patch('atlas.public_profiles.fetch',side_effect=ConnectionError('offline')):
   controller.public_sync({'platform':'xbox','username':'SyntheticXbox'})
   deadline=time.monotonic()+3
   while controller.public_guard.locked() and time.monotonic()<deadline:time.sleep(.01)
  self.assertFalse(controller.public_guard.locked());self.assertEqual(controller.store.library,before)
  self.assertEqual(Library(self.root).state['pins'],['ta:457']);archive.verify_archive(controller.store.export_archive())
 def test_unsupported_or_malformed_portable_profiles_are_rejected(self):
  for profiles in ({'epic':{'username':'unsupported'}},{'pc':{'username':[]}}):
   with self.subTest(profiles=profiles),self.assertRaises(ValueError):archive.make_archive(self.store.library,{'public_profiles':profiles})
 def test_malformed_or_secret_named_portable_inputs_are_rejected(self):
  for value in ({'ATLAS_STEAM_API_KEY':'not-a-real-key'},{'pc':[]},{'xbox':'x'*201}):
   with self.subTest(value=value),self.assertRaises(ValueError):archive.make_archive(self.store.library,{'provider_inputs':value})
 def test_malformed_scoped_warnings_are_rejected(self):
  for value in ({'epic':[]},{'pc':{}},{'pc':[{'reason':'Missing title'}]}):
   with self.subTest(value=value),self.assertRaises(ValueError):archive.make_archive(self.store.library,{'sync_warnings_by_platform':value})
