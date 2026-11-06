"""Identity-bound cover discovery. Never assigns an identifier from a game name."""
import asyncio
from contextlib import AsyncExitStack
from copy import deepcopy
import time
import re
from . import artwork, catalog, editions, settings, xbox

IDENTITY = ('id', 'platform', 'title_id', 'platform_edition', 'devices', 'provider')


def identity(game):
    return {k: deepcopy(game.get(k)) for k in IDENTITY}


def bound_match(game):
    match = game.get('artwork_match') or {}
    return (match.get('confirmed') is True and match.get('provider') == 'SteamGridDB'
            and match.get('game_id') == game['id']
            and all(match.get(k) == game.get(k) for k in ('platform', 'title_id', 'platform_edition'))
            and match.get('devices', []) == (game.get('devices') or []))


class Sources:
    """One Xbox session and one PSN catalogue per job; serial bounded requests."""
    def __init__(self, stack, profiles, stop, cache=None):
        self.stack, self.profiles, self.stop = stack, profiles, stop
        self.client = None
        self.psn = None
        cache = cache if cache is not None else {}
        self.results = cache.setdefault('official', {})
        self.denied = cache.setdefault('denied', set())

    async def official(self, game):
        platform = game.get('platform'); tid = str(game.get('title_id') or '')
        devices = set(game.get('devices') or [])
        edition = str(game.get('platform_edition') or '').lower()
        xbox_edition = edition == '-'.join(game.get('devices') or []) or (edition == '360' and devices == {'xbox360'}) or (edition == 'one' and devices == {'xboxone'})
        psn_edition = set(edition.split(',')) == devices
        if platform in self.denied:
            return [], 'Sağlayıcı bu işlemde erişimi reddetti; yeniden sorgulanmadı.'
        key = (platform, tid, tuple(sorted(devices)), game.get('platform_edition'), game.get('provider'), str(game.get('steam_appid') or ''))
        if key in self.results:
            return self.results[key]
        result = ([], 'Doğrulanabilir platform kimliği/edisyonu veya resmî kapak bulunamadı.')
        if platform == 'pc' and game.get('provider') == 'steam' and re.fullmatch(r'[1-9][0-9]{0,9}',tid) and str(game.get('steam_appid') or tid) == tid and game.get('platform_edition') == 'steam':
            result = ([{'kind': 'cover', 'provider': 'Steam', 'provider_id': tid,
                        'url': f'https://cdn.akamai.steamstatic.com/steam/apps/{tid}/library_600x900.jpg'}], '')
        elif platform == 'xbox' and re.fullmatch(r'[1-9][0-9]{0,9}',tid) and devices and xbox_edition:
            token = settings.get('ATLAS_XBOX_TOKEN_FILE')
            if not token and not xbox.has_tokens():
                result = ([], 'Xbox metadata keşfi için uygulamadan Microsoft oturumu açılmalı.')
            else:
                if self.client is None:
                    try:
                        self.client, _ = await self.stack.enter_async_context(xbox.authenticated_client(token or None))
                    except Exception:
                        self.denied.add(platform)
                        raise
                response = xbox._dump(await self.client.titlehub.get_title_info(tid))
                for title in response.get('titles', []):
                    # No names enter this identity decision, including device inference.
                    reported = set(editions.xbox_devices({'devices': title.get('devices', [])}))
                    if str(title.get('titleId')) != tid or reported != devices:
                        continue
                    candidates = artwork.xbox_title_candidates(title)
                    url = title.get('displayImage')
                    if artwork.safe_url(url):
                        candidates.insert(0, {'kind': 'cover', 'url': url, 'provider': 'Xbox TitleHub', 'provider_id': tid})
                    result = ([c for c in candidates if c.get('kind') == 'cover'], '')
                    break
        elif platform == 'psn' and tid and devices and psn_edition:
            profile = self.profiles.get('psn') or {}
            if not settings.get('ATLAS_PSN_NPSSO') or not profile.get('username') or not profile.get('id'):
                result = ([], 'PSN metadata keşfi için PSN oturumu ve doğrulanmış profil gerekli.')
            else:
                if self.psn is None:
                    from psnawp_api import PSNAWP
                    try:
                        user = PSNAWP(settings.get('ATLAS_PSN_NPSSO')).user(online_id=profile['username'])
                    except Exception:
                        self.denied.add(platform)
                        raise
                    if str(user.account_id) != str(profile['id']):
                        self.denied.add(platform)
                        raise ValueError('PSN profil kimliği değişti.')
                    found = {}
                    for title in user.trophy_titles(limit=None):
                        if self.stop():
                            break
                        ds = frozenset('psvita' if p.value == 'PSVITA' else p.value.lower() for p in title.title_platform)
                        found[(str(title.np_communication_id), ds)] = title.title_icon_url
                    self.psn = found
                url = self.psn.get((tid, frozenset(devices)))
                if artwork.safe_url(url):
                    result = ([{'kind': 'cover', 'url': url, 'provider': 'PlayStation', 'provider_id': tid}], '')
        self.results[key] = result
        return result


