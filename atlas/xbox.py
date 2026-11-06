"""Optional Microsoft/Xbox Live sign-in adapter using OpenXbox/xbox-webapi-python.

MIT-licensed upstream: https://github.com/OpenXbox/xbox-webapi-python
OAuth and API methods are provided by the installed package; we do not
reimplement XSTS, copy client credentials or request Microsoft passwords.

Important: these are *unofficially accessed* Xbox service endpoints. Availability
is subject to Microsoft's current permissions and rate limits.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import threading
from pathlib import Path
from typing import Any


def _sdk():
    try:
        from xbox.webapi.api.client import XboxLiveClient
        from xbox.webapi.authentication.manager import AuthenticationManager
        from xbox.webapi.authentication.models import OAuth2TokenResponse
        from xbox.webapi.common.signed_session import SignedSession
        from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, TOKENS_FILE
        return XboxLiveClient, AuthenticationManager, OAuth2TokenResponse, SignedSession, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, Path(TOKENS_FILE)
    except (ImportError, ModuleNotFoundError) as exc:
        raise DirectError('OpenXbox bileşeni kurulu değil. pip install -r requirements-xbox.txt komutunu çalıştır.') from exc


class DirectError(Exception):
    pass


def token_path():
    try:
        return _sdk()[-1]
    except DirectError:
        return None


def has_tokens():
    p = token_path()
    return bool(p and p.is_file() and p.stat().st_size > 20)


def _dump(value):
    if hasattr(value, 'model_dump'):
        try: return value.model_dump(mode='json', by_alias=True)
        except TypeError: return value.model_dump(by_alias=True)
    if hasattr(value, 'dict'): return value.dict(by_alias=True)
    if isinstance(value, dict): return value
    if isinstance(value, list): return [_dump(x) for x in value]
    raise DirectError('Xbox SDK yanıtı okunamadı.')


def _list(data, key):
    raw = data.get(key, [])
    return raw if isinstance(raw, list) else []


def _as_dict(x): return x if isinstance(x, dict) else _dump(x)


def normalize_profile(raw: dict, xuid: str) -> dict:
    """Xbox profile/settings response -> strict identity for account matching."""
    if not isinstance(raw, dict): raise DirectError('Xbox profil yanıtı beklenen biçimde değil.')
    users = raw.get('profileUsers', [])
    user = users[0] if isinstance(users, list) and users else raw
    if not isinstance(user, dict): raise DirectError('Xbox profil kaydı bulunamadı.')
    settings = user.get('settings') or []
    values = {str(s.get('id','')).casefold(): str(s.get('value','')) for s in settings if isinstance(s, dict)}
    gamertag = values.get('gamertag') or values.get('uniquemoderngamertag') or user.get('gamertag') or ''
    gs = values.get('gamerscore') or user.get('gamerscore') or '0'
    if not gamertag or not str(xuid).isdigit():
        raise DirectError('Xbox Gamertag veya XUID okunamadı; hesap doğrulanamadı.')
    return {'gamertag':str(gamertag), 'xuid':str(xuid), 'gamerscore':int(gs) if str(gs).isdigit() else 0, 'source':'OpenXbox'}


def parse_titles(titlehub: dict, recent360: dict|None=None, recent_one: dict|None=None) -> list[dict]:
    """Preserve title/platform/SCID identity; avoid inferring editions from name alone."""
    found = {}
    for obj in _list(titlehub, 'titles'):
        if not isinstance(obj, dict): continue
        tid = str(obj.get('titleId') or obj.get('title_id') or '')
        name = str(obj.get('name') or '').strip()
        if not tid.isdigit() or not name: continue
        devices = obj.get('devices') or []
        platforms = [str(d) for d in devices]
        plat = '360' if any('360' in d for d in platforms) else 'one' if platforms else 'unknown'
        found[(tid,plat)] = {'titleId':tid,'name':name,'platform':plat,'devices':platforms,'scid':obj.get('serviceConfigId') or '', 'source':'TitleHub','cover_url':str(obj.get('displayImage') or ''),'images':obj.get('images') or [], 'devices':platforms}
    for raw,plat in ((recent360,'360'),(recent_one,'one')):
        if not isinstance(raw,dict):continue
        for obj in _list(raw,'titles'):
            if not isinstance(obj,dict):continue
            tid=str(obj.get('titleId') or '')
            name=str(obj.get('name') or '').strip()
            if not tid.isdigit() or not name:continue
            found.setdefault((tid,plat),{'titleId':tid,'name':name,'platform':plat,'devices':[], 'scid':obj.get('serviceConfigId') or '', 'source':'AchievementHistory'})
    return list(found.values())


def _score_one(obj):
    for r in obj.get('rewards') or []:
        if str(r.get('type','')).casefold() == 'gamerscore':
            try:return int(r.get('value') or 0)
            except (ValueError,TypeError):continue
    try:return int(obj.get('gamerscore') or 0)
    except (ValueError,TypeError):return 0


def normalize_achievements(raw: dict, xbox360=False):
    result=[]
    for a in _list(raw,'achievements'):
        if not isinstance(a,dict):continue
        ident = next((a[k] for k in ('id','achievementId','achievement_id') if a.get(k) is not None and str(a[k]).strip()), '')
        name=str(a.get('name') or '').strip()
        name_missing = not bool(name)
        if name_missing:name = 'Başarım #' + str(ident) + ' (adı alınamadı)'
        if xbox360:
            if type(a.get('unlocked')) is not bool:raise ValueError('Xbox kazanılma durumu eksik')
            earned=a['unlocked']
            image='' # Xbox 360 imageId is *not* a URL. Never fabricate one.
            score=int(a.get('gamerscore') or 0)
            moment=a.get('timeUnlocked') if earned else ''
        else:
            state=str(a.get('progressState','')).casefold()
            if state not in ('achieved','notstarted','inprogress'):raise ValueError('Xbox kazanılma durumu eksik')
            earned=state == 'achieved'
            imgs=a.get('mediaAssets') or []
            image=next((str(x['url']) for x in imgs if isinstance(x,dict) and x.get('url') and
                      str(x.get('type','')).casefold() in ('icon','achievementicon','tile')),'')
            if not image:image=next((str(x['url']) for x in imgs if isinstance(x,dict) and x.get('url')),'')
            score=_score_one(a)
            moment=(a.get('progression') or {}).get('timeUnlocked','') if earned else ''
        measured_current=None;measured_target=None
        if not xbox360:
            reqs=(a.get('progression') or {}).get('requirements') or []
            if len(reqs)==1 and isinstance(reqs[0],dict):
                try:
                    current=float(reqs[0].get('current'));target=float(reqs[0].get('target'))
                    if target>0 and 0<=current<=target:
                        measured_current=current;measured_target=target
                except (ValueError,TypeError):pass
        result.append({'name':name,'id':str(ident), 'name_missing':name_missing,'unlocked':earned,
                       'timeUnlocked':str(moment or ''),'icon':image,'is_secret':a.get('isSecret') is True,
                       'description':str(a.get('description') or a.get('lockedDescription') or ''),
                       'gamerscore':score,'progress_current':measured_current,'progress_target':measured_target})
    return result


_refresh_lock=threading.Lock()

@asynccontextmanager
async def _refresh_guard():
    # Controllers use separate asyncio.run loops on different HTTP threads.
    # An asyncio.Lock cannot safely serialize these callers.
    from . import sync_control
    while not _refresh_lock.acquire(blocking=False):
        sync_control.check()
        await asyncio.sleep(.05)
    try:
        sync_control.check()
        yield
    finally:_refresh_lock.release()

@asynccontextmanager
async def authenticated_client(token_file=None):
    SDK,Manager,Token,Signed,client_id,secret,redirect,default_path = _sdk()
    path = Path(token_file) if token_file else default_path
    async with Signed() as session:
        manager=Manager(session,client_id,secret,redirect)
        async with _refresh_guard():
            if not path.is_file(): raise DirectError('Microsoft oturumu bulunamadı. Önce Microsoft ile giriş yap.')
            try: token_text=path.read_text(encoding='utf-8')
            except OSError as e: raise DirectError('OpenXbox token dosyası okunamıyor.') from e
            try:
                manager.oauth=Token.model_validate_json(token_text)
                await manager.refresh_tokens()
            except Exception as e:
                raise DirectError('Microsoft Xbox oturumu yenilenemedi. Yeniden giriş yap. ('+type(e).__name__+')') from e
            if not str(manager.xsts_token.xuid).isdigit():
                raise DirectError('Xbox XUID doğrulanamadı.')
            try:
                path.parent.mkdir(parents=True,exist_ok=True)
                tmp=path.with_suffix('.pending')
                tmp.write_text(manager.oauth.model_dump_json(),encoding='utf-8')
                tmp.replace(path)
            except OSError as e: raise DirectError('Yenilenen Microsoft oturumu kaydedilemedi.') from e
        # Serialize only authentication, not subsequent title/achievement queries.
        yield SDK(manager), str(manager.xsts_token.xuid)


async def account_info():
    async with authenticated_client() as (client,xuid):
        response=await client.profile.get_profile_by_xuid(xuid)
        return normalize_profile(_dump(response), xuid)


async def account_titles():
    async with authenticated_client() as (client,xuid):
        titlehub={};recent360={};recentone={}
        errors=[]
        try: titlehub=_dump(await client.titlehub.get_title_history(xuid,max_items=250))
        except Exception as e: errors.append('TitleHub: '+type(e).__name__)
        try: recent360=_dump(await client.achievements.get_achievements_xbox360_recent_progress_and_info(xuid))
        except Exception as e: errors.append('360: '+type(e).__name__)
        try: recentone=_dump(await client.achievements.get_achievements_xboxone_recent_progress_and_info(xuid))
        except Exception as e: errors.append('One: '+type(e).__name__)
        found=parse_titles(titlehub,recent360,recentone)
        if not found and errors:raise DirectError('Oyun listesi alınamadı: '+', '.join(errors))
        return found


async def fetch_title_achievements(client,xuid,title_id: str,platform='auto'):
    """Read a title with a shared authenticated XSTS session; fallback on unknown mode."""
    order=['360','one'] if platform=='360' else ['one','360']
    failures=[]
    for p in order:
        try:
            res=(await client.achievements.get_achievements_xbox360_all(xuid,title_id)) if p=='360' else (await client.achievements.get_achievements_xboxone_gameprogress(xuid,title_id))
            parsed=normalize_achievements(_dump(res),p=='360')
            if parsed:return parsed
        except Exception as e:
            err=str(e)
            if any(code in err for code in ('429','401','403')):
                raise DirectError('Xbox servisi erişimi reddetti/limit uyguladı: '+type(e).__name__) from e
            failures.append(f'{p}: {type(e).__name__}')
    raise DirectError('Başarımlar alınamadı; '+(', '.join(failures) if failures else 'Yanıt boş.'))


async def title_achievements(title_id: str,platform: str='auto'):
    async with authenticated_client() as (client,xuid):
        return await fetch_title_achievements(client,xuid,title_id,platform)


async def authorize_and_verify(code: str, profile_expected: str, normalizer, expected_xuid: str|None=None):
    """Acquire OAuth tokens and verify target gamertag *before* persisting."""
    SDK,Manager,Token,Signed,client_id,secret,redirect,path=_sdk()
    async with Signed() as session:
        manager=Manager(session,client_id,secret,redirect)
        await manager.request_tokens(code)
        client=SDK(manager)
        xuid=str(client.xuid)
        profile=normalize_profile(_dump(await client.profile.get_profile_by_xuid(xuid)), xuid)
        if normalizer(profile['gamertag'])!=normalizer(profile_expected):
            raise DirectError(f"Microsoft hesabında '{profile['gamertag']}' bulundu; arşiv '{profile_expected}' hesabına ait. Bağlantı kaydedilmedi.")
        if expected_xuid and expected_xuid!=xuid:
            raise DirectError('Microsoft oturumunun XUID değeri önceki hesapla farklı; bağlantı kaydedilmedi.')
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix('.pending')
        tmp.write_text(manager.oauth.model_dump_json(),encoding='utf-8')
        tmp.replace(path)
        return profile
