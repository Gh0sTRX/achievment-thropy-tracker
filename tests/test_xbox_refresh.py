import asyncio
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from atlas import xbox


class RefreshTests(unittest.TestCase):
    def test_cancelled_waiter_does_not_release_another_refresh(self):
        async def scenario():
            xbox._refresh_lock.acquire()
            async def waiting():
                async with xbox._refresh_guard():self.fail('Acquired an owned refresh lock')
            try:
                task=asyncio.create_task(waiting());await asyncio.sleep(.01);task.cancel()
                with self.assertRaises(asyncio.CancelledError):await task
                self.assertTrue(xbox._refresh_lock.locked())
            finally:xbox._refresh_lock.release()
            async with xbox._refresh_guard():pass
        asyncio.run(scenario())

    def test_refresh_lock_is_released_before_api_queries(self):
        with TemporaryDirectory() as root:
            path=Path(root)/'tokens.json';path.write_text('0');sdk,_=self.sdk(path)
            async def scenario():
                async with xbox.authenticated_client():
                    self.assertFalse(xbox._refresh_lock.locked())
                    async with xbox.authenticated_client():pass
            with patch.object(xbox,'_sdk',return_value=sdk):asyncio.run(asyncio.wait_for(scenario(),1))
            self.assertEqual(path.read_text(),'2')

    def sdk(self,path,fail_once=False):
        state={'active':0,'maximum':0,'fail':fail_once};guard=threading.Lock()
        class Token:
            def __init__(self,n):self.n=n
            @staticmethod
            def model_validate_json(text):return Token(int(text))
            def model_dump_json(self):return str(self.n)
        class Signed:
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
        class Manager:
            def __init__(self,*args):self.xsts_token=SimpleNamespace(xuid='123')
            async def refresh_tokens(self):
                with guard:
                    state['active']+=1;state['maximum']=max(state['maximum'],state['active'])
                try:
                    await asyncio.sleep(.02)
                    if state['fail']:
                        state['fail']=False;raise ConnectionError('synthetic secret')
                    self.oauth=Token(self.oauth.n+1)
                finally:
                    with guard:state['active']-=1
        return (lambda manager:manager,Manager,Token,Signed,'client','unused','unused',path),state

    def test_parallel_threads_read_latest_rotated_token(self):
        with TemporaryDirectory() as root:
            path=Path(root)/'tokens.json';path.write_text('0')
            sdk,state=self.sdk(path)
            async def request():
                async with xbox.authenticated_client() as (_,xuid):self.assertEqual(xuid,'123')
            with patch.object(xbox,'_sdk',return_value=sdk),ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(lambda _:asyncio.run(request()),range(3)))
            self.assertEqual(path.read_text(),'3','Each refresh must read the most recently rotated token')
            self.assertEqual(state['maximum'],1)

    def test_failed_refresh_preserves_token_and_allows_retry(self):
        with TemporaryDirectory() as root:
            path=Path(root)/'tokens.json';path.write_text('0')
            sdk,_=self.sdk(path,fail_once=True)
            async def request():
                async with xbox.authenticated_client():pass
            with patch.object(xbox,'_sdk',return_value=sdk):
                with self.assertRaises(xbox.DirectError) as error:asyncio.run(request())
                self.assertNotIn('synthetic secret',str(error.exception));self.assertEqual(path.read_text(),'0')
                asyncio.run(request())
            self.assertEqual(path.read_text(),'1')
