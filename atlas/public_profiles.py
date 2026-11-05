"""Read public target profiles using an operator-owned service session.

The target player supplies only an ID. Credentials never travel to the browser.
"""
import asyncio
from . import settings
import re
from datetime import datetime, timezone
from . import xbox, artwork, editions, sync_control
from .core import game_id
from . import identity


def validate(platform, username):
    if platform not in ('xbox', 'psn'):
        raise ValueError('Xbox veya PlayStation seç.')
    username = str(username).strip()
    pattern = r'[A-Za-z][A-Za-z0-9_-]{2,15}' if platform == 'psn' else r'[\w #\-]{1,32}'
    if not re.fullmatch(pattern, username):
        raise ValueError('Geçerli bir Gamertag veya Online ID gir.')
    return username


def readiness():
    return {'xbox': bool(settings.get('ATLAS_XBOX_TOKEN_FILE')) or xbox.has_tokens(),
            'psn': bool(settings.get('ATLAS_PSN_NPSSO'))}


def game(platform, title_id, name, edition, cover=''):
    return {'id': game_id(platform, title_id), 'name': name, 'platform': platform,
            'title_id': title_id, 'platform_edition': edition,
            'cover_url': cover if artwork.safe_url(cover) else '', 'hero_url': '',
            'image_source': platform, 'plan': '', 'notes': '', 'ownership': 'unknown'}


def achievement(g, remote):
    rid = str(remote['id'])
    return {'id': f"{g['platform']}:{g['title_id']}:{rid}", 'provider_id': rid,
            'game_id': g['id'], 'game_name': g['name'], 'platform': g['platform'],
            'devices':g.get('devices',[]), 'device_label':g.get('device_label','Cihaz belirtilmemiş'),
            'platform_edition':g.get('platform_edition','unknown'), 'title_id':g['title_id'],
            'name': remote['name'], 'points': remote.get('gamerscore', 0),
            'ratio': 0, 'dlc': remote.get('group', ''), 'source_url': '',
            'unlocked': bool(remote['unlocked']), 'unlock_time': remote.get('timeUnlocked', ''),
            'flag': False, 'is_secret':remote.get('is_secret') is True,
            'rarity_percent':remote.get('rarity_percent'), 'rarity_source':remote.get('rarity_source',''), 'description': remote.get('description', ''),
            'icon_url': remote.get('icon', '') if artwork.safe_url(remote.get('icon', '')) else '',
            'source': g['platform'], 'trophy_type': remote.get('trophy_type', ''),
            'progress_current': remote.get('progress_current'),
            'progress_target': remote.get('progress_target')}


async def _pages(client, url, headers, key, params=None):
    """Keep continuation values opaque; never follow URLs supplied by a response."""
    params = dict(params or {})
    records = []; seen = set()
    for _ in range(1000):
        limits = getattr(getattr(client, 'achievements', None), 'rate_limit_read', None)
        options = {'rate_limits': limits} if limits is not None else {}
        sync_control.check()
        res = await sync_control.request(client.session.get(url, headers=headers, params=params, **options))
        res.raise_for_status()
        raw = res.json()
        if not isinstance(raw, dict) or not isinstance(raw.get(key), list):
            raise ValueError('Xbox yanıtı beklenen biçimde değil.')
        records.extend(raw[key])
        token = (raw.get('pagingInfo') or {}).get('continuationToken') or raw.get('continuationToken')
        if not token:
            return records
        if token in seen:
            raise ValueError('Xbox sayfalama döngüsü; önceki kayıtlar korundu.')
        seen.add(token); params['continuationToken'] = token
    raise ValueError('Xbox sayfalama sınırı aşıldı; önceki kayıtlar korundu.')