async def _discover(store, progress, stop, platform, game_id, cache):
    with store.lock:
        profiles = deepcopy(store.state.get('public_profiles', {}))
        games = [(g, deepcopy(g)) for g in store.library['games'] if not catalog.is_app(g)
                 and (not platform or g.get('platform') == platform) and (not game_id or g['id'] == game_id)]
        key = store.steamgriddb_key
    report = dict(scanned=0, discovered=0, pending=0, no_source=0, failed=0, skipped=0, cancelled=False)
    cache = cache if cache is not None else {}
    choices = cache.setdefault('choices', {})
    names = cache.setdefault('names', {}); sgdb_denied = cache.get('sgdb_denied',False); dirty = 0; saved_at = time.monotonic()
    async with AsyncExitStack() as stack:
        sources = Sources(stack, profiles, stop, cache)
        for index, (original, game) in enumerate(games):
            if stop():
                report['cancelled'] = True
                break
            progress(index, len(games), 'Kapak kaynağı aranıyor · ' + game.get('name', ''))
            report['scanned'] += 1
            if artwork.game_cached(store.root, game, 'cover') or (game.get('artwork_meta') or {}).get('cover', {}).get('provider') == 'user_file':
                report['skipped'] += 1
                continue
            from .media_sync import game_sources
            last = (game.get('artwork_download') or {}).get('cover') or {}
            if game_sources(game, 'cover') and last.get('state') not in ('failed', 'blocked'):
                report['skipped'] += 1
                continue
            access = [bool(key), bool(settings.get('ATLAS_XBOX_TOKEN_FILE') or xbox.has_tokens()), bool(settings.get('ATLAS_PSN_NPSSO'))]
            previous = game.get('cover_discovery') or {}
            if previous.get('identity') == identity(game) and previous.get('access') == access and previous.get('profile') == profiles.get(game.get('platform')) and not (previous.get('state')=='discovered' and last.get('state') in ('failed','blocked')) and time.time() < previous.get('retry_after', 0):
                report[previous.get('state') if previous.get('state') in ('pending', 'no_source', 'failed') else 'skipped'] += 1
                continue
            state = 'no_source'; reason = ''; candidates = []; suggestions = []
            stage = 'official'
            try:
                candidates, reason = await sources.official(game)
                candidates = [c for c in candidates if artwork.safe_url(c.get('url'))]
                if last.get('state')=='failed':
                    old_urls={c['url'] for c in game_sources(game,'cover')}
                    candidates=[c for c in candidates if c['url'] not in old_urls]
                if not candidates and key and not stop() and not sgdb_denied:
                    stage = 'sgdb'
                    if bound_match(game):
                        match_id=game['artwork_match']['provider_id']
                        if match_id not in choices:choices[match_id]=artwork.candidates(match_id,key)
                        candidates = [c for c in choices[match_id] if c.get('kind') == 'cover']
                        candidates = [{**c, 'provider': 'SteamGridDB', 'confirmed_game_id': game['id']} for c in candidates]
                    else:
                        name = str(game.get('name', '')).strip().casefold()
                        if name not in names:
                            names[name] = artwork.search_game(game.get('name', ''), key)
                        suggestions = names[name]
                candidates = [c for c in candidates if artwork.safe_url(c.get('url'))]
                if candidates:
                    state = 'discovered'; reason = 'Kimlik ve edisyonla doğrulanmış kapak kaynağı bulundu.'
                elif suggestions:
                    state = 'pending'; reason = 'İsim araması yalnız aday buldu; oyun ve edisyon onayı gerekiyor.'
                elif not key:
                    reason += ' SteamGridDB anahtarı bağlı değil; ek kaynak araması yapılamadı.'
            except Exception as exc:
                state = 'failed'; code = getattr(exc, 'code', None) or getattr(getattr(exc, 'response', None), 'status_code', None)
                # Provider text/URLs may contain credentials: never persist them.
                reason = 'Metadata kaynağına erişilemedi: ' + type(exc).__name__ + (f' (HTTP {code})' if code else '')
                if code in (401, 403, 429):
                    if stage == 'official':sources.denied.add(game.get('platform'))
                    else:
                        sgdb_denied = True;cache['sgdb_denied']=True
            if stop():
                report['cancelled'] = True
                break
            with store.lock:
                current = next((g for g in store.library['games'] if g['id'] == game['id']), None)
                if current is not original or identity(current) != identity(game) or store.state.get('public_profiles', {}) != profiles or current.get('artwork_meta') != game.get('artwork_meta') or current.get('artwork_match') != game.get('artwork_match') or current.get('cover_url') != game.get('cover_url'):
                    report['skipped'] += 1
                    continue
                safe = [c for c in candidates if artwork.safe_url(c.get('url'))]
                # Bound all new sources to this precise identity, including devices.
                existing = current.get('art_candidates', [])
                additions = [dict(c, cover_identity=identity(game)) for c in safe]
                current['art_candidates'] = existing + [c for c in additions if c not in existing]
                current['cover_discovery'] = dict(identity=identity(game), access=access, profile=profiles.get(game.get('platform')), state=state, reason=reason,
                    candidates=suggestions, checked_at=time.time(), retry_after=time.time() + (300 if state == 'failed' else 21600))
                dirty += 1
                if dirty >= 25 or time.monotonic() - saved_at >= 5:
                    store.save(); dirty = 0; saved_at = time.monotonic()
                report[state] += 1
    if dirty:
        with store.lock:store.save()
    progress(report['scanned'], len(games), 'Kapak kaynağı taraması tamamlandı.' if not stop() else 'Kaynak taraması durduruldu.')
    return report


