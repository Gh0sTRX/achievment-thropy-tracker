"""Automatic verified media caching; local user choices always win."""
from . import artwork


def download(store, progress=lambda *a:None, stop=lambda:False):
    with store.lock:
        games=[dict(g) for g in store.library['games']]
        icons=[dict(a) for a in store.library['achievements'] if a.get('icon_url') or a.get('icon_candidate')]
    results={'downloaded':0,'missing':[],'errors':[]}
    for index,g in enumerate(games):
        if stop():return results
        candidates=list(g.get('art_candidates',[]))
        for kind in ('cover','logo'):
            value=g.get(kind+'_url','')
            if value and value!='local':candidates.insert(0,{'kind':kind,'url':value,'provider':g.get('image_source') or g.get('platform')})
        for kind in ('cover','logo'):
            if g.get(kind+'_url')=='local' and artwork.cached(store.root,kind,g['id']):continue
            found=False
            for c in candidates:
                if c.get('kind')!=kind or not artwork.safe_url(c.get('url','')):continue
                try:
                    data,mime=artwork.fetch(c['url'])
                    if not mime.startswith('image/'):raise ValueError('Görsel yanıtı değil')
                    with store.lock:
                        current=next((x for x in store.library['games'] if x['id']==g['id']),None)
                        if not current:break
                        previous=(current.get('artwork_meta') or {}).get(kind,{})
                        if previous.get('provider')=='user_file':found=True;break
                        meta=artwork.store_bytes(store.root,kind,g['id'],data)
                        from datetime import datetime,timezone
                        current[kind+'_url']='local'
                        current.setdefault('artwork_meta',{})[kind]={**meta,'provider':c.get('provider','official'),
                            'provider_id':g['title_id'],'source_url':c['url'],'original_url':c['url'],
                            'rights_note':'Sağlayıcının sunduğu oyun görseli.', 'saved_at':datetime.now(timezone.utc).isoformat()}
                        store.save()
                    results['downloaded']+=1;found=True;break
                except Exception as exc:
                    code=getattr(exc,'code',None)
                    if code in (401,403,429):
                        results['errors'].append(f'{g["name"]}: medya servisi {code}');return results
            if not found:results['missing'].append({'game_id':g['id'],'kind':kind})
        progress(index+1,len(games)+len(icons),g['name'])
    for index,a in enumerate(icons):
        if stop():return results
        if artwork.cached(store.root,'icon',a['id']):continue
        url=a.get('icon_url') or a.get('icon_candidate')
        try:
            artwork.cache_image(store.root,'icon',a['id'],url)
            with store.lock:
                current=next((x for x in store.library['achievements'] if x['id']==a['id']),None)
                if current:
                    # The legacy candidate becomes visible only after real image decoding succeeds.
                    current['icon_url']=url;store.save()
            results['downloaded']+=1
        except Exception as exc:
            code=getattr(exc,'code',None)
            if code in (401,403,429):
                results['errors'].append(f'İkon servisi {code}');return results
            results['missing'].append({'achievement_id':a['id'],'kind':'icon'})
        progress(len(games)+index+1,len(games)+len(icons),a['name'])
    progress(len(games)+len(icons),len(games)+len(icons),'Görsel kontrolü tamamlandı')
    return results