async def _xbox(username, progress):
    path = settings.get('ATLAS_XBOX_TOKEN_FILE') or (xbox.token_path() if xbox.has_tokens() else None)
    if not path:
        raise ValueError('Xbox veri servisi kurulmamış. İşletmeci ATLAS_XBOX_TOKEN_FILE ayarlamalı; oyuncunun Microsoft hesabını bağlaması gerekmez.')
    async with xbox.authenticated_client(path) as (client, _):
        raw = xbox._dump(await client.profile.get_profile_by_gamertag(username))
        users = raw.get('profileUsers') or []
        if len(users) != 1:
            raise ValueError('Xbox profili bulunamadı.')
        profile = xbox.normalize_profile(raw, str(users[0].get('id', '')))
        xuid = profile['xuid']
        identity.verify_requested_name('xbox', username, profile['gamertag'])
        histories = []
        base = 'https://achievements.xboxlive.com'
        for version in ('1', '2'):
            titles = await _pages(client, f'{base}/users/xuid({xuid})/history/titles',
                                  {'x-xbl-contract-version': version}, 'titles')
            histories.extend((t, version) for t in titles)
        metadata = {}
        try:
            titlehub = xbox._dump(await client.titlehub.get_title_history(xuid, max_items=10000))
            metadata = {t['titleId']: t for t in xbox.parse_titles(titlehub)}
        except Exception:
            # Optional cover metadata must not replace or fabricate progression.
            pass
        games=[];items=[];warnings=[];failed=[];groups={}
        for title,version in histories:
            tid=str(title.get('titleId',''))
            if tid.isdigit():groups.setdefault(tid,[]).append((title,version))
        async def load_title(tid, variants):
            async with semaphore:
                return await load_one(tid,variants)

        async def load_one(tid,variants):
            sync_control.check()
            meta=metadata.get(tid,{})
            known=editions.xbox_devices(variants[0][0],meta,variants[0][1])
            if known and 'xbox360' not in known:
                variants.sort(key=lambda pair:pair[1]!='2')
            errors=[];loaded=False
            for title,version in variants:
                devices=editions.xbox_devices(title,meta,version)
                g=editions.apply(game('xbox',tid,str(title.get('name') or tid),'360' if version=='1' else 'one',meta.get('cover_url','')),devices)
                g['api_generation']=version
                if devices and devices!=['xbox360']:g['platform_edition']='-'.join(devices)
                g['art_candidates']=[]
                for image in meta.get('images',[]):
                    if not isinstance(image,dict):continue
                    typ=str(image.get('imageType') or image.get('imagePurpose') or image.get('type') or '').lower()
                    kind='logo' if 'logo' in typ else 'cover' if any(w in typ for w in ('box','poster','cover')) else 'hero' if any(w in typ for w in ('background','wallpaper','hero')) else 'banner' if 'banner' in typ else 'screenshot' if 'screenshot' in typ else ''
                    url=str(image.get('uri') or image.get('url') or '')
                    if kind and artwork.safe_url(url):g['art_candidates'].append({'kind':kind,'url':url,'provider':'Xbox TitleHub'})
                cached=sync_control.reuse(g,title,xuid)
                if cached is not None:
                    games.append(g);items.extend(cached);loaded=True;break
                try:
                    endpoint='titleachievements' if version=='1' else 'achievements'
                    records=await _pages(client,f'{base}/users/xuid({xuid})/{endpoint}',{'x-xbl-contract-version':version},'achievements',{'titleId':tid})
                    if version=='1':
                        # The legacy title catalogue does not contain the target player's unlocks.
                        earned=await _pages(client,f'{base}/users/xuid({xuid})/achievements',{'x-xbl-contract-version':'1'},'achievements',{'titleId':tid})
                        earned_by_id={str(a.get('id',a.get('achievementId',''))):a for a in earned}
                        merged=[]
                        for record in records:
                            rid=str(record.get('id',record.get('achievementId','')))
                            user_record=earned_by_id.get(rid)
                            merged.append({**record,'unlocked':user_record.get('unlocked',True) if user_record else False,
                                'timeUnlocked':user_record.get('timeUnlocked','') if user_record else ''})
                        records=merged
                    normalized=xbox.normalize_achievements({'achievements':records},version=='1')
                    if len(normalized)!=len(records) or any(not a['id'].strip() for a in normalized):raise ValueError('Gerçek başarım kimliği okunamadı')
                    if len({a['id'] for a in normalized})!=len(normalized):raise ValueError('Tekrarlanan başarım kimliği')
                    if not records:raise ValueError('Başarım listesi boş döndü')
                    for original,record in zip(records,normalized):
                        if version=='1':record['icon_candidate']=artwork.legacy_icon_url(tid,original.get('imageId'))
                    rows=[achievement(g,a) for a in normalized]
                    for row,remote in zip(rows,normalized):
                        if remote.get('icon_candidate'):row['icon_candidate']=remote['icon_candidate']
                    sync_control.mark(g,title)
                    games.append(g);items.extend(rows);loaded=True;break
                except sync_control.Cancelled:raise
                except Exception as exc:
                    code=getattr(getattr(exc,'response',None),'status_code',None)
                    if code in (401,403,429):raise
                    errors.append(str(exc) if type(exc) is ValueError else type(exc).__name__)
            if not loaded:
                failed.append(tid);warnings.append({'title_id':tid,'game':variants[0][0].get('name',tid),'reason':'; '.join(errors)[:180]})
            progress(len(games)+len(failed),len(groups),variants[0][0].get('name',tid))
        semaphore=asyncio.Semaphore(3)
        tasks=[asyncio.create_task(load_title(tid,variants)) for tid,variants in groups.items()]
        try:await asyncio.gather(*tasks)
        except BaseException:
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            raise
        sync_control.check()
        return {'id':xuid,'username':profile['gamertag'],'warnings':warnings,'failed_title_ids':failed},games,items


