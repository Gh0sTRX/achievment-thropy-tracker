"""Bounded media caching; cancellation preserves completed, validated files."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from .sync_control import Cancelled
from . import artwork,catalog


def game_sources(game,kind):
    """Shared eligible sources for download and health; user files stay local."""
    saved=(game.get('artwork_meta') or {}).get(kind,{})
    if saved.get('provider')=='user_file':return []
    from .cover_recovery import identity,bound_match
    candidates=[c for c in game.get('art_candidates',[]) if c.get('kind')==kind
                and (not c.get('cover_identity') or c['cover_identity']==identity(game))
                and (c.get('provider')!='SteamGridDB' or bound_match(game))]
    candidates.sort(key=lambda c:c.get('provider')=='SteamGridDB')
    sources=[]
    recorded_title=saved.get('title_id') or (saved.get('provider_id') if saved.get('provider')!='SteamGridDB' else None)
    if saved.get('game_id')==game['id'] and saved.get('platform')==game.get('platform') and saved.get('platform_edition')==game.get('platform_edition') and (recorded_title or None)==(game.get('title_id') or None):
        sources.append({**saved,'url':saved.get('source_url')})
    sources.append({'url':game.get(kind+'_url'),'provider':game.get('image_source') or game.get('platform')})
    return [c for c in sources+candidates if artwork.safe_url(c.get('url'))]


def asset_diagnosis(root,game,kind,present):
    saved=(game.get('artwork_meta') or {}).get(kind,{})
    last=(game.get('artwork_download') or {}).get(kind,{})
    sources=game_sources(game,kind);available=bool(sources);code=last.get('code')
    try:invalid_cache=any((root/'artwork'/(kind+'_'+artwork.cache_token(game['id'])+ext)).is_file() for ext in ('.png','.jpg','.webp')) and not present
    except ValueError:invalid_cache=False
    if present:state,reason,action='cached','Geçerli yerel görsel var.','Çevrimdışı kullanılabilir.'
    elif saved.get('provider')=='user_file':state,reason,action='local_file_missing','Seçtiğin yerel dosya eksik veya bozuk.','Kendi dosyanı yeniden seç; otomatik üzerine yazılmaz.'
    elif not artwork.game_art_matches(game,kind):state,reason,action='identity_mismatch','Yerel görsel farklı oyun kimliği/edisyona bağlı.','Dosya korunuyor; doğru edisyon kaynağını yeniden onayla.'
    elif invalid_cache:state,reason,action='invalid_cache','Yerel dosya var ama geçerli bir görsel olarak okunamıyor.',('Bu oyunun görsellerini yeniden indir.' if available else 'Doğru edisyon için görsel veya kendi dosyanı seç.')
    elif saved and not available and game.get(kind+'_url')=='local':state,reason,action='identity_mismatch','Saklı kaynak bu oyun kimliği/edisyonu için doğrulanamıyor.','Oyun ve edisyon eşleşmesini yeniden onayla veya kendi dosyanı seç.'
    elif code in (401,403,429):state,reason,action='blocked',f'Kaynak erişimi engellendi (HTTP {code}).',('Hız sınırı: daha sonra yeniden dene.' if code==429 else 'Erişimi kontrol et veya başka izinli kaynak/kendi dosyanı seç.')
    elif code==404:state,reason,action='failed','Kaynakta bu görsel bulunamadı (HTTP 404).','Aynı edisyon için başka görsel seç.'
    elif game.get(kind+'_url')=='local' and available:state,reason,action='missing_cache','Kayıtlı görsel dosyası yok veya decode edilemiyor; kaynak adresi var.','Bu oyunun eksik görsellerini yeniden indir.'
    elif not available:state,reason,action='missing_source','Bu kategori için kullanılabilir kaynak yok.','CSV görsel taşımaz; doğru oyun/edisyonu onaylayıp görsel veya kendi dosyanı seç.'
    elif last.get('state')=='failed':state,reason,action='failed','Görsel indirilemedi veya geçerli bir resim değildi.','Ağ erişimini kontrol et; yeniden dene veya başka izinli görsel seç.'
    else:state,reason,action='available_uncached','Kaynak adresi var; doğrulanmış yerel dosya henüz yok.','Bu oyunun eksik görsellerini indir.'
    return {'kind':kind,'state':state,'code':None if present else code,'last_state':last.get('state'),'source_available':available,'provider':saved.get('provider') or (sources[0].get('provider') if sources else '') or game.get('image_source',''),'reason':reason,'action':action}


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


def download(store, progress=lambda *a:None, stop=lambda:False, platform=None, game_id=None, covers_only=False, transfer=None):
    from datetime import datetime,timezone
    with store.lock:
        games=[deepcopy(g) for g in store.library['games'] if not catalog.is_app(g) and (not platform or g.get('platform')==platform) and (not game_id or g['id']==game_id)]
        profile_context=deepcopy(store.state.get('public_profiles',{}))
        game_objects={g['id']:g for g in store.library['games']}
        gids={g['id'] for g in games}
        icons=[] if covers_only else [dict(a) for a in store.library['achievements'] if a.get('game_id') in gids or (not platform and not game_id and a.get('game_id') not in {g['id'] for g in store.library['games']})]
    kinds=('cover',) if covers_only else ('cover','hero','banner','logo','screenshot')
    report={'downloaded':0,'cached':0,'missing_source':0,'failed':0,'blocked':0,'skipped':0,'cancelled':0,'attempted':0,'processed':0,'planned':len(games)*len(kinds)+len(icons),'records':len(games)+len(icons),'missing':[],'errors':[],'details':[],'detail_count':0,'missing_count':0,'error_count':0,'checked_at':datetime.now(timezone.utc).isoformat()}
    outcomes=transfer.setdefault('outcomes',{}) if transfer is not None else None
    forbidden_hosts=transfer.setdefault('forbidden_hosts',set()) if transfer is not None else set()
    unavailable=transfer.setdefault('unavailable',{}) if transfer is not None else {}
    blocked=threading.Event();dirty=0;last_save=time.monotonic();indexed=None;indexes={}
    def lookup(is_icon,ident):
        nonlocal indexed,indexes
        if indexed is not store.library:
            indexed=store.library;indexes={False:{x['id']:x for x in indexed['games']},True:{x['id']:x for x in indexed['achievements']}}
        return indexes[is_icon].get(ident)
    assets=[(g,kind,False) for g in games for kind in kinds]+[(a,'icon',True) for a in icons]
    def halted():return stop() or blocked.is_set()
    def record_outcome(detail, attempted=False):
        if outcomes is None:return
        key=(detail['id'],detail['kind']);previous=outcomes.get(key,{})
        # A later cache hit or cancellation must not erase this job's completed download.
        if previous.get('state')=='downloaded' and detail['state'] in ('cached','cancelled'):return
        outcomes[key]={**detail,'attempted':attempted or previous.get('attempted',False)}
    def process(asset):
        nonlocal dirty,last_save
        obj,kind,is_icon=asset
        ident=obj['id'];state='missing_source';code=None;attempted=False;meta=None
        if halted():
            with store.lock:
                report['cancelled']+=1
                record_outcome({'id':ident,'game_id':obj.get('game_id',ident),'kind':kind,'platform':obj.get('platform'),'state':'cancelled','code':None})
            return
        if (artwork.cached(store.root,kind,ident) if is_icon else artwork.game_cached(store.root,obj,kind)):state='cached'
        elif (obj.get('artwork_meta') or {}).get(kind,{}).get('provider')=='user_file':state='skipped'
        else:
            candidates=([{'url':obj.get('icon_url') or obj.get('icon_candidate'),'provider':obj.get('provider') or obj.get('platform')}] if is_icon else game_sources(obj,kind))
            candidates=[c for c in candidates if artwork.safe_url(c.get('url'))]
            seen=set()
            for candidate in candidates:
                url=candidate['url']
                if url in seen:continue
                seen.add(url)
                if halted():state='cancelled';break
                host=urlsplit(url).hostname
                with store.lock:forbidden=host in forbidden_hosts
                if forbidden:
                    state='blocked';code=403;continue
                with store.lock:prior_failure=unavailable.get(url)
                if prior_failure:
                    state,code=prior_failure;continue
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
                        if not current or any(current.get(k)!=obj.get(k) for k in ('platform','game_id','title_id','platform_edition','devices','provider')):state='skipped';break
                        if not is_icon and (current is not game_objects.get(ident) or store.state.get('public_profiles',{})!=profile_context):state='skipped';break
                        if not is_icon and (current.get('artwork_meta') or {}).get(kind,{}).get('provider')=='user_file':state='skipped';break
                        if not is_icon:meta=artwork.store_bytes(store.root,kind,ident,data)
                        provenance={**meta,'provider':candidate.get('provider') or obj.get('platform'),'provider_id':candidate.get('provider_id') or (obj.get('provider_identity') or {}).get('achievement_id') or obj.get('provider_id') or obj.get('title_id',''),'title_id':obj.get('title_id'),'source_url':url,'game_id':obj.get('game_id',ident),'platform':obj.get('platform'),'platform_edition':obj.get('platform_edition'),'saved_at':report['checked_at'],'rights_note':candidate.get('rights_note') or 'Sağlayıcı görseli; yeniden dağıtım izni verilmez.'}
                        if is_icon:current['icon_meta']=provenance;current['icon_url']=url
                        else:current[kind+'_url']='local';current.setdefault('artwork_meta',{})[kind]=provenance
                        dirty+=1;state='downloaded';code=None;break
                except Cancelled:state='cancelled';break
                except Exception as exc:
                    code=getattr(exc,'code',None);state='blocked' if code in (401,403,429) else 'failed'
                    if transfer is not None and isinstance(exc,(ValueError,URLError,TimeoutError,ConnectionError)):
                        with store.lock:unavailable[url]=(state,code)
                    if code==403:
                        # Respect this host's denial without suppressing already
                        # selected, independent sources from other providers.
                        with store.lock:forbidden_hosts.add(host)
                    elif state=='blocked':blocked.set();break
        with store.lock:
            report[state]+=1;report['attempted']+=int(attempted);report['processed']+=1
            detail={'id':ident,'game_id':obj.get('game_id',ident),'kind':kind,'state':state,'code':code,'platform':obj.get('platform')}
            record_outcome(detail,attempted)
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
            if current and all(current.get(k)==obj.get(k) for k in ('platform','game_id','title_id','platform_edition','devices','provider')) and (is_icon or current is game_objects.get(ident) and store.state.get('public_profiles',{})==profile_context) and (not is_icon or state!='missing_source'):
                value={'state':state,'code':code,'updated_at':report['checked_at']}
                if is_icon:current['icon_download']=value
                else:current.setdefault('artwork_download',{})[kind]=value
                dirty+=1
            if dirty and time.monotonic()-last_save>=5:store.save();dirty=0;last_save=time.monotonic()
        progress(report['processed'],report['planned'],obj.get('name',''))
    for asset in assets[:len(games)*len(kinds)]:process(asset)
    with ThreadPoolExecutor(max_workers=4,thread_name_prefix='atlas-media') as pool:
        for offset in range(len(games)*len(kinds),len(assets),4):
            if halted():
                report['cancelled']+=len(assets)-offset;break
            list(pool.map(process,assets[offset:offset+4]))
    if dirty:
        with store.lock:store.save()
    report['stopped']=bool(stop() or blocked.is_set())
    report['details_truncated']=report['detail_count']>len(report['details'])
    return report


def health(store,platform=None,game_id=None):
    """Coverage counts decoded local assets; candidates are a separate metric."""
    kinds=('cover','hero','banner','logo','screenshot')
    with store.lock:
        games=[dict(g) for g in store.library['games'] if not catalog.is_app(g) and (not platform or g.get('platform')==platform) and (not game_id or g['id']==game_id)]
        gids={g['id'] for g in games};items=[dict(a) for a in store.library['achievements'] if a.get('game_id') in gids]
    present={g['id']:{kind:bool(artwork.game_cached(store.root,g,kind)) for kind in kinds} for g in games}
    coverage={kind:sum(present[g['id']][kind] for g in games) for kind in kinds}
    sources={kind:sum(bool(game_sources(g,kind)) for g in games) for kind in kinds}
    icon_groups={g['id']:[] for g in games};icons=0
    for a in items:
        cached=bool(artwork.cached(store.root,'icon',a['id']));icons+=int(cached)
        icon_groups[a['game_id']].append({'cached':cached,'source':artwork.safe_url(a.get('icon_url') or a.get('icon_candidate')),'state':(a.get('icon_download') or {}).get('state'),'code':(a.get('icon_download') or {}).get('code')})
    issues=[]
    for g in games:
        missing=[kind for kind in kinds if not present[g['id']][kind]]
        icon_rows=icon_groups[g['id']];icon_cached=sum(r['cached'] for r in icon_rows);icon_missing=len(icon_rows)-icon_cached
        if not missing and not icon_missing:continue
        assets={kind:asset_diagnosis(store.root,g,kind,present[g['id']][kind]) for kind in kinds}
        icon_blocked=sum(not r['cached'] and r['state']=='blocked' for r in icon_rows);icon_failed=sum(not r['cached'] and r['state']=='failed' for r in icon_rows);icon_no_source=sum(not r['cached'] and not r['source'] for r in icon_rows)
        assets['icon']={'kind':'icon','state':'missing' if icon_missing else 'cached','missing':icon_missing,'cached':icon_cached,'total':len(icon_rows),'source_available':any(r['source'] and not r['cached'] for r in icon_rows),'blocked':icon_blocked,'failed':icon_failed,'missing_source':icon_no_source,'http_codes':sorted({r['code'] for r in icon_rows if not r['cached'] and type(r['code']) is int}),'reason':f'{len(icon_rows)} kayıtlı başarımın {icon_missing} ikon dosyası eksik; {icon_no_source} kaynaksız, {icon_blocked} engelli, {icon_failed} başarısız.','action':'Başarım kaynağında ikon varsa yeniden indir; CSV tek başına ikon içermez.' if icon_missing else 'Mevcut ikonlar çevrimdışı kullanılabilir.'}
        issues.append({'game_id':g['id'],'name':g.get('name',''),'platform':g.get('platform'),'title_id':g.get('title_id',''),'edition':g.get('platform_edition',''),'devices':g.get('devices',[]),'missing':missing+(['icon'] if icon_missing else []),'states':g.get('artwork_download',{}),'assets':assets})
    states=[v for g in games for v in g.get('artwork_download',{}).values()]+[a['icon_download'] for a in items if a.get('icon_download')]
    state_counts={key:sum(s.get('state')==key for s in states) for key in ('downloaded','cached','missing_source','failed','blocked','skipped','cancelled')}
    return {'games':len(games),'achievements':len(items),'cached':coverage,'cached_icons':icons,'valid_source_urls':sources,'icon_source_urls':sum(artwork.safe_url(a.get('icon_url') or a.get('icon_candidate')) for a in items),
            'missing':{kind:len(games)-coverage[kind] for kind in kinds},'issues':issues[:200],'issue_count':len(issues),'has_more':len(issues)>200,'missing_icons':len(items)-icons,'scope':'validated_local_cache','last_checked_states':state_counts,'checked_at':max((s.get('updated_at','') for s in states),default='')}


def cover_inventory(store, platform=None, offset=0, limit=20, state=None):
    """All-library Game Universe cover queue, never inferred by title alone.

    Reports verified *decoded* local covers; remote candidates and URLs are not
    counted as downloaded art. Results are paginated for large libraries.
    """
    try:
        offset=int(offset)
        limit=int(limit)
    except (TypeError,ValueError):
        raise ValueError('Kapak kuyruğu sayfa parametresi geçersiz.') from None
    if offset<0 or offset>1_000_000 or not 1<=limit<=50:
        raise ValueError('Kapak kuyruğu sayfa aralığı geçersiz.')
    if state not in (None,'pending','no_source','failed','available'):raise ValueError('Kapak kuyruk filtresi geçersiz.')
    if platform not in (None,'xbox','psn','pc'):
        raise ValueError('Kapak platformu geçersiz.')
    with store.lock:
        games=sorted((dict(g) for g in store.library['games']
                      if not catalog.is_app(g) and (platform is None or g.get('platform')==platform)),
                     key=lambda g:(str(g.get('name','')).casefold(),str(g.get('platform','')),str(g['id'])))
    missing=[];covered=0;available=0;unmatched=0;pending=0;failed=0
    for g in games:
        if artwork.game_cached(store.root,g,'cover'):
            covered+=1
            continue
        info=asset_diagnosis(store.root,g,'cover',False)
        from .cover_recovery import identity
        discovery=g.get('cover_discovery') or {}
        if discovery.get('identity')!=identity(g):discovery={}
        pending+=int(discovery.get('state')=='pending')
        failed+=int(info['state'] in ('blocked','failed','invalid_cache') or discovery.get('state')=='failed')
        available+=int(info['source_available'])
        unmatched+=int(info['state'] in ('missing_source','identity_mismatch'))
        missing.append({'game_id':g['id'],'name':g.get('name',''),'platform':g.get('platform',''),
                        'edition':g.get('platform_edition',''),'title_id':str(g.get('title_id') or ''),
                        'state':info['state'],'reason':info['reason'],'action':info['action'],
                        'provider':info['provider'],'source_available':info['source_available'],
                        'code':info['code'],'discovery':discovery})
    queue=[g for g in missing if state is None or (state=='pending' and g['discovery'].get('state')=='pending') or (state=='no_source' and not g['source_available'] and g['discovery'].get('state')!='pending') or (state=='failed' and (g['state'] in ('blocked','failed','invalid_cache') or g['discovery'].get('state')=='failed')) or (state=='available' and g['source_available'])]
    return {'total_games':len(games),'covered':covered,'missing':len(missing),'queue_total':len(queue),
            'with_source':available,'needs_matching':unmatched,'pending_approval':pending,'failed':failed,'offset':offset,
            'limit':limit,'has_more':offset+limit<len(queue),'items':queue[offset:offset+limit]}
