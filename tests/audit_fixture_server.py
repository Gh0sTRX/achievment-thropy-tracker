"""Optional local-only synthetic fixtures; never reads real account credentials or data."""
import json,sys,threading,time
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from atlas.server import LocalApp
from atlas import artwork
Path('work/audit').mkdir(parents=True,exist_ok=True)
fixtures=[];urls={};metrics={}
for count in (80,5000,15000,40000):
 root=TemporaryDirectory(prefix='atlas-audit-');fixtures.append(root);app=LocalApp(root.name)
 games=[];items=[];game_count=max(4,count//50)
 for i in range(game_count):
  platform='xbox' if i%2==0 else 'psn';device=('xbox360' if i%4==0 else 'windows') if platform=='xbox' else ('ps3' if i%4==1 else 'ps5')
  games.append({'id':f'audit-game-{i}','title_id':str(1000+i),'name':f'AUDIT GAME {i:04} <img src=x onerror="window.pwned=1">','platform':platform,'devices':[device],'platform_edition':device,'hero_url':'','cover_url':''})
 for i in range(count):
  g=games[i%game_count]
  items.append({'id':f'audit-ach-{i}','game_id':g['id'],'game_name':g['name'],'name':f'AUDIT ACH {i} <script>window.pwned=1</script>','description':'Fixture only <img src=x onerror="window.pwned=1">','points':10 if g['platform']=='xbox' else 0,'platform':g['platform'],'unlocked':i%3==0,'unlock_time':'2026-11-03T10:00:00+03:00' if i%3==0 else '', 'is_secret':i%5==1,'trophy_type':'bronze' if g['platform']=='psn' else '', 'source':'audit_fixture'})
 if count==80:
  app.controller.store.state['provider_inputs']={'xbox':'SyntheticXbox'}
  items[0]['description']='Sentetik sağlayıcı açıklaması';items[0]['icon_url']=''
  items[3]['unlock_time']='';items[6]['unlock_time']='03/04/2026';items[6]['unlock_time_raw']='03/04/2026'
  artwork.store_bytes(Path(root.name),'icon',items[0]['id'],Path('assets/atlas-mark.png').read_bytes())
  artwork.store_bytes(Path(root.name),'cover',games[1]['id'],Path('assets/atlas-mark.png').read_bytes());games[1]['cover_url']='local'
 app.controller.store.library={'schema':2,'gamertag':'AUDIT FIXTURE — NOT A LIVE PROFILE','complete_export':False,'games':games,'achievements':items}
 # Original application mark used only as a test image; no game art is generated.
 artwork.store_bytes(Path(root.name),'hero',games[0]['id'],Path('assets/atlas-mark.png').read_bytes());games[0]['hero_url']='local'
 timings=[]
 for _ in range(3):
  start=time.perf_counter();app.controller.status();timings.append(round((time.perf_counter()-start)*1000,2))
 metrics[str(count)]={'games':game_count,'status_ms':timings}
 threading.Thread(target=app.serve_forever,daemon=True).start();urls[str(count)]=app.url
Path('work/audit/fixture-urls.json').write_text(json.dumps(urls));Path('work/audit/server-performance.json').write_text(json.dumps(metrics,indent=2))
threading.Event().wait()
