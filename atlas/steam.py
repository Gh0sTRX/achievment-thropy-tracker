"""Steam Web API PC provider. No scraping, title guessing or Gamerscore conversion."""
from datetime import datetime, timezone
import json
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from . import settings, sync_control, artwork

class SteamError(ValueError):
    def __init__(self, message, code=None):
        super().__init__(message); self.code=code

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise SteamError('Steam API yönlendirmesi reddedildi.')


def validate(value):
    value=str(value).strip()
    if value.startswith('https://'):
        u=urlsplit(value)
        if u.hostname!='steamcommunity.com' or u.username or u.password or u.port not in (None,443) or u.query or u.fragment:
            raise SteamError('SteamID64 veya resmi Steam profil adresini gir.')
        parts=u.path.strip('/').split('/')
        if len(parts)!=2 or parts[0] not in ('id','profiles'):raise SteamError('Steam profil adresi geçersiz.')
        value=parts[1]
        if parts[0]=='profiles' and not value.isdigit():raise SteamError('SteamID64 geçersiz.')
    if value.isdigit():
        if not 76561197960265728<=int(value)<2**64:raise SteamError('SteamID64 geçersiz.')
    elif not re.fullmatch(r'[A-Za-z0-9_-]{2,64}',value):raise SteamError('Steam kullanıcı adresini veya SteamID64 gir.')
    return value


def request(interface,method,version='v1',**params):
    sync_control.check()
    key=settings.get('ATLAS_STEAM_API_KEY')
    if not key:raise SteamError('Steam Web API anahtarı cihazda ayarlanmamış.')
    url='https://api.steampowered.com/'+interface+'/'+method+'/'+version+'/?'+urlencode({'key':key,**params})
    try:
        with build_opener(NoRedirect()).open(Request(url,headers={'User-Agent':'AchievementAtlas'}),timeout=20) as response:
            raw=response.read(4_000_001)
        if len(raw)>4_000_000:raise SteamError('Steam yanıtı boyut sınırını aştı.')
        result=json.loads(raw)
        if not isinstance(result,dict):raise SteamError('Steam yanıt biçimi geçersiz.')
        sync_control.check();return result
    except HTTPError as e:
        messages={401:'Steam anahtarı reddedildi.',403:'Steam erişimi reddedildi; gizlilik veya anahtarı kontrol et.',429:'Steam hız sınırı; daha sonra yeniden dene.'}
        raise SteamError(messages.get(e.code,'Steam servisi isteği tamamlayamadı.'),e.code) from None
    except (URLError,TimeoutError,OSError,json.JSONDecodeError):
        # Never expose a request URL: it contains the service key.
        raise SteamError('Steam ağ yanıtı alınamadı; önceki kayıt korundu.') from None


SCHEMA_TTL=6*60*60
MAX_TITLE_WORKERS=3

def clean_schema(schema):
    if not isinstance(schema,dict) or not isinstance(schema.get('gameName'),str) or not schema['gameName']:
        raise SteamError('Steam oyun şeması alınamadı.')
    stats=schema.get('availableGameStats',{})
    if not isinstance(stats,dict):raise SteamError('Steam başarım şeması geçersiz.')
    definitions=stats.get('achievements',[])
    if not isinstance(definitions,list):raise SteamError('Steam başarım şeması geçersiz.')
    seen=set();clean=[]
    for row in definitions:
        if not isinstance(row,dict) or not isinstance(row.get('name'),str) or not row['name'] or row['name'] in seen:
            raise SteamError('Steam başarım şeması kimlikleri geçersiz.')
        seen.add(row['name'])
        clean.append({k:row[k] for k in ('name','displayName','description','hidden','icon','icongray') if k in row})
    return {'gameName':schema['gameName'],'availableGameStats':{'achievements':clean}}

