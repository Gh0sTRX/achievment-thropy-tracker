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

class MediaBatchTests(unittest.TestCase):
    def test_cached_icons_do_not_fetch_and_progress_finishes(self):
        from atlas import media_sync
        from atlas.core import Library
        with tempfile.TemporaryDirectory() as root:
            store=Library(root);store.library['achievements']=[{'id':'a1','game_id':'g','name':'Icon','icon_url':'https://xboxlive.com/a.png'}]
            events=[]
            with patch('atlas.artwork.cached',return_value=True),patch('atlas.artwork.cache_image') as fetch:
                result=media_sync.download(store,lambda *x:events.append(x))
            fetch.assert_not_called();self.assertEqual(result['downloaded'],0);self.assertEqual(events[-1][:2],(1,1))
    def test_bounded_icon_downloads_and_batched_writes(self):
        from atlas import media_sync
        from atlas.core import Library
        import threading
        with tempfile.TemporaryDirectory() as root:
            store=Library(root);store.library['achievements']=[{'id':f'a{i}','game_id':'g','name':'Icon','icon_url':f'https://xboxlive.com/{i}.png'} for i in range(32)]
            active=0;peak=0;guard=threading.Lock()
            def download(*args):
                nonlocal active,peak
                with guard:active+=1;peak=max(peak,active)
                time.sleep(.005)
                with guard:active-=1
            with patch('atlas.artwork.cached',return_value=None),patch('atlas.artwork.cache_image',side_effect=download),patch.object(store,'save',wraps=store.save) as save:
                result=media_sync.download(store)
                self.assertEqual(result['downloaded'],32);self.assertLessEqual(peak,4);self.assertGreater(peak,1);self.assertLessEqual(save.call_count,3)
    def test_stop_does_not_schedule_next_batch(self):
        from atlas import media_sync
        from atlas.core import Library
        stopped=False
        with tempfile.TemporaryDirectory() as root:
            store=Library(root);store.library['achievements']=[{'id':f'a{i}','game_id':'g','name':'Icon','icon_url':f'https://xboxlive.com/{i}.png'} for i in range(40)]
            def download(*args):
                nonlocal stopped
                stopped=True
            with patch('atlas.artwork.cached',return_value=None),patch('atlas.artwork.cache_image',side_effect=download) as fetch:
                result=media_sync.download(store,stop=lambda:stopped)
                self.assertLessEqual(fetch.call_count,4);self.assertLessEqual(result['downloaded'],4)

class MigrationTests(unittest.TestCase):
    def test_legacy_csv_keeps_ids_and_raw_date(self):
        from atlas.core import Library
        with tempfile.TemporaryDirectory() as root:
            s=Library(root);s.library['games']=[{'id':'g','platform':'xbox'}]
            s.library['achievements']=[{'id':'ta:12','game_id':'g','unlocked':True,'unlock_time':'03 Nov 2026','source':'trueachievements_csv'}];s.state['pins']=['ta:12'];s.save()
            new=Library(root);a=new.library['achievements'][0]
            self.assertEqual((a['id'],a['platform'],a['unlock_time']),('ta:12','xbox','2026-11-03'))
            self.assertEqual(a['unlock_time_raw'],'03 Nov 2026');self.assertEqual(new.state['pins'],['ta:12'])
