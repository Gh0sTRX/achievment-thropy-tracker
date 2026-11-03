"""Read public target profiles using an operator-owned service session.

The target player supplies only an ID. Credentials never travel to the browser.
"""
import asyncio
import os
import re
from datetime import datetime, timezone
from . import xbox, artwork
from .core import game_id


def validate(platform, username):
    if platform not in ('xbox', 'psn'):
        raise ValueError('Xbox veya PlayStation seç.')
    username = str(username).strip()
    pattern = r'[A-Za-z][A-Za-z0-9_-]{2,15}' if platform == 'psn' else r'[\w #\-]{1,32}'
    if not re.fullmatch(pattern, username):
        raise ValueError('Geçerli bir Gamertag veya Online ID gir.')
    return username


def readiness():
    return {'xbox': bool(os.getenv('ATLAS_XBOX_TOKEN_FILE')),
            'psn': bool(os.getenv('ATLAS_PSN_NPSSO'))}


def game(platform, title_id, name, edition, cover=''):
    return {'id': game_id(platform, title_id), 'name': name, 'platform': platform,
            'title_id': title_id, 'platform_edition': edition,
            'cover_url': cover if artwork.safe_url(cover) else '', 'hero_url': '',
            'image_source': platform, 'plan': '', 'notes': '', 'ownership': 'unknown'}


def achievement(g, remote):
    rid = str(remote['id'])
    return {'id': f"{g['platform']}:{g['title_id']}:{rid}", 'provider_id': rid,
            'game_id': g['id'], 'game_name': g['name'], 'platform': g['platform'],
            'name': remote['name'], 'points': remote.get('gamerscore', 0),
            'ratio': 0, 'dlc': remote.get('group', ''), 'source_url': '',
            'unlocked': bool(remote['unlocked']), 'unlock_time': remote.get('timeUnlocked', ''),
            'flag': False, 'description': remote.get('description', ''),
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
        res = await client.session.get(url, headers=headers, params=params, **options)
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
    path = os.getenv('ATLAS_XBOX_TOKEN_FILE')
    if not path:
        raise ValueError('Xbox veri servisi kurulmamış. İşletmeci ATLAS_XBOX_TOKEN_FILE ayarlamalı; oyuncunun Microsoft hesabını bağlaması gerekmez.')
    async with xbox.authenticated_client(path) as (client, _):
        raw = xbox._dump(await client.profile.get_profile_by_gamertag(username))
        users = raw.get('profileUsers') or []
        if len(users) != 1:
            raise ValueError('Xbox profili bulunamadı.')
        profile = xbox.normalize_profile(raw, str(users[0].get('id', '')))
        xuid = profile['xuid']
        histories = []
        base = 'https://achievements.xboxlive.com'
        for version in ('1', '2'):
            titles = await _pages(client, f'{base}/users/xuid({xuid})/history/titles',
                                  {'x-xbl-contract-version': version}, 'titles')
            histories.extend((t, version) for t in titles)
        games = []; items = []; seen = set()
        for title, version in histories:
            tid = str(title.get('titleId', ''))
            if not tid.isdigit() or tid in seen:
                continue
            seen.add(tid)
            g = game('xbox', tid, str(title.get('name') or tid), '360' if version == '1' else 'one')
            endpoint = 'titleachievements' if version == '1' else 'achievements'
            records = await _pages(client, f'{base}/users/xuid({xuid})/{endpoint}',
                                   {'x-xbl-contract-version': version}, 'achievements', {'titleId': tid})
            normalized = xbox.normalize_achievements({'achievements': records}, version == '1')
            if len(normalized) != len(records) or any(not a['id'] for a in normalized):
                raise ValueError('Xbox başarım kimlikleri eksik; arşiv değiştirilmedi.')
            games.append(g); items.extend(achievement(g, a) for a in normalized)
            progress(len(games), len(seen), g['name'])
        return {'id': xuid, 'username': profile['gamertag']}, games, items


def _psn(username, progress):
    secret = os.getenv('ATLAS_PSN_NPSSO')
    if not secret:
        raise ValueError('PSN veri servisi kurulmamış. İşletmeci ATLAS_PSN_NPSSO ayarlamalı; oyuncudan oturum bilgisi istenmez.')
    try:
        from psnawp_api import PSNAWP
    except ImportError:
        raise ValueError('PSN bileşeni eksik: pip install -r requirements-psn.txt') from None
    user = PSNAWP(secret).user(online_id=username)
    titles = list(user.trophy_titles(limit=None))
    games = []; items = []
    for title in titles:
        if not title.np_communication_id or not title.title_platform:
            raise ValueError('PSN oyun kimliği eksik; arşiv değiştirilmedi.')
        platform = sorted(title.title_platform, key=lambda p: p.value)[0]
        g = game('psn', title.np_communication_id, title.title_name or title.np_communication_id,
                 ','.join(sorted(p.value for p in title.title_platform)), title.title_icon_url or '')
        trophies = user.trophies(title.np_communication_id, platform, include_progress=True,
                                 trophy_group_id='all', limit=None)
        for t in trophies:
            if t.trophy_id is None or t.earned is None:
                raise ValueError('PSN kazanılma verisi eksik; arşiv değiştirilmedi.')
            moment = t.earned_date_time
            items.append(achievement(g, {'id': t.trophy_id, 'name': t.trophy_name or 'Gizli kupa',
                'unlocked': t.earned, 'description': t.trophy_detail or '', 'icon': t.trophy_icon_url or '',
                'timeUnlocked': moment.isoformat() if moment else '', 'group': t.trophy_group_id or '',
                'trophy_type': t.trophy_type.value if t.trophy_type else '',
                'progress_current': t.progress, 'progress_target': t.trophy_progress_target_value}))
        games.append(g); progress(len(games), len(titles), g['name'])
    return {'id': str(user.account_id), 'username': user.online_id}, games, items


def fetch(platform, username, progress=lambda *args: None):
    username = validate(platform, username)
    try:
        identity, games, items = asyncio.run(_xbox(username, progress)) if platform == 'xbox' else _psn(username, progress)
    except (ValueError, xbox.DirectError):
        raise
    except Exception as exc:
        # SDK exceptions can contain request headers or tokens; expose only the class.
        raise ValueError('Profil alınamadı: '+type(exc).__name__+'. Gizlilik, servis oturumu, ağ erişimi ve hız limitini kontrol et.') from None
    if len({a['id'] for a in items}) != len(items):
        raise ValueError('Tekrarlanan kupa kimliği; arşiv değiştirilmedi.')
    return {'platform': platform, **identity, 'games': games, 'achievements': items,
            'synced_at': datetime.now(timezone.utc).isoformat()}
