"""Local operator configuration. Never return secret values to the web client."""
import base64
import ctypes
import json
import os
from pathlib import Path

FIELDS = {'ATLAS_XBOX_TOKEN_FILE', 'ATLAS_PSN_NPSSO', 'BRAVE_SEARCH_API_KEY',
          'OPENAI_API_KEY', 'ATLAS_GUIDE_MODEL', 'ATLAS_AUTO_GUIDES', 'ATLAS_STEAM_API_KEY'}
_values = {}


def get(name, default=''):
    return os.environ.get(name, _values.get(name, default))


def _dpapi(data, decrypt=False):
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    crypt.CryptProtectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_wchar_p, ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptProtectData.restype = wintypes.BOOL
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.restype = wintypes.BOOL
    if decrypt:
        ok = crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target))
    else:
        ok = crypt.CryptProtectData(ctypes.byref(source), 'Achievement Atlas', None, None, None, 1, ctypes.byref(target))
    if not ok:
        raise ValueError('Windows ayar koruması açılamadı. Aynı Windows kullanıcısıyla tekrar dene.')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        kernel.LocalFree(target.data)


def read(root):
    path = Path(root)/'settings.json'
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
        if raw.get('format') == 'windows-dpapi-v1':
            if os.name != 'nt':
                raise ValueError('Bu ayarlar Windows kullanıcı hesabıyla şifrelenmiş.')
            raw = json.loads(_dpapi(base64.b64decode(raw['data']), decrypt=True))
        return {k: str(v) for k, v in raw.items() if k in FIELDS}
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        raise ValueError('Yerel ayar dosyası okunamadı; settings.json dosyasını yedekleyip yeniden başlat.') from None


def activate(root):
    global _values
    _values = read(root)


def status():
    return {k: bool(get(k)) for k in FIELDS if k not in ('ATLAS_AUTO_GUIDES', 'ATLAS_GUIDE_MODEL')} | {
        'auto_guides': get('ATLAS_AUTO_GUIDES') == '1',
        'model': get('ATLAS_GUIDE_MODEL', 'gpt-4.1-mini'),
        'storage': 'Windows kullanıcı hesabıyla şifreli' if os.name == 'nt' else 'Yalnız bu kullanıcıya açık yerel dosya'}


def save(root, updates, clear=()):
    global _values
    if not isinstance(updates, dict) or not isinstance(clear, list):
        raise ValueError('Ayar biçimi geçersiz.')
    if set(updates) - FIELDS or set(clear) - FIELDS:
        raise ValueError('Bilinmeyen ayar alanı.')
    values = read(root)
    for key in clear:
        values.pop(key, None)
    for key, value in updates.items():
        value = str(value).strip()
        if len(value) > 4000 or '\n' in value or '\r' in value:
            raise ValueError('Ayar değeri geçersiz.')
        if value:
            values[key] = value
    token = values.get('ATLAS_XBOX_TOKEN_FILE', '')
    if token and not Path(token).is_file():
        raise ValueError('Xbox oturum dosyası bulunamadı. Dosyanın tam yolunu gir.')
    steam=values.get('ATLAS_STEAM_API_KEY','')
    if steam and (len(steam)!=32 or any(c not in '0123456789abcdefABCDEF' for c in steam)):
        raise ValueError('Steam Web API anahtarı 32 onaltılık karakter olmalı.')
    npsso = values.get('ATLAS_PSN_NPSSO', '')
    if npsso and (len(npsso) != 64 or not npsso.isalnum()):
        raise ValueError('PSN servis oturumu 64 harf/rakam olmalı.')
    if values.get('ATLAS_AUTO_GUIDES', '0') not in ('0', '1'):
        raise ValueError('Otomatik rehber tercihi geçersiz.')
    encoded = json.dumps(values).encode()
    payload = {'format': 'windows-dpapi-v1', 'data': base64.b64encode(_dpapi(encoded)).decode()} if os.name == 'nt' else values
    path = Path(root)/'settings.json'
    # Create with restrictive permissions before atomic replacement on POSIX.
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as out:
        json.dump(payload, out, ensure_ascii=False, indent=2)
    os.replace(temporary, path)
    _values = values
    return {'message': 'Ayarlar cihazına kaydedildi. Servis anahtarları tarayıcıya geri gönderilmez.', 'settings': status()}
