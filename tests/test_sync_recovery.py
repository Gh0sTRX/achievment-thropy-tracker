import time
import unittest
from copy import deepcopy
from tempfile import TemporaryDirectory
from unittest.mock import patch
from atlas.server import Controller
from atlas import public_profiles


class SyncRecoveryTests(unittest.TestCase):
    def wait(self,c):
        deadline=time.monotonic()+3
        while c.public_guard.locked() and time.monotonic()<deadline:time.sleep(.005)
        self.assertFalse(c.public_guard.locked(),'Retry guard remained locked')

    def snapshot(self):
        game=public_profiles.game('xbox','12','Test','360')
        item=public_profiles.achievement(game,{'id':'1','name':'First','unlocked':True})
        return {'platform':'xbox','id':'123','username':'Player','synced_at':'2026-11-06','games':[game],'achievements':[item]}

    def test_network_failure_then_retry_without_restart_preserves_archive(self):
        with TemporaryDirectory() as root:
            c=Controller(root);c.store.apply_public_profile(self.snapshot())
            c.store.library['games'][0]['notes']='keep'
            c.store.state['pins']=[c.store.library['achievements'][0]['id']];c.store.save()
            before=deepcopy(c.store.library)
            with patch.object(public_profiles,'readiness',return_value={'xbox':True}),patch.object(public_profiles,'fetch',side_effect=[ConnectionError('SECRET'),self.snapshot()]),patch.object(c,'download_media'),patch('atlas.server.settings.get',return_value='0'):
                c.public_sync({'platform':'xbox','username':'Player'});self.wait(c)
                self.assertEqual(c.store.library,before)
                self.assertTrue(c.store.status['public_job']['error'])
                c.public_sync({'platform':'xbox','username':'Player'});self.wait(c)
            self.assertFalse(c.store.status['public_job']['error'])
            self.assertEqual(c.store.state['provider_access']['xbox']['state'],'verified')
            self.assertEqual(c.store.library['games'][0]['notes'],'keep')
            self.assertTrue(c.store.state['pins'])

    def test_optional_followup_failures_are_not_account_errors(self):
        with TemporaryDirectory() as root:
            c=Controller(root)
            with patch.object(public_profiles,'readiness',return_value={'xbox':True}),patch.object(public_profiles,'fetch',return_value=self.snapshot()),patch.object(c,'download_media',side_effect=RuntimeError('SECRET')),patch.object(c,'generate_guides',side_effect=RuntimeError('SECRET')),patch('atlas.server.settings.get',return_value='1'),patch('atlas.server.guides.configured',return_value=True):
                c.public_sync({'platform':'xbox','username':'Player'});self.wait(c)
            self.assertFalse(c.store.status['public_job']['error'])
            self.assertEqual(c.store.state['provider_access']['xbox']['state'],'verified')
            self.assertEqual(len(c.store.library['achievements']),1)
            events=c.store.state['activity_history']
            self.assertEqual([x['kind'] for x in events],['media','guides','profile'])
            self.assertTrue(events[0]['error']);self.assertTrue(events[1]['error']);self.assertFalse(events[2]['error'])
            self.assertNotIn('SECRET',str(events));self.assertNotIn('SECRET',str(c.store.status))