def discover(store, progress=lambda *a: None, stop=lambda: False, platform=None, game_id=None, cache=None):
    return asyncio.run(_discover(store, progress, stop, platform, game_id, cache))



def recover(store, progress=lambda *a: None, stop=lambda: False, platform=None, game_id=None):
    """One bounded cover job: saved sources, discovery, then one fallback discovery.

    Counters describe unique game covers, not the sum of repeated phases. HTTP
    denials and exhausted URLs remain blocked throughout the entire operation.
    """
    from . import media_sync
    with store.lock:
        library=store.library
        game_list=library['games']
        profiles=deepcopy(store.state.get('public_profiles',{}))
        games=[(g,identity(g)) for g in library['games'] if not catalog.is_app(g)
               and (not platform or g.get('platform')==platform) and (not game_id or g['id']==game_id)]

    invalid_context=False
    def context_changed():
        with store.lock:
            return invalid_context or store.library is not library or store.library['games'] is not game_list or store.state.get('public_profiles',{})!=profiles

    def scope_changed():
        with store.lock:
            current={g['id']:g for g in store.library['games'] if not catalog.is_app(g)
                     and (not platform or g.get('platform')==platform) and (not game_id or g['id']==game_id)}
            return len(current)!=len(games) or any(current.get(before['id']) is not g or identity(g)!=before for g,before in games)

    def halted():
        return stop() or context_changed()

    transfer={};cache={};passes=[];discoveries=[]
    def download_phase(label):
        def update(done,total,name):progress(done,total,label+' · '+name)
        result=media_sync.download(store,update,halted,platform,game_id,covers_only=True,transfer=transfer)
        passes.append({k:result[k] for k in ('attempted','downloaded','failed','blocked','stopped')})
        return result

    report=download_phase('Kayıtlı kapak kaynakları')
    for label in ('Kapak kaynakları aranıyor','Başarısız kapaklar için ek kaynak aranıyor'):
        if report['stopped'] or halted():break
        # Stop if an in-place identity change occurred between phases too.
        if scope_changed():
            invalid_context=True
            break
        found=discover(store,lambda d,t,n:progress(d,t,label+' · '+n),halted,platform,game_id,cache)
        discoveries.append(found)
        if not found['discovered'] or halted():break
        report=download_phase('Doğrulanan kapaklar indiriliyor')
        if not report['failed']:break

    invalid_context=invalid_context or scope_changed()
    # A profile switch can change which IDs the downloader sees before its snapshot.
    # Count only this job's original scope, including unprocessed cancelled entries.
    outcomes=[transfer['outcomes'].get((before['id'],'cover'),
              dict(id=before['id'],game_id=before['id'],kind='cover',platform=before['platform'],state='cancelled',code=None,attempted=False))
              for g,before in games]
    for state in ('downloaded','cached','missing_source','failed','blocked','skipped','cancelled'):
        report[state]=sum(x['state']==state for x in outcomes)
    report['attempted']=sum(bool(x['attempted']) for x in outcomes)
    report['asset_attempts']=sum(p['attempted'] for p in passes)
    report['processed']=len(outcomes)-report['cancelled']
    report['planned']=report['records']=len(games)
    errors=[x for x in outcomes if x['state'] in ('failed','blocked')]
    missing=[x for x in outcomes if x['state']=='missing_source']
    details=[x for x in outcomes if x['state'] not in ('cached','downloaded')]
    # Keep per-job memory diagnostics bounded and free of private request URLs.
    clean=lambda rows:[{k:v for k,v in x.items() if k!='attempted'} for x in rows[:200]]
    report.update(errors=[f"cover: HTTP {x['code']}" if x['code'] else 'cover: invalid image or transport' for x in errors[:200]],
                  error_count=len(errors),missing=clean(missing),missing_count=len(missing),details=clean(details),
                  detail_count=len(details),details_truncated=len(details)>200,passes=passes,
                  context_changed=context_changed(),stopped=bool(report['stopped'] or halted()))
    report['discovery']=discoveries[0] if discoveries else None
    if len(discoveries)>1:report['fallback_discovery']=discoveries[1]
    return report
