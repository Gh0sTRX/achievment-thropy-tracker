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
from .dates import normalize_unlock

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
            'source_url':url,'unlocked':earned,'unlock_time':normalize_unlock(r.get('UnlockDate')) if earned else '',
            'unlock_time_raw':str(r.get('UnlockDate') or '')[:120] if earned else '',
            'flag':str(r.get('Unachieveable') or '').strip().lower() in ('true','yes','1'),
            'description':'','icon_url':'','source':'trueachievements_csv','platform':'xbox'})
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


def empty_library():
    return {'schema': 2, 'platform': 'empty', 'gamertag': '', 'created_at': '',
            'complete_export': False, 'games': [], 'achievements': []}


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
        from . import archive
        archive.recover_interrupted_restore(self.root)
        self.revision=0
        self.library=self._read(self.library_path, empty_library())
        self.state=self._read(self.state_path, {'pins':[],'hidden':[],'custom_art':{},'xbox_titles':{},'linked_profile':None,'sync_at':None,'log':[]})
        for key,default in [('pins',[]),('hidden',[]),('custom_art',{}),('xbox_titles',{}),('linked_profile',None),('sync_at',None),('log',[])]:
            self.state.setdefault(key,deepcopy(default))
        from .preferences import DEFAULTS
        self.state['ui'] = {**deepcopy(DEFAULTS), **self.state.get('ui', {})}
        # Migrate v0.5/v0.6 demonstration rows; keep every real record and session.
        demo_games = {g['id'] for g in self.library.get('games', []) if g.get('platform') == 'demo'}
        demo_items = [a for a in self.library.get('achievements', [])
                      if a.get('source') == 'demo' or a.get('game_id') in demo_games or str(a.get('id', '')).startswith('demo:')]
        if demo_games or demo_items or self.library.get('platform') == 'demo':
            if self.library_path.exists():
                backup = self.root/'migration-v06-demo-backup.json'
                if not backup.exists(): atomic_write(backup, self.library)
            self.library['games'] = [g for g in self.library['games'] if g['id'] not in demo_games]
            removed = {a['id'] for a in demo_items}
            self.library['achievements'] = [a for a in self.library['achievements'] if a['id'] not in removed]
            if not self.library['games']: self.library = empty_library()
            self.state['pins'] = [x for x in self.state['pins'] if x not in removed]
            self.state['demo_removed'] = True
            self.save()
        migrated=False
        platform_by_game={g['id']:g.get('platform') for g in self.library.get('games',[])}
        for item in self.library.get('achievements',[]):
            if not item.get('platform') and platform_by_game.get(item.get('game_id')):
                item['platform']=platform_by_game[item['game_id']];migrated=True
            if item.get('source')=='trueachievements_csv' and item.get('unlock_time'):
                old=item['unlock_time'];normal=normalize_unlock(old)
                if normal!=old:
                    item.setdefault('unlock_time_raw',old);item['unlock_time']=normal;migrated=True
        if migrated:
            self._backup_migration()
            self.save()
        self.live_artwork={}
        self.steamgriddb_key=None
        self.status={'connected':False,'message':'No platform session','job':None,'art_job':None}

    def _backup_migration(self):
        # Preserve exact original bytes (including unknown fields) before v0.14 normalization.
        for original in (self.library_path,self.state_path):
            backup=original.with_name('migration-v014-'+original.name)
            if original.exists() and not backup.exists():
                try:
                    with backup.open('xb') as output:output.write(original.read_bytes())
                except FileExistsError:pass

    @staticmethod
    def _read(p,default):
        try:
            value=json.loads(p.read_text(encoding='utf-8'))
            if not isinstance(value,dict):raise ValueError('Expected an object')
            return value
        except FileNotFoundError:return deepcopy(default)
        except (OSError,ValueError) as exc:
            raise ValueError('Yerel JSON arşivi okunamadı: '+p.name+'. Dosya değiştirilmedi; yedeğini kontrol et.') from exc

    def save(self):
        self.revision+=1
        atomic_write(self.library_path,self.library)
        atomic_write(self.state_path,self.state)

    def export_archive(self):
        """Portable current library and non-secret state, not OAuth or image cache."""
        from . import archive
        with self.lock:
            return archive.make_archive(self.library, self.state)

    def restore_archive(self, document):
        """Restore is guarded by a disk rollback snapshot; credentials never imported."""
        from . import archive
        from .preferences import DEFAULTS
        with self.lock:
            verified = archive.verify_archive(document)
            state = verified['state']
            defaults = {'pins': [], 'hidden': [], 'custom_art': {}, 'xbox_titles': {},
                        'linked_profile': None, 'sync_at': None, 'log': []}
            for key, value in defaults.items():
                state.setdefault(key, deepcopy(value))
            state['ui'] = {**deepcopy(DEFAULTS), **state.get('ui', {})}
            document = archive.make_archive(verified['library'], state)
            restored = archive.restore_files(self.root, document, self.library, self.state)
            self.library, self.state = restored['library'], restored['state']
            self.revision += 1
            self.status = {'connected': False,
                           'message': 'Arşiv geri yüklendi; oturum yeniden doğrulanmalı.',
                           'job': None, 'art_job': None}
            return {'message': 'Kayıtlar güvenle geri yüklendi. Canlı hesap erişimini yeniden doğrula.',
                    'games': len(self.library['games']),
                    'achievements': len(self.library['achievements'])}

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
                for key in ('title_id','platform_edition','cover_url','hero_url','image_source','plan','notes','ownership','artwork_meta','art_theme','logo_url','banner_url','screenshot_url'):
                    if prior.get(key):g[key]=prior[key]
            for a in lib['achievements']:
                prior=old_ach.get(a['id']) or {}
                for key in ('icon_url','description'):
                    if prior.get(key):a[key]=prior[key]
                if prior.get('unlocked') and not a['unlocked']:
                    a['unlocked']=True;a['unlock_time']=prior.get('unlock_time','')
            # A TrueAchievements CSV is Xbox-only. Never delete an unrelated PSN/PC
            # collection when importing a new Xbox export into a mixed library.
            other_games = [deepcopy(g) for g in old['games']
                           if g.get('platform') not in ('xbox', 'demo')]
            other_ids = {g['id'] for g in other_games}
            if other_ids.intersection(g['id'] for g in lib['games']):
                raise ValueError('CSV oyun kimliği başka platformla çakışıyor; içe aktarma iptal edildi.')
            other_items = [deepcopy(a) for a in old['achievements']
                           if a.get('game_id') in other_ids]
            if other_games:
                lib['games'] = other_games + lib['games']
                lib['achievements'] = other_items + lib['achievements']
                lib['schema'] = 2
                lib['platform'] = 'mixed'
                lib['complete_export'] = False
            self.library=lib;self.save()
        imported_items = [a for a in lib['achievements'] if a['game_id'] not in other_ids]
        return {'games':len(lib['games'])-len(other_games),
                'achievements':len(imported_items),
                'earned':sum(a['unlocked'] for a in imported_items),
                'preserved_other_platform_games':len(other_games),
                'message':'Xbox CSV imported; other platforms and earned achievements preserved.'}

    def set_preferences(self, values):
        from .preferences import validate
        with self.lock:
            clean=validate(values,self.library['games'])
            self.state['ui'].update(clean)
            self.save()
        return {'message':'Görünüm tercihleri kaydedildi.'}

    def set_pin(self,aid,pinned):
        if aid not in {a['id'] for a in self.library['achievements']}:raise ValueError('Unknown achievement')
        with self.lock:
            pins=set(self.state['pins'])
            if pinned:pins.add(aid)
            else:pins.discard(aid)
            self.state['pins']=sorted(pins);self.save()
        return {'message':'Target updated'}

    def apply_public_profile(self, snapshot):
        """Commit a fully fetched profile atomically; never mix two players' unlocks."""
        platform = snapshot['platform']
        with self.lock:
            profiles = self.state.setdefault('public_profiles', {})
            previous = profiles.get(platform, {})
            same = previous.get('id') == snapshot['id']
            if previous.get('id'):
                previous_games = [g for g in self.library['games'] if g.get('platform') == platform]
                previous_ids = {g['id'] for g in previous_games}
                atomic_write(self.root/'profiles'/(game_id(platform, previous['id'])+'.json'),
                    {**previous, 'platform': platform, 'games': previous_games,
                     'achievements': [a for a in self.library['achievements'] if a['game_id'] in previous_ids]})
            # Archive each successful remote snapshot so changing the target is reversible.
            key = game_id(platform, snapshot['id'])
            archive = self.root/'profiles'/(key+'.json')
            cached = self._read(archive, {})
            old_items = {a['id']: a for a in (self.library['achievements'] if same else cached.get('achievements', []))}
            new_items = deepcopy(snapshot['achievements'])
            for a in new_items:
                prior = old_items.get(a['id'], {})
                if prior.get('unlocked'):
                    a['unlocked'] = True
                    a['unlock_time'] = prior.get('unlock_time', '')
                if prior.get('guide') and prior.get('description') == a.get('description') and prior.get('device_label','') == a.get('device_label','') and prior.get('platform_edition','') == a.get('platform_edition',''):
                    a['guide'] = prior['guide']
            new_games = deepcopy(snapshot['games'])
            prior_games = {g['id']: g for g in (self.library['games'] if same else cached.get('games', []))}
            failed = set(snapshot.get('failed_title_ids', []))
            retained_failed = [deepcopy(g) for g in prior_games.values() if g.get('title_id') in failed]
            retained_failed_ids = {g['id'] for g in retained_failed}
            new_games.extend(retained_failed)
            new_items.extend(deepcopy(a) for a in old_items.values() if a['game_id'] in retained_failed_ids)
            for g in new_games:
                prior = prior_games.get(g['id'], {})
                for field in ('hero_url', 'plan', 'notes', 'artwork_meta','art_theme','logo_url','banner_url','screenshot_url'):
                    if prior.get(field): g[field] = prior[field]
                if prior.get('cover_url') == 'local': g['cover_url'] = 'local'
            atomic_write(archive, {**snapshot, 'games': new_games, 'achievements': new_items})
            retained_games = [g for g in self.library['games'] if g.get('platform') not in (platform, 'demo')]
            retained_ids = {g['id'] for g in retained_games}
            retained_items = [a for a in self.library['achievements'] if a['game_id'] in retained_ids]
            self.library = {'schema': 2, 'platform': 'mixed', 'gamertag': snapshot['username'],
                'created_at': self.library.get('created_at', ''), 'complete_export': False,
                'games': retained_games+new_games, 'achievements': retained_items+new_items}
            profiles[platform] = {k: snapshot[k] for k in ('id', 'username', 'synced_at')}
            valid = {a['id'] for a in self.library['achievements']}
            self.state['pins'] = [p for p in self.state['pins'] if p in valid]
            self.state['sync_at'] = snapshot['synced_at']
            self.state['sync_warnings'] = deepcopy(snapshot.get('warnings', []))
            self.save()
        return {'games': len(new_games), 'achievements': len(new_items)}

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
