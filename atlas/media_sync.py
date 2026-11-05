"""Bounded media caching; cancellation preserves completed, validated files."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from urllib.error import URLError
from .sync_control import Cancelled
from . import artwork,catalog


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


def download(store, progress=lambda *a:None, stop=lambda:False, platform=None, game_id=None):
    from datetime import datetime,timezone
    with store.lock:
        games=[dict(g) for g in store.library['games'] if not catalog.is_app(g) and (not platform or g.get('platform')==platform) and (not game_id or g['id']==game_id)]
        gids={g['id'] for g in games}
        icons=[dict(a) for a in store.library['achievements'] if a.get('game_id') in gids or (not platform and not game_id and a.get('game_id') not in {g['id'] for g in store.library['games']})]
    kinds=('cover','hero','banner','logo','screenshot')
    report={'downloaded':0,'cached':0,'missing_source':0,'failed':0,'blocked':0,'skipped':0,'cancelled':0,'attempted':0,'processed':0,'planned':len(games)*5+len(icons),'records':len(games)+len(icons),'missing':[],'errors':[],'details':[],'detail_count':0,'missing_count':0,'error_count':0,'checked_at':datetime.now(timezone.utc).isoformat()}
    blocked=threading.Event();dirty=0;last_save=time.monotonic();indexed=None;indexes={}
    def lookup(is_icon,ident):
        nonlocal indexed,indexes
        if indexed is not store.library:
            indexed=store.library;indexes={False:{x['id']:x for x in indexed['games']},True:{x['id']:x for x in indexed['achievements']}}
        return indexes[is_icon].get(ident)
    assets=[(g,kind,False) for g in games for kind in kinds]+[(a,'icon',True) for a in icons]
    def halted():return stop() or blocked.is_set()
    def process(asset):
        nonlocal dirty,last_save
        obj,kind,is_icon=asset
        ident=obj['id'];state='missing_source';code=None;attempted=False;meta=None
        if halted():
            with store.lock:report['cancelled']+=1
            return
        if artwork.cached(store.root,kind,ident):state='cached'
        elif (obj.get('artwork_meta') or {}).get(kind,{}).get('provider')=='user_file':state='skipped'
        else:
            candidates=([{'url':obj.get('icon_url') or obj.get('icon_candidate'),'provider':obj.get('provider') or obj.get('platform')}] if is_icon else
                [c for c in obj.get('art_candidates',[]) if c.get('kind')==kind]+[{'url':obj.get(kind+'_url'),'provider':obj.get('image_source') or obj.get('platform')}])
            candidates=[c for c in candidates if artwork.safe_url(c.get('url'))]
            seen=set()
            for candidate in candidates:
                url=candidate['url']
                if url in seen:continue
                seen.add(url)
                if halted():state='cancelled';break
                attempted=True
                try:
                    if is_icon:
                        meta=media_request(lambda:artwork.cache_image(store.root,kind,ident,url),halted) or {}
                    else:
                        data,mime=media_request(lambda:artwork.fetch(url),halted)
                        if not mime.startswith('image/'):raise ValueError('Invalid image response')
                    # Identity and user override are rechecked after the network request.
                    with store.lock:
                        current=lookup(is_icon,ident)
                        if not current or any(current.get(k)!=obj.get(k) for k in ('platform','game_id','title_id','platform_edition')):state='skipped';break
                        if not is_icon and (current.get('artwork_meta') or {}).get(kind,{}).get('provider')=='user_file':state='skipped';break
                        if not is_icon:meta=artwork.store_bytes(store.root,kind,ident,data)
                        provenance={**meta,'provider':candidate.get('provider') or obj.get('platform'),'provider_id':candidate.get('provider_id') or obj.get('provider_id') or obj.get('title_id',''),'source_url':url,'game_id':obj.get('game_id',ident),'platform':obj.get('platform'),'platform_edition':obj.get('platform_edition'),'saved_at':report['checked_at'],'rights_note':candidate.get('rights_note') or 'Sağlayıcı görseli; yeniden dağıtım izni verilmez.'}
                        if is_icon:current['icon_meta']=provenance;current['icon_url']=url
                        else:current[kind+'_url']='local';current.setdefault('artwork_meta',{})[kind]=provenance
                        dirty+=1;state='downloaded';break
                except Cancelled:state='cancelled';break
                except Exception as exc:
                    code=getattr(exc,'code',None);state='blocked' if code in (401,403,429) else 'failed'
                    if state=='blocked':blocked.set();break
        with store.lock:
            report[state]+=1;report['attempted']+=int(attempted);report['processed']+=1
            detail={'id':ident,'game_id':obj.get('game_id',ident),'kind':kind,'state':state,'code':code,'platform':obj.get('platform')}
            # Never include provider exception text or credential-bearing request URLs.
            if state in ('failed','blocked'):
                report['error_count']+=1
                if len(report['errors'])<200:report['errors'].append(f'{kind}: HTTP {code}' if code else f'{kind}: invalid image or transport')
            if state=='missing_source':
                report['missing_count']+=1
                if len(report['missing'])<200:report['missing'].append(detail)
            if state not in ('cached','downloaded'):
                report['detail_count']+=1
                if len(report['details'])<200:report['details'].append(detail)
        with store.lock:
            current=lookup(is_icon,ident)
            if current and (not is_icon or state!='missing_source'):
                value={'state':state,'code':code,'updated_at':report['checked_at']}
                if is_icon:current['icon_download']=value
                else:current.setdefault('artwork_download',{})[kind]=value
                dirty+=1
            if dirty and time.monotonic()-last_save>=5:store.save();dirty=0;last_save=time.monotonic()
        progress(report['processed'],report['planned'],obj.get('name',''))
    for asset in assets[:len(games)*5]:process(asset)
    with ThreadPoolExecutor(max_workers=4,thread_name_prefix='atlas-media') as pool:
        for offset in range(len(games)*5,len(assets),4):
            if halted():
                report['cancelled']+=len(assets)-offset;break
            list(pool.map(process,assets[offset:offset+4]))
    if dirty:
        with store.lock:store.save()
    report['stopped']=bool(stop() or blocked.is_set())
    report['details_truncated']=report['detail_count']>len(report['details'])
    return report


def health(store,platform=None):
    """Coverage counts decoded local assets; candidates are a separate metric."""
    kinds=('cover','hero','banner','logo','screenshot')
    with store.lock:
        games=[dict(g) for g in store.library['games'] if not platform or g.get('platform')==platform]
        gids={g['id'] for g in games};items=[dict(a) for a in store.library['achievements'] if a.get('game_id') in gids]
    present={g['id']:{kind:bool(artwork.cached(store.root,kind,g['id'])) for kind in kinds} for g in games}
    coverage={kind:sum(present[g['id']][kind] for g in games) for kind in kinds}
    sources={kind:sum(bool(artwork.safe_url(g.get(kind+'_url')) or artwork.safe_url((g.get('artwork_meta') or {}).get(kind,{}).get('source_url')) or any(c.get('kind')==kind and artwork.safe_url(c.get('url')) for c in g.get('art_candidates',[]))) for g in games) for kind in kinds}
    issues=[{'game_id':g['id'],'name':g.get('name',''),'platform':g.get('platform'),'devices':g.get('devices',[]),'missing':[kind for kind in kinds if not present[g['id']][kind]],'states':g.get('artwork_download',{})} for g in games if not all(present[g['id']].values())]
    icons=sum(bool(artwork.cached(store.root,'icon',a['id'])) for a in items)
    states=[v for g in games for v in g.get('artwork_download',{}).values()]+[a['icon_download'] for a in items if a.get('icon_download')]
    state_counts={key:sum(s.get('state')==key for s in states) for key in ('downloaded','cached','missing_source','failed','blocked','skipped','cancelled')}
    return {'games':len(games),'achievements':len(items),'cached':coverage,'cached_icons':icons,'valid_source_urls':sources,'icon_source_urls':sum(artwork.safe_url(a.get('icon_url') or a.get('icon_candidate')) for a in items),
            'missing':{kind:len(games)-coverage[kind] for kind in kinds},'issues':issues[:200],'issue_count':len(issues),'has_more':len(issues)>200,'missing_icons':len(items)-icons,'scope':'validated_local_cache','last_checked_states':state_counts,'checked_at':max((s.get('updated_at','') for s in states),default='')}
