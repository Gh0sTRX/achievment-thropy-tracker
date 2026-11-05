"""Explicit, title-bound metadata enrichment; proposed names are never identity proof."""
from copy import deepcopy
from . import artwork
from .dates import normalize_unlock
from .core import normalize

def proposals(game,items,remote):
    result=[]
    for a in items:
        matches=[r for r in remote if normalize(r.get('name'))==normalize(a.get('name')) and int(r.get('gamerscore') or 0)==int(a.get('points') or 0) and r.get('id')]
        if len(matches)==1 and sum(normalize(x.get('name'))==normalize(a.get('name')) and x.get('points')==a.get('points') for x in items)==1:
            result.append({'local_id':a['id'],'remote':deepcopy(matches[0])})
    return result

def apply(store,batch,selected):
    with store.lock:
        if batch.get('library_token') and batch['library_token']!=store.content_token():raise ValueError('Arşiv/profil değişti; eşleşmeleri yeniden sorgula.')
        game=next((g for g in store.library['games'] if g['id']==batch['game']['id']),None)
        if not game or any(game.get(k)!=batch['game'].get(k) for k in ('platform','title_id','platform_edition','devices')):raise ValueError('Oyun/edisyon kimliği değişti; yeniden sorgula.')
        items={a['id']:a for a in store.library['achievements'] if a['game_id']==game['id']};count=0
        for pair in batch['pairs']:
            if pair['local_id'] not in selected:continue
            a=items.get(pair['local_id']);r=pair['remote']
            if not a:continue
            identity={'provider':'xbox','title_id':game['title_id'],'achievement_id':str(r['id'])}
            if a.get('provider_identity') and a['provider_identity']!=identity:raise ValueError('Başarım kimliği çakışıyor; arşiv değiştirilmedi.')
        for pair in batch['pairs']:
            if pair['local_id'] not in selected or pair['local_id'] not in items:continue
            a=items[pair['local_id']];r=pair['remote']
            a['provider_identity']={'provider':'xbox','title_id':game['title_id'],'achievement_id':str(r['id'])}
            if r.get('description'):a['description']=str(r['description'])[:2000]
            if artwork.safe_url(r.get('icon')):a['icon_url']=r['icon']
            if a.get('unlocked') and not a.get('unlock_time') and r.get('unlocked'):
                a['unlock_time']=normalize_unlock(r.get('timeUnlocked'));a.setdefault('unlock_time_raw',str(r.get('timeUnlocked') or '')[:120])
            a['metadata_source']='Xbox API · kullanıcı onaylı eşleşme';count+=1
        store.save()
        return {'message':f'{count} başarımın sağlayıcı metadata bilgisi güncellendi. Kazanımlar, notlar ve hedefler korundu.','updated':count}
