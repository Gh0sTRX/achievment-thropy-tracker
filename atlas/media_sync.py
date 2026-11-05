"""Bounded media caching; cancellation preserves completed, validated files."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from urllib.error import URLError
from .sync_control import Cancelled
from . import artwork


def media_request(call,halted):
    """Retry transient transports only; cancellation/rate limits stop new requests."""
    for attempt in range(3):
        if halted():raise Cancelled()
        try:return call()
        except Exception as exc:
            code=getattr(exc,'code',None)
            transient=code in (408,500,502,503,504) or code is None and isinstance(exc,(URLError,TimeoutError,ConnectionError))
            if not transient or attempt==2:raise
            deadline=time.monotonic()+.25*(2**attempt)
            while time.monotonic()<deadline:
                if halted():raise Cancelled()
                time.sleep(.05)


def download(store, progress=lambda *a:None, stop=lambda:False):
    with store.lock:
        games=[dict(g) for g in store.library['games']]
        icons=[dict(a) for a in store.library['achievements'] if a.get('icon_url') or a.get('icon_candidate')]
    results={'downloaded':0,'missing':[],'errors':[]};blocked=threading.Event()
    total=len(games)+len(icons);dirty=0;indexed=None;game_index={};item_index={}
    def halted():return stop() or blocked.is_set()
    def lookup(kind,ident):
        nonlocal indexed,game_index,item_index
        if indexed is not store.library:
            indexed=store.library;game_index={g['id']:g for g in indexed['games']};item_index={a['id']:a for a in indexed['achievements']}
        return (game_index if kind=='game' else item_index).get(ident)
    def changed():
        nonlocal dirty
        dirty+=1
        if dirty>=16:store.save();dirty=0
    def record_state(g,kind,state,reason=''):
        nonlocal dirty
        from datetime import datetime,timezone
        with store.lock:
            current=lookup('game',g['id'])
            if not current or any(current.get(k)!=g.get(k) for k in ('platform','title_id','platform_edition')):return
            previous=current.setdefault('artwork_download',{}).get(kind,{})
            if previous.get('state')==state and previous.get('reason','')==reason:return
            current['artwork_download'][kind]={'state':state,'reason':reason,'updated_at':datetime.now(timezone.utc).isoformat()}
            dirty+=1
    try:
        for index,g in enumerate(games):
            if halted():break
            candidates=list(g.get('art_candidates',[]))
            for kind in ('cover','hero','banner','logo','screenshot'):
                value=g.get(kind+'_url','')
                if value and value!='local':candidates.insert(0,{'kind':kind,'url':value,'provider':g.get('image_source') or g.get('platform')})
            for kind in ('cover','hero','banner','logo','screenshot'):
                if halted():break
                if g.get(kind+'_url')=='local' and artwork.cached(store.root,kind,g['id']):
                    record_state(g,kind,'cached');continue
                if (g.get('artwork_meta') or{}).get(kind,{}).get('provider')=='user_file':
                    record_state(g,kind,'missing_user_file','Yerel görseli yeniden seç. Otomatik kaynak üzerine yazılmaz.')
                    results['missing'].append({'game_id':g['id'],'kind':kind});continue
                found=False
                for c in candidates:
                    if halted():break
                    if c.get('kind')!=kind or not artwork.safe_url(c.get('url','')):continue
                    try:
                        data,mime=media_request(lambda:artwork.fetch(c['url']),halted)
                        if not mime.startswith('image/'):raise ValueError('Görsel yanıtı değil')
                        with store.lock:
                            current=lookup('game',g['id'])
                            if not current or any(current.get(k)!=g.get(k) for k in ('platform','title_id','platform_edition')):break
                            previous=(current.get('artwork_meta') or {}).get(kind,{})
                            if previous.get('provider')=='user_file':found=True;break
                            meta=artwork.store_bytes(store.root,kind,g['id'],data)
                            from datetime import datetime,timezone
                            current[kind+'_url']='local'
                            current.setdefault('artwork_meta',{})[kind]={**meta,'provider':c.get('provider','official'),
                                'provider_id':c.get('provider_id') or g.get('title_id',''),'game_id':g['id'],'platform':g.get('platform'),'platform_edition':g.get('platform_edition'),'source_url':c['url'],'original_url':c['url'],
                                'rights_note':c.get('rights_note') or 'Sağlayıcının sunduğu oyun görseli.', 'saved_at':datetime.now(timezone.utc).isoformat()}
                            changed()
                        results['downloaded']+=1;found=True;record_state(g,kind,'downloaded');break
                    except Exception as exc:
                        code=getattr(exc,'code',None)
                        if code in (401,403,429):record_state(g,kind,'blocked',str(code));results['errors'].append(f'{g["name"]}: medya servisi {code}');blocked.set();break
                if not found and not halted():
                    record_state(g,kind,'missing','Güvenilir aday yok veya görsel alınamadı.')
                    results['missing'].append({'game_id':g['id'],'kind':kind})
            progress(index+1,total,g['name'])
        def icon(a):
            if halted():return a,'stopped',None
            if artwork.cached(store.root,'icon',a['id']):return a,'cached',None
            url=a.get('icon_url') or a.get('icon_candidate')
            try:
                media_request(lambda:artwork.cache_image(store.root,'icon',a['id'],url),halted)
                return a,'downloaded',url
            except Exception as exc:
                code=getattr(exc,'code',None)
                if code in (401,403,429):blocked.set();return a,'blocked',code
                return a,'missing',None
        # Small chunks avoid enqueuing an entire large library after stop/rate-limit.
        with ThreadPoolExecutor(max_workers=4,thread_name_prefix='atlas-media') as pool:
            for offset in range(0,len(icons),16):
                if halted():break
                for a,state,value in pool.map(icon,icons[offset:offset+16]):
                    if state=='downloaded':
                        with store.lock:
                            current=lookup('item',a['id'])
                            if current and (current.get('icon_url') or current.get('icon_candidate'))==value:
                                current['icon_url']=value;changed()
                        results['downloaded']+=1
                    elif state=='blocked':results['errors'].append(f'İkon servisi {value}')
                    elif state=='missing':results['missing'].append({'achievement_id':a['id'],'kind':'icon'})
                    progress(len(games)+offset+icons[offset:offset+16].index(a)+1,total,a['name'])
        if not halted():progress(total,total,'Görsel kontrolü tamamlandı')
    finally:
        if dirty:
            with store.lock:store.save()
    return results


def health(store):
    """Coverage reflects validated local bytes, never merely a candidate URL."""
    kinds=('cover','hero','banner','logo','screenshot')
    with store.lock:
        games=[dict(g) for g in store.library['games']]
        items=[dict(a) for a in store.library['achievements']]
    present={g['id']:{kind:bool(artwork.cached(store.root,kind,g['id'])) for kind in kinds} for g in games}
    coverage={kind:sum(present[g['id']][kind] for g in games) for kind in kinds}
    issues=[{'game_id':g['id'],'name':g.get('name',''),'platform':g.get('platform'),'devices':g.get('devices',[]),'missing':[kind for kind in kinds if not present[g['id']][kind]],'states':g.get('artwork_download',{})} for g in games if not all(present[g['id']].values())]
    icons=sum(bool(artwork.cached(store.root,'icon',a['id'])) for a in items)
    return {'games':len(games),'achievements':len(items),'cached':coverage,'cached_icons':icons,
            'missing':{kind:len(games)-coverage[kind] for kind in kinds},
            'issues':issues[:200],'issue_count':len(issues),'has_more':len(issues)>200,'missing_icons':len(items)-icons,'scope':'validated_local_cache'}
