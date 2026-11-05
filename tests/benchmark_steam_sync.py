"""Optional synthetic latency comparison; no real Steam account/network is used."""
import json
from pathlib import Path
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from atlas import steam,public_profiles
from test_steam import responses,SID


def main():
    results={}
    for workers in (1,3):
        samples=[]
        def request(*args,**kwargs):
            if args[1]=='GetOwnedGames':
                return {'response':{'game_count':30,'games':[{'appid':i,'name':f'Fixture {i}'} for i in range(1,31)]}}
            time.sleep(.005)
            return responses(*args,**kwargs)
        for _ in range(3):
            with patch.object(steam,'ThreadPoolExecutor',side_effect=lambda **kw:ThreadPoolExecutor(max_workers=workers)),patch.object(steam,'request',side_effect=request):
                start=time.perf_counter();result=public_profiles.fetch('pc',SID)
                samples.append(round((time.perf_counter()-start)*1000,2))
                assert len(result['achievements'])==30
        results[str(workers)]={'samples_ms':samples,'median_ms':statistics.median(samples)}
    print(json.dumps({'synthetic':True,'games':30,'request_delay_ms':5,'results':results},indent=2))

if __name__=='__main__':main()
