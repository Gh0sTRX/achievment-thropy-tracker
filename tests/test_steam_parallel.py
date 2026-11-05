import threading
import time
import unittest
from unittest.mock import patch
from atlas import steam,public_profiles,sync_control
from test_steam import responses,SID


def provider(*args,**kw):
    if args[1]=='GetOwnedGames':return {'response':{'game_count':9,'games':[{'appid':i,'name':'Game '+str(i)} for i in range(1,10)]}}
    return responses(*args,**kw)

class ParallelSteamTests(unittest.TestCase):
    def test_three_workers_overlap_and_results_remain_ordered(self):
        barrier=threading.Barrier(3);lock=threading.Lock();active=0;peak=0
        original=steam.fetch_game
        def game(row,*args):
            nonlocal active,peak
            with lock:active+=1;peak=max(peak,active)
            try:
                barrier.wait(timeout=3)
                time.sleep((4-int(row['appid'])%3)*.001)
                return original(row,*args)
            finally:
                with lock:active-=1
        with patch.object(steam,'request',side_effect=provider),patch.object(steam,'fetch_game',side_effect=game):
            result=public_profiles.fetch('pc',SID)
        self.assertEqual(peak,3)
        self.assertEqual([g['id'] for g in result['games']],['steam:'+str(i) for i in range(1,10)])
        self.assertEqual(len({a['id'] for a in result['achievements']}),9)

    def test_context_cache_force_and_stop_are_visible_to_workers(self):
        observed=[]
        def game(row,*args):
            value=sync_control.context.get()
            observed.append((value['force'],value['cache']['marker'],value['stop']()))
            return steam_game(row,*args)
        steam_game=steam.fetch_game
        with patch.object(steam,'request',side_effect=provider),patch.object(steam,'fetch_game',side_effect=game):
            public_profiles.fetch('pc',SID,cache={'marker':'local-only'},force=True)
        self.assertEqual(observed,[(True,'local-only',False)]*9)

    def test_cancel_drains_only_current_batch(self):
        barrier=threading.Barrier(3);stopped=threading.Event();calls=[]
        def request(*args,**kw):
            if args[1]=='GetSchemaForGame':
                calls.append(int(kw['appid']));barrier.wait(timeout=3);stopped.set()
            return provider(*args,**kw)
        with patch.object(steam,'request',side_effect=request),self.assertRaises(sync_control.Cancelled):
            public_profiles.fetch('pc',SID,stop=stopped.is_set)
        self.assertEqual(sorted(calls),[1,2,3])

    def test_rate_limit_origin_wins_over_peer_cancellation(self):
        barrier=threading.Barrier(3);calls=[]
        def request(*args,**kw):
            if args[1]=='GetSchemaForGame':
                appid=int(kw['appid']);calls.append(appid);barrier.wait(timeout=3)
                if appid==2:raise steam.SteamError('RATE_LIMIT_ORIGIN',429)
                deadline=time.monotonic()+3
                while not sync_control.context.get()['stop']():
                    if time.monotonic()>deadline:raise AssertionError('Rate-limit stop not propagated')
                    time.sleep(.001)
            return provider(*args,**kw)
        with patch.object(steam,'request',side_effect=request),self.assertRaisesRegex(ValueError,'RATE_LIMIT_ORIGIN'):
            public_profiles.fetch('pc',SID)
        self.assertEqual(sorted(calls),[1,2,3])

    def test_title_failure_does_not_stop_other_titles_or_mix_ids(self):
        def request(*args,**kw):
            if args[1]=='GetSchemaForGame' and int(kw['appid'])==2:raise steam.SteamError('Temporary title failure',503)
            return provider(*args,**kw)
        events=[]
        with patch.object(steam,'request',side_effect=request):result=public_profiles.fetch('pc',SID,progress=lambda *x:events.append(x))
        self.assertEqual(result['failed_title_ids'],['2']);self.assertEqual(len(result['games']),8)
        self.assertEqual([e[0] for e in events],list(range(1,10)))
        self.assertTrue(all(a['id'].startswith(a['game_id']+':') for a in result['achievements']))

    def test_duplicate_owned_ids_are_rejected_before_title_requests(self):
        def request(*args,**kw):
            if args[1]=='GetOwnedGames':return {'response':{'game_count':2,'games':[{'appid':1},{'appid':1}]}}
            raise AssertionError('No title request should start')
        with patch.object(steam,'request',side_effect=request),self.assertRaisesRegex(ValueError,'AppID'):
            public_profiles.fetch('pc',SID)

    def test_auth_failure_keeps_archive_notes_and_pins_unchanged(self):
        from tempfile import TemporaryDirectory
        from atlas.server import Controller
        with TemporaryDirectory() as root:
            controller=Controller(root)
            with patch.object(steam,'request',side_effect=responses):old=public_profiles.fetch('pc',SID)
            controller.store.apply_public_profile(old)
            controller.store.library['games'][0]['notes']='Keep this note'
            controller.store.state['pins']=[old['achievements'][0]['id']]
            controller.store.save();before=controller.store.library_path.read_bytes()
            def request(*args,**kw):
                if args[1]=='GetSchemaForGame':raise steam.SteamError('AUTH_ACCESS_DENIED',403)
                return provider(*args,**kw)
            with patch.object(steam,'request',side_effect=request),patch.object(public_profiles,'readiness',return_value={'pc':True}),patch.object(controller,'download_media') as media:
                controller.public_sync({'platform':'pc','username':SID})
                deadline=time.monotonic()+4
                while controller.public_guard.locked() and time.monotonic()<deadline:time.sleep(.005)
                self.assertFalse(controller.public_guard.locked())
                media.assert_not_called()
            self.assertEqual(controller.store.library_path.read_bytes(),before)
            self.assertEqual(controller.store.state['pins'],[old['achievements'][0]['id']])
            self.assertEqual(controller.store.library['games'][0]['notes'],'Keep this note')
            self.assertIn('AUTH_ACCESS_DENIED',controller.store.status['public_job']['error'])