def _psn(username, progress):
    secret = settings.get('ATLAS_PSN_NPSSO')
    if not secret:
        raise ValueError('PSN veri servisi kurulmamış. İşletmeci ATLAS_PSN_NPSSO ayarlamalı; oyuncudan oturum bilgisi istenmez.')
    try:
        from psnawp_api import PSNAWP
    except ImportError:
        raise ValueError('PSN bileşeni eksik: pip install -r requirements-psn.txt') from None
    user = PSNAWP(secret).user(online_id=username)
    identity.verify_requested_name('psn', username, user.online_id)
    identity.provider_key('psn', user.account_id)
    titles = list(user.trophy_titles(limit=None))
    games = []; items = []
    for title in titles:
        sync_control.check()
        if not title.np_communication_id or not title.title_platform:
            raise ValueError('PSN oyun kimliği eksik; arşiv değiştirilmedi.')
        platform = sorted(title.title_platform, key=lambda p: p.value)[0]
        g = game('psn', title.np_communication_id, title.title_name or title.np_communication_id,
                 ','.join(sorted(p.value for p in title.title_platform)), title.title_icon_url or '')
        g=editions.apply(g,[{'PSVITA':'psvita'}.get(p.value,p.value.lower()) for p in sorted(title.title_platform,key=lambda p:p.value)])
        def count_trophies(value):
            counts=[getattr(value,k,None) for k in ('bronze','silver','gold','platinum')]
            return sum(counts) if all(type(v) is int and v>=0 for v in counts) else None
        stamp=getattr(title,'last_updated_datetime',None)
        summary={'lastUnlock':stamp.isoformat() if stamp else '',
                 'currentAchievements':count_trophies(getattr(title,'earned_trophies',None)),
                 'totalAchievements':count_trophies(getattr(title,'defined_trophies',None))}
        g['api_generation']='psn:'+str(getattr(title,'trophy_set_version',''))
        cached=sync_control.reuse(g,summary,str(user.account_id))
        if cached is not None:
            games.append(g);items.extend(cached);progress(len(games),len(titles),g['name']);continue
        trophies = user.trophies(title.np_communication_id, platform, include_progress=True,
                                 trophy_group_id='all', limit=None)
        for t in trophies:
            sync_control.check()
            if t.trophy_id is None or t.earned is None:
                raise ValueError('PSN kazanılma verisi eksik; arşiv değiştirilmedi.')
            moment = t.earned_date_time
            items.append(achievement(g, {'id': t.trophy_id, 'name': t.trophy_name or 'Gizli kupa',
                'unlocked': t.earned, 'description': t.trophy_detail or '', 'icon': t.trophy_icon_url or '',
                'timeUnlocked': moment.isoformat() if moment else '', 'group': t.trophy_group_id or '',
                'trophy_type': t.trophy_type.value if t.trophy_type else '',
                'is_secret':getattr(t,'trophy_hidden',None) is True,
                'rarity_percent':getattr(t,'trophy_earn_rate',None),
                'rarity_source':'PSN API' if getattr(t,'trophy_earn_rate',None) is not None else '',
                'progress_current': t.progress, 'progress_target': t.trophy_progress_target_value}))
        sync_control.mark(g,summary)
        games.append(g); progress(len(games), len(titles), g['name'])
    return {'id': str(user.account_id), 'username': user.online_id}, games, items


def fetch(platform, username, progress=lambda *args: None, stop=lambda:False, cache=None, force=False):
    username = validate(platform, username)
    token=sync_control.context.set({'stop':stop,'cache':cache,'force':force})
    try:
        sync_control.check()
        identity, games, items = asyncio.run(_xbox(username, progress)) if platform == 'xbox' else _psn(username, progress)
    except (ValueError, xbox.DirectError, sync_control.Cancelled):
        raise
    except Exception as exc:
        # SDK exceptions can contain request headers or tokens; expose only the class.
        raise ValueError('Profil alınamadı: '+type(exc).__name__+'. Gizlilik, servis oturumu, ağ erişimi ve hız limitini kontrol et.') from None
    finally:sync_control.context.reset(token)
    if stop():raise sync_control.Cancelled()
    if not games or not items:
        details = '; '.join(w['game']+': '+w['reason'] for w in identity.get('warnings', [])[:2])
        raise ValueError('Oyun veya başarım alınamadı. '+(details or 'Gizlilik ve servis erişimini kontrol et.')+' Önceki arşiv korundu.')
    if len({a['id'] for a in items}) != len(items):
        raise ValueError('Tekrarlanan kupa kimliği; arşiv değiştirilmedi.')
    result = {'platform': platform, **identity, 'games': games, 'achievements': items,
              'synced_at': datetime.now(timezone.utc).isoformat()}
    from . import identity as identity_rules
    identity_rules.validate_snapshot(result)
    return result