def schema_for(appid,refresh=False):
    """Only public schema metadata is cached; player unlocks and keys never enter it."""
    if not re.fullmatch(r'[1-9][0-9]{0,9}',str(appid)) or int(appid)>4294967295:raise SteamError('Steam AppID geçersiz.')
    context=sync_control.context.get() or{}
    root=(context.get('cache') or{}).get('schema_root')
    path=Path(root)/(str(appid)+'-english.json') if root else None
    if path and not refresh and not context.get('force'):
        try:
            if path.stat().st_size<=4_000_000:
                cached=json.loads(path.read_text(encoding='utf-8'))
                age=time.time()-cached['fetched_at']
                schema=clean_schema(cached['schema'])
                if cached.get('version')==1 and cached.get('appid')==str(appid) and cached.get('language')=='english' and 0<=age<SCHEMA_TTL and schema['availableGameStats']['achievements']:
                    return schema
        except (OSError,ValueError,TypeError,KeyError):pass
    schema=clean_schema(request('ISteamUserStats','GetSchemaForGame','v2',appid=appid,l='english').get('game',{}))
    sync_control.check()
    if path and schema['availableGameStats']['achievements']:
        try:
            from .core import atomic_write
            atomic_write(path,{'version':1,'appid':str(appid),'language':'english','fetched_at':time.time(),'schema':schema})
        except OSError:pass # Cache failure must not discard successfully fetched profile data.
    return schema



def fetch_game(row,sid,known_games):
    appid=str(row['appid'])
    schema=schema_for(appid)
    sync_control.check()
    definitions=schema['availableGameStats']['achievements']
    if not definitions and 'steam:'+appid in known_games:
        raise SteamError('Steam boş şema döndürdü; önceki başarım listesi korunur.')
    player={}
    if definitions:
        stats=request('ISteamUserStats','GetPlayerAchievements',steamid=sid,appid=appid,l='english').get('playerstats',{})
        if stats.get('success') is not True or str(stats.get('steamID',''))!=sid:raise SteamError('Steam başarım görünürlüğü veya hesap kimliği doğrulanamadı.')
        entries=stats.get('achievements',[])
        if not isinstance(entries,list):raise SteamError('Steam kazanım listesi geçersiz.')
        if any(not isinstance(a,dict) or not isinstance(a.get('apiname'),str) or not a['apiname'] for a in entries):
            raise SteamError('Steam başarım satırı geçersiz; önceki oyun kaydı korunur.')
        player={a.get('apiname'):a for a in entries}
        if len(player)!=len(entries):raise SteamError('Tekrarlanan Steam başarım kimliği.')
        if set(player)!={row['name'] for row in definitions}:
            schema=schema_for(appid,refresh=True)
            definitions=schema['availableGameStats']['achievements']
            if set(player)!={row['name'] for row in definitions}:raise SteamError('Steam şeması ve kazanım listesi uyuşmuyor; önceki kayıt korundu.')
    gid='steam:'+appid;name=str(row.get('name') or schema['gameName'])
    g={'id':gid,'title_id':appid,'steam_appid':appid,'provider':'steam','platform':'pc','name':name,'platform_edition':'steam','devices':['pc'],'device_label':'PC · Steam','ownership':'unknown','art_candidates':[]}
    # AppID comes from this account's official list, never a title match.
    for kind,filename in (('cover','library_600x900.jpg'),('hero','library_hero.jpg'),('logo','logo.png'),('banner','header.jpg')):
        url='https://cdn.akamai.steamstatic.com/steam/apps/'+appid+'/'+filename
        g['art_candidates'].append({'kind':kind,'url':url,'provider':'Steam AppID','provider_id':appid})
    current=[];keys=set()
    for definition in definitions:
        api=definition.get('name')
        if not isinstance(api,str) or not api or api in keys or api not in player:raise SteamError('Steam başarım kimlikleri eksik veya tekrarlı.')
        keys.add(api);entry=player[api]
        if type(entry.get('achieved')) is not int or entry['achieved'] not in (0,1):raise SteamError('Steam kazanılma bilgisi eksik.')
        unlocked=bool(entry['achieved']);stamp='';epoch=entry.get('unlocktime')
        if unlocked and type(epoch) is int and epoch>0:
            try:stamp=datetime.fromtimestamp(epoch,timezone.utc).isoformat()
            except (OverflowError,OSError,ValueError):pass
        icon=definition.get('icon' if unlocked else 'icongray','')
        current.append({'id':gid+':'+api,'provider_id':api,'provider':'steam','game_id':gid,'title_id':appid,'game_name':name,'platform':'pc','devices':['pc'],'device_label':'PC · Steam','platform_edition':'steam','name':str(definition.get('displayName') or api),'description':str(definition.get('description') or ''),'is_secret':definition.get('hidden') in (1,True),'unlocked':unlocked,'unlock_time':stamp,'points':0,'trophy_type':'','dlc':'','icon_url':icon if artwork.safe_url(icon) else '', 'source':'steam_web_api'})
    return g,current


