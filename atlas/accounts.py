"""Provider preflight is independent of achievement sync and optional paid guides."""
import asyncio
from datetime import datetime,timezone
from . import settings,public_profiles,xbox,steam
FIELDS={'psn':'ATLAS_PSN_NPSSO','pc':'ATLAS_STEAM_API_KEY'}
LABELS={'xbox':'Xbox','psn':'PlayStation','pc':'Steam'}

def snapshot(store):
    ready=public_profiles.readiness();states=store.state.get('provider_access',{})
    return {p:{**states.get(p,{}),'state':states.get(p,{}).get('state','configured') if ready.get(p) else 'not_configured','configured':bool(ready.get(p))} for p in LABELS}

def probe(platform,username):
    if platform=='pc':
        value=steam.validate(username);sid=value
        if not value.isdigit():
            response=steam.request('ISteamUser','ResolveVanityURL',vanityurl=value).get('response',{})
            sid=str(response.get('steamid',''))
            if response.get('success')!=1:raise ValueError('Steam kullanıcı adresi bulunamadı.')
        steam.validate(sid)
        owned=steam.request('IPlayerService','GetOwnedGames',steamid=sid,include_appinfo=0).get('response',{})
        if type(owned.get('game_count')) is not int:raise ValueError('Steam oyun ayrıntıları gizli. Profil ve oyun ayrıntılarını herkese açık yap.')
        return {'id':sid,'username':value}
    if platform=='psn':
        from psnawp_api import PSNAWP
        user=PSNAWP(settings.get('ATLAS_PSN_NPSSO')).user(online_id=username)
        # Read one group to check target trophy visibility, never download the library here.
        next(iter(user.trophy_titles(limit=1)),None)
        return {'id':str(user.account_id),'username':user.online_id}
    info=asyncio.run(xbox.account_info())
    return {'service_account_id':str(info['xuid']),'username':username}

def failure(exc):
    code=getattr(exc,'code',None) or getattr(getattr(exc,'response',None),'status_code',None)
    name=type(exc).__name__.lower()
    if code==429:return 'rate_limited','İstek sınırına ulaşıldı. Daha sonra yeniden dene.'
    if code in (401,403) or any(k in name for k in ('unauthorized','authentication','forbidden')):return 'expired','Erişim reddedildi veya oturum süresi doldu. Oturumu/anahtarı ve profil gizliliğini kontrol et.'
    if isinstance(exc,ValueError) and 'gizli' in str(exc):return 'private','Profil/oyun ayrıntıları gizli. Görünürlüğü kontrol et.'
    return 'failed','Bağlantı doğrulanamadı. Kullanıcı adını, ağ erişimini ve servis oturumunu kontrol edip yeniden dene.'

def remember(store,platform,state,**values):
    with store.lock:
        value={'state':state,'checked_at':datetime.now(timezone.utc).isoformat(),**values}
        store.state.setdefault('provider_access',{})[platform]=value;store.save()
        return value
