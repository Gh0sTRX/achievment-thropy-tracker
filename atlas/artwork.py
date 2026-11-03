"""Permissioned local artwork cache.

SteamGridDB requires a user API key. No game images or icons are redistributed with
this code. Never bypass anti-bot pages; do not fetch untrusted domains.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
import urllib.error
from .core import data_dir

TRUSTED_DOMAINS=(
    'steamgriddb.com','xboxlive.com','xbox.com','microsoft.com','s-microsoft.com',
    'trueachievements.com',
)
MAX_BYTES=8_000_000
AGENT='AchievementAtlas/0.5 (personal artwork cache; github-ready OSS)'

def safe_url(url:str)->bool:
    try:
        p=urllib.parse.urlparse(url)
        if p.scheme!='https' or p.username or p.password or p.port not in (None,443):return False
        host=(p.hostname or '').casefold()
        return any(host==d or host.endswith('.'+d) for d in TRUSTED_DOMAINS)
    except (TypeError,ValueError,AttributeError):return False

class GuardedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not safe_url(newurl):raise ValueError('Untrusted image redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

opener=urllib.request.build_opener(GuardedRedirects())

def fetch(url,maxsize=MAX_BYTES,headers=None):
    if not safe_url(url):raise ValueError('Image source host is not allowed')
    req=urllib.request.Request(url,headers={'User-Agent':AGENT,**(headers or {})})
    with opener.open(req,timeout=12) as res:
        if not safe_url(res.geturl()):raise ValueError('Unsafe redirect')
        data=res.read(maxsize+1)
        if len(data)>maxsize:raise ValueError('Image too large')
        return data,(res.headers.get('Content-Type') or '').split(';')[0].lower()

def suffix(data):
    if data.startswith(b'\xff\xd8\xff'):return '.jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
    if data[:4]==b'RIFF' and data[8:12]==b'WEBP':return '.webp'
    return None

def cache_image(root:Path, category:str, ident:str, url:str)->str:
    if category not in ('cover','hero','icon'):raise ValueError('Invalid image category')
    if not re.fullmatch(r'[a-zA-Z0-9:_-]{2,120}',str(ident)):raise ValueError('Invalid image ID')
    data,mime=fetch(url)
    ext=suffix(data)
    if not ext or not mime.startswith('image/'):
        raise ValueError('Image provider did not return an image')
    directory=root/'artwork';directory.mkdir(parents=True,exist_ok=True)
    clean=re.sub('[^a-zA-Z0-9_-]','_',ident)
    for old in directory.glob(category+'_'+clean+'.*'):
        if old.suffix in ('.png','.jpg','.webp'):old.unlink(missing_ok=True)
    path=directory/(category+'_'+clean+ext)
    tmp=path.with_suffix('.temp')
    tmp.write_bytes(data);os.replace(tmp,path)
    return path.name

def cached(root,category,ident):
    clean=re.sub('[^a-zA-Z0-9_-]','_',str(ident))
    for ext in ('.png','.jpg','.webp'):
        p=root/'artwork'/(category+'_'+clean+ext)
        if p.is_file() and p.stat().st_size<=MAX_BYTES:return p
    return None

def sgdb_json(path,key):
    if not key or len(key)>400:raise ValueError('SteamGridDB API key missing')
    url='https://www.steamgriddb.com/api/v2/'+path.lstrip('/')
    data,mime=fetch(url,headers={'Authorization':'Bearer '+key,'Accept':'application/json'})
    if mime!='application/json':raise ValueError('SteamGridDB did not return JSON')
    parsed=json.loads(data)
    if not parsed.get('success'):raise ValueError('Artwork provider returned an error')
    return parsed.get('data') or []

def search_game(name,key):
    name=str(name).strip()[:160]
    if not name:raise ValueError('Game title missing')
    records=sgdb_json('search/autocomplete/'+urllib.parse.quote(name,safe=''),key)
    return [{'id':int(x['id']),'name':str(x.get('name',''))[:160]} for x in records[:12] if str(x.get('id','')).isdigit()]

def candidates(sgdb_id,key):
    ident=int(sgdb_id)
    if ident<=0:raise ValueError('Invalid game ID')
    result=[]
    for category,kind in (('cover','grids'),('hero','heroes')):
        records=sgdb_json(f'{kind}/game/{ident}',key)
        for x in records[:9]:
            url=str(x.get('url') or '')
            if safe_url(url):result.append({'kind':category,'url':url,'thumb':x.get('thumb') or url,
                 'width':x.get('width'),'height':x.get('height'),'source':'SteamGridDB'})
    return result