def fetch(username,progress=lambda *args:None):
    value=validate(username)
    if value.isdigit():sid=value
    else:
        resolved=request('ISteamUser','ResolveVanityURL',vanityurl=value).get('response',{})
        sid=str(resolved.get('steamid',''))
        if resolved.get('success')!=1 or not sid.isdigit():raise SteamError('Steam kullanıcı adresi çözümlenemedi.')
        validate(sid)
    owned=request('IPlayerService','GetOwnedGames',steamid=sid,include_appinfo=1,include_played_free_games=1).get('response',{})
    if type(owned.get('game_count')) is not int or not isinstance(owned.get('games',[]),list):
        raise SteamError('Steam oyun ayrıntıları gizli veya erişilemiyor. Profil ve oyun ayrıntılarını herkese açık yap.')
    if owned['game_count']!=len(owned.get('games',[])):raise SteamError('Steam oyun listesi eksik; önceki kayıt korundu.')
    context=sync_control.context.get() or{}
    cache=context.get('cache') or{}
    # Legacy archives without an account ID still receive conservative protection.
    known_games={a.get('game_id') for a in cache.get('achievements',[])} if not cache.get('id') or str(cache['id'])==sid else set()
    games=[];items=[];warnings=[];failed=[];seen=set()
    rows=owned.get('games',[])
    for row in rows:
        if not isinstance(row,dict):raise SteamError('Steam oyun listesi geçersiz.')
        appid=str(row.get('appid',''))
        if not appid.isdigit() or not 0<int(appid)<=4294967295 or appid in seen:raise SteamError('Steam AppID listesi geçersiz.')
        seen.add(appid)
    halted=threading.Event()
    parent_stop=context.get('stop',lambda:False)
    def worker(row):
        token=sync_control.context.set({**context,'stop':lambda:halted.is_set() or parent_stop()})
        try:
            sync_control.check()
            result=fetch_game(row,sid,known_games)
            sync_control.check()
            return result
        except SteamError as exc:
            if exc.code in (401,403,429):halted.set()
            raise
        except BaseException:
            halted.set()
            raise
        finally:sync_control.context.reset(token)
    # A batch holds at most three titles. No full-library task queue survives stop/429.
    with ThreadPoolExecutor(max_workers=MAX_TITLE_WORKERS,thread_name_prefix='atlas-steam') as pool:
        for offset in range(0,len(rows),MAX_TITLE_WORKERS):
            sync_control.check()
            batch=rows[offset:offset+MAX_TITLE_WORKERS]
            futures=[pool.submit(copy_context().run,worker,row) for row in batch]
            outcomes=[];fatal=[]
            for row,future in zip(batch,futures):
                try:outcomes.append((row,future.result(),None))
                except SteamError as exc:
                    if exc.code in (401,403,429):fatal.append(exc)
                    else:outcomes.append((row,None,exc))
                except BaseException as exc:fatal.append(exc)
            if parent_stop():raise sync_control.Cancelled()
            if fatal:
                # The originating auth/rate/transport bug wins over peer cancellation.
                error=next((e for e in fatal if not isinstance(e,sync_control.Cancelled)),fatal[0])
                raise error
            for row,result,error in outcomes:
                if error:
                    failed.append(str(row['appid']));warnings.append({'game':str(row.get('name') or row['appid']),'reason':str(error)})
                else:
                    g,current=result;games.append(g);items.extend(current)
                progress(len(games)+len(failed),len(rows),str(row.get('name') or row['appid']))
    if not games and owned['game_count']:raise SteamError('Steam oyunları alınamadı; önceki arşiv korundu.')
    return {'id':sid,'username':value,'provider':'steam','warnings':warnings,'failed_title_ids':failed},games,items
