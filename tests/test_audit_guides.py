"""Consent/cost and cancellation regressions; no live provider calls."""
import json
import os
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from atlas import guides,settings
from atlas.core import Library
from atlas.server import Controller
from test_public_profiles import snapshot


def wait_guard(guard):
    deadline=time.monotonic()+3
    while guard.locked() and time.monotonic()<deadline:time.sleep(.005)
    if guard.locked():raise AssertionError('Worker did not finish')

class GuideConsentTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{},clear=True);self.env.start()
        self.tmp=TemporaryDirectory();self.c=Controller(self.tmp.name)
    def tearDown(self):
        wait_guard(self.c.public_guard);wait_guard(self.c.guide_guard)
        self.tmp.cleanup();settings._values={};self.env.stop()
    def sync_with(self,preference,configured=True):
        if preference is not None:os.environ['ATLAS_AUTO_GUIDES']=preference
        os.environ.update(BRAVE_SEARCH_API_KEY='fixture-brave',OPENAI_API_KEY='fixture-model')
        with patch('atlas.public_profiles.readiness',return_value={'xbox':True}),patch('atlas.public_profiles.fetch',return_value=snapshot()),patch.object(self.c,'download_media'),patch.object(self.c,'generate_guides') as generate,patch('atlas.guides.configured',return_value=configured):
            self.c.public_sync({'platform':'xbox','username':'Player1'});wait_guard(self.c.public_guard)
            self.assertEqual(len(self.c.store.library['achievements']),1)
            return generate.call_args_list
    def test_keys_alone_never_consent(self):self.assertEqual(self.sync_with(None),[])
    def test_explicit_off_never_calls(self):self.assertEqual(self.sync_with('0'),[])
    def test_only_explicit_one_dispatches(self):
        self.assertEqual(len(self.sync_with('1')),1)
    def test_missing_service_does_not_damage_profile(self):self.assertEqual(self.sync_with('1',False),[])
    def test_manual_is_independent_of_auto_off_and_safe_on_failure(self):
        self.c.store.apply_public_profile(snapshot());before=json.loads(json.dumps(self.c.store.library))
        os.environ['ATLAS_AUTO_GUIDES']='0'
        with patch('atlas.guides.configured',return_value=True),patch('atlas.guides.create',side_effect=ValueError('Rehber servisine erişilemedi: URLError')) as create:
            self.c.generate_guides({});wait_guard(self.c.guide_guard)
        create.assert_called_once();self.assertEqual(self.c.store.library,before)
        self.assertIn('erişilemedi',self.c.store.status['guide_job']['error'])
    def test_stop_current_completed_guide_keeps_result_but_no_next(self):
        snap=snapshot();second=dict(snap['achievements'][0],id='second',name='Second');snap['achievements'].append(second)
        self.c.store.apply_public_profile(snap)
        def create(a,stop):
            self.c.stop_guides()
            return {'fingerprint':guides.fingerprint(a),'steps':['Saved completed response']}
        with patch('atlas.guides.configured',return_value=True),patch('atlas.guides.create',side_effect=create) as mocked:
            self.c.generate_guides({});wait_guard(self.c.guide_guard)
        mocked.assert_called_once();items=self.c.store.library['achievements']
        self.assertTrue(items[0].get('guide'));self.assertNotIn('guide',items[1])
    def test_stop_after_search_prevents_openai_charge(self):
        stopped=False
        def response(*args,**kwargs):
            nonlocal stopped
            stopped=True
            return {'web':{'results':[{'url':'https://example.com/guide','title':'Fixture','description':'Source'}]}}
        with patch('atlas.guides.configured',return_value=True),patch('atlas.guides._json',side_effect=response) as network:
            with self.assertRaises(guides.Cancelled):guides.create(snapshot()['achievements'][0],stop=lambda:stopped)
        network.assert_called_once();self.assertIn('api.search.brave.com',network.call_args.args[0])
    def test_stop_before_start_sends_nothing(self):
        with patch('atlas.guides.configured',return_value=True),patch('atlas.guides._json') as network:
            with self.assertRaises(guides.Cancelled):guides.create(snapshot()['achievements'][0],stop=lambda:True)
        network.assert_not_called()

class ArchiveSafetyTests(unittest.TestCase):
    def test_bad_json_and_bad_root_never_open_empty_or_overwrite(self):
        for raw in (b'{broken',b'[]'):
            with TemporaryDirectory() as root:
                p=Path(root)/'library.json';p.write_bytes(raw)
                with self.assertRaisesRegex(ValueError,'Dosya değiştirilmedi'):Library(root)
                self.assertEqual(p.read_bytes(),raw)
    def test_migration_makes_exact_backup_and_is_idempotent(self):
        with TemporaryDirectory() as root:
            p=Path(root)/'library.json';state=Path(root)/'state.json'
            original=json.dumps({'games':[{'id':'g','platform':'xbox'}],'achievements':[{'id':'ta:1','game_id':'g','source':'trueachievements_csv','unlock_time':'3 Nov 2026','unlocked':True}],'unknown':{'preserve':True}}).encode()
            p.write_bytes(original);state.write_bytes(b'{"pins":["ta:1"]}')
            s=Library(root);self.assertTrue(s.library['unknown']['preserve']);self.assertEqual(s.state['pins'],['ta:1'])
            backup=Path(root)/'migration-v014-library.json';self.assertEqual(backup.read_bytes(),original)
            after=p.read_bytes();Library(root);self.assertEqual(p.read_bytes(),after);self.assertEqual(backup.read_bytes(),original)
    def test_status_revision_belongs_to_its_snapshot(self):
        with TemporaryDirectory() as root:
            c=Controller(root);initial=c.store.revision
            from atlas import recommendations
            rank=recommendations.rank
            def change_during_report(*args,**kw):
                c.store.save()
                return rank(*args,**kw)
            with patch('atlas.recommendations.rank',side_effect=change_during_report):reply=c.status()
            self.assertEqual(reply['revision'],initial);self.assertGreater(c.store.revision,reply['revision'])

class LegacyBoundaryTests(unittest.TestCase):
    def test_sdk_exception_details_are_not_browser_messages(self):
        from atlas.server import safe_error
        from atlas import xbox
        self.assertEqual(safe_error(RuntimeError('Authorization: secret-token')),'RuntimeError')
        self.assertEqual(safe_error(xbox.DirectError('Safe authored explanation')),'Safe authored explanation')
    def test_psn_cannot_be_mapped_or_scheduled_as_xbox(self):
        with TemporaryDirectory() as root:
            c=Controller(root);c.store.library['games']=[{'id':'psn','name':'Same','platform':'psn','title_id':'123'}]
            c.active_matches=[{'name':'Same','titleId':'123','platform':'one'}]
            with self.assertRaises(ValueError):c.xbox_map({'game_id':'psn','title_id':'123'})
            with self.assertRaises(ValueError):c.xbox_sync({})
