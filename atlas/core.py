"""Portable, strictly local achievement library; no account identifiers in source release."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
import re
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MAX_CSV_BYTES = 5_000_000
TA_ID = re.compile(r'/a(\d{2,12})/')


def data_dir() -> Path:
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or Path.home())
    else:
        base = Path(os.environ.get('XDG_DATA_HOME') or (Path.home()/'.local'/'share'))
    return base/'AchievementAtlas'


def game_id(platform: str, title: str) -> str:
    return hashlib.sha256((platform+'\0'+title.strip().casefold()).encode()).hexdigest()[:20]


def normalize(text: str) -> str:
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKC',str(text or '')).casefold() if c.isalnum())


def parse_csv_text(data: str, earned: bool) -> list[dict]:
    if not isinstance(data,str) or len(data.encode('utf-8')) > MAX_CSV_BYTES:
        raise ValueError('CSV dosyası geçersiz veya 5 MB sınırını aşıyor.')
    rows = list(csv.DictReader(io.StringIO(data.lstrip('\ufeff'))))
    if len(rows)>15000:
        raise ValueError('Tek CSV dosyasında en fazla 15.000 kayıt destekleniyor.')
    if not rows:
        return []
    for field in ('GameName','AchievementName','AchievementPageURL','Gamerscore'):
        if field not in rows[0]: raise ValueError('TrueAchievements CSV sütunu eksik: '+field)
    parsed=[]
    for r in rows:
        url=(r.get('AchievementPageURL') or '').strip()
        u=urlparse(url)
        if u.scheme!='https' or u.hostname not in ('www.trueachievements.com','trueachievements.com'):
            continue
        m=TA_ID.search(u.path)
        if not m: continue
        name=(r.get('AchievementName') or '').strip()[:180]
        game=(r.get('GameName') or '').strip()[:180]
        if not name or not game: continue
        try: gs=int(float(r.get('Gamerscore') or 0))
        except (TypeError,ValueError): gs=0
        try:ratio=float(r.get('TARatio') or 0)
        except (TypeError,ValueError):ratio=0
        parsed.append({'id':'ta:'+m.group(1),'provider_id':m.group(1),
            'game_id':game_id('xbox',game),'game_name':game,'name':name,'points':max(0,min(10000,gs)),
            'ratio':round(max(0,min(1000,ratio)),2),'dlc':(r.get('DLCName') or '').strip()[:140],
            'source_url':url,'unlocked':earned,'unlock_time':(r.get('UnlockDate') or '') if earned else '',
            'flag':str(r.get('Unachieveable') or '').strip().lower() in ('true','yes','1'),
            'description':'','icon_url':'','source':'trueachievements_csv'})
    return parsed


def build_library(earned_csv: str, locked_csv: str, gamertag: str='') -> dict:
    items = {}
    for x in parse_csv_text(locked_csv,False): items[x['id']] = x
    for x in parse_csv_text(earned_csv,True):
        existing=items.get(x['id'])
        if existing and existing['game_id']!=x['game_id']:
            raise ValueError('Aynı başarıma farklı oyun atanmış; import iptal edildi.')
        items[x['id']]=x
    if not items: raise ValueError('İçe aktarılabilecek TrueAchievements kaydı bulunamadı.')
    games={}
    for item in items.values():
        gid=item['game_id']
        if gid not in games:
            games[gid]={'id':gid,'name':item['game_name'],'platform':'xbox','title_id':'',
                        'platform_edition':'unknown','cover_url':'','hero_url':'','image_source':'',
                        'plan':'','notes':'','ownership':'unknown'}
    return {'schema':1,'platform':'xbox','gamertag':gamertag.strip()[:80],
            'created_at':datetime.now(timezone.utc).isoformat(),
            'complete_export':bool(earned_csv.strip() and locked_csv.strip()),
            'games':list(games.values()),'achievements':list(items.values())}


def make_sample() -> dict:
    names=['ORBITAL RANGER','PIXEL VALLEY','DEEP BLUE','NIGHT DRIVE']
    badges=[('First Steps',10,1.05),('Explorer',25,1.35),('Challenge Accepted',40,1.9),('Final Chapter',100,3.1),('Collector',50,2.2)]
    games=[];ach=[]
    for i,name in enumerate(names):
        gid=game_id('demo',name)
        games.append({'id':gid,'name':name,'platform':'demo','title_id':'',
            'platform_edition':'demo','cover_url':'','hero_url':'','image_source':'',
            'plan':'Demo game — not a real platform title','notes':'','ownership':'unknown'})
        for j,(t,pts,ratio) in enumerate(badges):
            ach.append({'id':f'demo:{i}:{j}','provider_id':f'demo:{i}:{j}',
                'game_id':gid,'game_name':name,'name':t,'points':pts,'ratio':ratio,
                'dlc':'','source_url':'','unlocked':j < (i+1)%4,'unlock_time':'',
                'flag':False,'description':'Demonstration only. Import your own data to replace this.',
                'icon_url':'','source':'demo'})
    return {'schema':1,'platform':'demo','gamertag':'','created_at':'',
            'complete_export':False,'games':games,'achievements':ach}


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,path)


class Library:
    def __init__(self, root=None):
        self.root=Path(root) if root else data_dir()
        self.library_path=self.root/'library.json'
        self.state_path=self.root/'state.json'
        self.lock=threading.RLock()
        self.library=self._read(self.library_path, make_sample())
        self.state=self._read(self.state_path, {'pins':[],'hidden':[],'custom_art':{},'xbox_titles':{},'linked_profile':None,'sync_at':None,'log':[]})
        for key,default in [('pins',[]),('hidden',[]),('custom_art',{}),('xbox_titles',{}),('linked_profile',None),('sync_at',None),('log',[])]:
            self.state.setdefault(key,deepcopy(default))
        self.live_artwork={}
        self.steamgriddb_key=None
        self.status={'connected':False,'message':'No platform session','job':None,'art_job':None}

    @staticmethod
    def _read(p,default):
        try:return json.loads(p.read_text(encoding='utf-8'))
        except (OSError,ValueError):return deepcopy(default)

    def save(self):
        atomic_write(self.library_path,self.library)
        atomic_write(self.state_path,self.state)

    def payload(self):
        with self.lock:
            return {'library':deepcopy(self.library),'state':deepcopy(self.state),'status':deepcopy(self.status)}

    def import_csv(self,earned,locked,gamertag=''):
        lib=build_library(earned,locked,gamertag)
        linked=(self.state.get('linked_profile') or {}).get('gamertag','')
        if linked and gamertag and normalize(linked)!=normalize(gamertag):
            raise ValueError('The CSV gamertag differs from the connected Xbox account. Disconnect first to avoid mixing users.')
        with self.lock:
            old=self.library
            old_games={g['id']:g for g in old['games']}
            old_ach={a['id']:a for a in old['achievements']}
            for g in lib['games']:
                prior=old_games.get(g['id']) or {}
                for key in ('title_id','platform_edition','cover_url','hero_url','image_source','plan','notes','ownership'):
                    if prior.get(key):g[key]=prior[key]
            for a in lib['achievements']:
                prior=old_ach.get(a['id']) or {}
                for key in ('icon_url','description'):
                    if prior.get(key):a[key]=prior[key]
                if prior.get('unlocked') and not a['unlocked']:
                    a['unlocked']=True;a['unlock_time']=prior.get('unlock_time','')
            self.library=lib;self.save()
        return {'games':len(lib['games']),'achievements':len(lib['achievements']),
                'earned':sum(a['unlocked'] for a in lib['achievements']),'message':'Library imported; saved achievements never revoked.'}

    def set_pin(self,aid,pinned):
        if aid not in {a['id'] for a in self.library['achievements']}:raise ValueError('Unknown achievement')
        with self.lock:
            pins=set(self.state['pins'])
            if pinned:pins.add(aid)
            else:pins.discard(aid)
            self.state['pins']=sorted(pins);self.save()
        return {'message':'Target updated'}

    def apply_live_game(self,game_id,api_items):
        """Exact title identity first, unambiguous name + points second. Never cross game boundary."""
        with self.lock:
            matches={}
            for a in self.library['achievements']:
                if a['game_id']==game_id:
                    matches.setdefault((normalize(a['name']),int(a['points'])),[]).append(a)
            changed=0;unmatched=0;ambiguous=0
            for remote in api_items:
                key=(normalize(remote.get('name')),int(remote.get('gamerscore') or 0))
                candidates=matches.get(key,[])
                if len(candidates)!=1:
                    if candidates:ambiguous+=1
                    else:unmatched+=1
                    continue
                a=candidates[0]
                if remote.get('unlocked') and not a['unlocked']:
                    a['unlocked']=True;a['unlock_time']=remote.get('timeUnlocked') or '';changed+=1
                if remote.get('icon'):
                    a['icon_url']=str(remote['icon'])[:2048]
                if remote.get('description'):
                    a['description']=str(remote['description'])[:2000]
                if remote.get('progress_current') is not None and remote.get('progress_target') is not None:
                    try:
                        current=float(remote['progress_current']);target=float(remote['progress_target'])
                        if 0<=current<=target and target>0:
                            a['progress_current']=current;a['progress_target']=target
                    except (ValueError,TypeError):pass
            self.state['sync_at']=datetime.now(timezone.utc).isoformat()
            self.save()
        return {'updated':changed,'unmatched':unmatched,'ambiguous':ambiguous}