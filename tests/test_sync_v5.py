import asyncio
import tempfile
import time
import unittest
from unittest.mock import patch
from atlas import sync_control,dates

class DateTests(unittest.TestCase):
    def test_explicit_dates_and_ambiguous_rejection(self):
        for raw,out in [('2026-11-03','2026-11-03'),('03 Nov 2026','2026-11-03'),('2026-11-03T23:30:00+03:00','2026-11-03T23:30:00+03:00'),('45292','2024-01-01')]:self.assertEqual(dates.normalize_unlock(raw),out)
        for raw in ('03/11/2026','11/03/26','2026-02-30','60','garbage','3 Nov 26'):self.assertEqual(dates.normalize_unlock(raw),'')

class SyncTests(unittest.TestCase):
    def test_cancel_inflight_async_request(self):
        stopped=False
        async def run():
            nonlocal stopped
            token=sync_control.context.set({'stop':lambda:stopped})
            async def network():await asyncio.sleep(10)
            async def stop():
                nonlocal stopped
                await asyncio.sleep(.02);stopped=True
            asyncio.create_task(stop())
            try:
                with self.assertRaises(sync_control.Cancelled):await sync_control.request(network())
            finally:sync_control.context.reset(token)
        asyncio.run(run())
    def test_cache_scoped_identity_full_count_ttl_and_force(self):
        summary={'lastUnlock':'2026-11-03','currentAchievements':1,'totalAchievements':2}
        old={'id':'target','games':[{'id':'game','api_generation':'1','sync_signature':sync_control.signature(summary),'sync_checked_at':time.time()}],'achievements':[{'game_id':'game','id':'a'},{'game_id':'game','id':'b'}]}
        def reuse(identity='target',force=False):
            token=sync_control.context.set({'stop':lambda:False,'force':force,'cache':old})
            try:return sync_control.reuse({'id':'game','api_generation':'1'},summary,identity)
            finally:sync_control.context.reset(token)
        self.assertEqual(len(reuse()),2);self.assertIsNone(reuse('other'));self.assertIsNone(reuse(force=True))
        old['games'][0]['sync_checked_at']=time.time()-601;self.assertIsNone(reuse())
    def test_stop_api_prevents_profile_commit_and_followup(self):
        from atlas.server import Controller
        with tempfile.TemporaryDirectory() as root:
            c=Controller(root);before=c.store.payload()['library']
            def fetch(*args,**kw):
                c.stop_downloads({'kind':'profile'});raise sync_control.Cancelled()
            with patch('atlas.public_profiles.readiness',return_value={'xbox':True,'psn':False}),patch('atlas.public_profiles.fetch',side_effect=fetch),patch.object(c,'download_media') as media:
                c.public_sync({'platform':'xbox','username':'Player1'})
                end=time.time()+2
                while c.public_guard.locked() and time.time()<end:time.sleep(.01)
                self.assertTrue(c.store.status['public_job']['cancelled']);self.assertEqual(c.store.library,before);media.assert_not_called()
