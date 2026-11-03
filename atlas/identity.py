"""Provider-scoped identity safety. Public display names are never account keys."""
from __future__ import annotations
import re
import unicodedata


def display_key(value):
    """Keep Xbox suffix '#' meaningful; fold casing/Unicode and whitespace only."""
    if not isinstance(value, str):
        return ''
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def provider_key(platform, account_id):
    """Stable IDs may come from either provider; do not infer from a username."""
    if platform not in ('xbox', 'psn'):
        raise ValueError('Bilinmeyen hesap platformu.')
    ident = str(account_id).strip() if account_id is not None else ''
    if not ident or len(ident) > 128 or not re.fullmatch(r'[a-zA-Z0-9:_-]+', ident):
        raise ValueError('Hesap sağlayıcısı geçerli kalıcı kimlik döndürmedi.')
    return platform, ident


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError('Servis profili geçersiz.')
    platform, ident = provider_key(snapshot.get('platform'), snapshot.get('id'))
    if not display_key(snapshot.get('username')):
        raise ValueError('Servis profil adı boş.')
    games = snapshot.get('games')
    items = snapshot.get('achievements')
    if not isinstance(games, list) or not isinstance(items, list):
        raise ValueError('Servis oyun veya başarım listesi geçersiz.')
    by_id = {}
    for game in games:
        if not isinstance(game, dict):
            raise ValueError('Servisten gelen oyun geçersiz.')
        gid = game.get('id')
        if not isinstance(gid, str) or not gid or gid in by_id or game.get('platform') != platform:
            raise ValueError('Oyun kimliği veya platform kapsamı geçersiz.')
        by_id[gid] = game
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Servisten gelen başarım geçersiz.')
        aid, gid = item.get('id'), item.get('game_id')
        if (not isinstance(aid, str) or not aid or aid in seen or gid not in by_id
                or item.get('platform') != platform):
            raise ValueError('Başarım kimliği veya oyun/platform bağı geçersiz.')
        seen.add(aid)
    return platform, ident


def reject_name_reuse(previous, incoming):
    """Same visible name resolving to another stable account is not a safe overwrite."""
    if not isinstance(previous, dict) or not previous.get('id'):
        return
    if (str(previous.get('id')) != str(incoming.get('id'))
            and display_key(previous.get('username'))
            and display_key(previous.get('username')) == display_key(incoming.get('username'))):
        raise ValueError('Aynı oyuncu adı farklı bir hesap kimliğine çözümlendi. '
                         'Önceki kayıt korunuyor; hesap eşleştirmesini doğrula.')


def verify_requested_name(platform, requested, resolved):
    provider_key(platform, 'valid')
    if display_key(requested) != display_key(resolved):
        raise ValueError('Servisin döndürdüğü oyuncu adı istenen profille uyuşmuyor. '
                         'Kayıtlar değiştirilmedi; oyuncu kimliğini doğrula.')
