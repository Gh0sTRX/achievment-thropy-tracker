"""Public GitHub Releases updater. Download integrity does not replace publisher trust."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
from . import __version__

REPOSITORY='Gh0sTRX/achievment-thropy-tracker'
LATEST=f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
MAX_INSTALLER=300_000_000
HOSTS={'api.github.com','github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}


def version(value):
    if not isinstance(value,str) or not re.fullmatch(r'v?\d{1,5}\.\d{1,5}\.\d{1,5}',value):
        raise ValueError('Güncelleme sürümü geçersiz.')
    return tuple(map(int,value.removeprefix('v').split('.')))


def safe_url(value):
    try:
        p=urlsplit(value)
        return p.scheme=='https' and p.hostname in HOSTS and not p.username and not p.password and p.port in (None,443)
    except (ValueError,TypeError):return False


class Redirects(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not safe_url(newurl):raise ValueError('Güncelleme indirmesi güvenilir adrese yönlenmedi.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def open_url(url):
    if not safe_url(url):raise ValueError('Güncelleme adresi geçersiz.')
    return build_opener(Redirects()).open(Request(url,headers={
        'User-Agent':'AchievementAtlas/'+__version__, 'Accept':'application/vnd.github+json' if url.startswith('https://api.github.com/') else 'application/octet-stream'}),timeout=30)


def read_json(url):
    with open_url(url) as response:
        data=response.read(512_001)
        if len(data)>512_000:raise ValueError('Güncelleme bilgisi çok büyük.')
    result=json.loads(data)
    if not isinstance(result,dict):raise ValueError('Güncelleme yanıtı geçersiz.')
    return result


def release_info(raw, current=__version__):
    if raw.get('draft') or raw.get('prerelease'):raise ValueError('Kararlı yayın bulunamadı.')
    tag=raw.get('tag_name','');number=version(tag)
    if tag!='v'+'.'.join(map(str,number)):raise ValueError('Yayın etiketi geçersiz.')
    if number<=version(current):return None
    label=tag[1:];name=f'AchievementAtlas-{label}-Windows-x64-Setup.exe'
    base=f'https://github.com/{REPOSITORY}/releases/download/{tag}/'
    assets={a.get('name'):a for a in raw.get('assets',[]) if isinstance(a,dict)}
    for filename in (name,'update-manifest.json'):
        if filename not in assets or assets[filename].get('browser_download_url')!=base+filename:
            raise ValueError('Yayın doğrulanabilir güncelleme dosyası içermiyor.')
    return {'version':label,'tag':tag,'name':name,'url':base+name,
            'manifest_url':base+'update-manifest.json',
            'notes':str(raw.get('body',''))[:6000],
            'release_url':f'https://github.com/{REPOSITORY}/releases/tag/{tag}'}


def validate_manifest(raw, release):
    if raw.get('schema')!=1 or raw.get('repository')!=REPOSITORY or raw.get('version')!=release['version']:
        raise ValueError('Güncelleme manifesti bu yayına ait değil.')
    if raw.get('installer')!=release['name'] or raw.get('signed') is not True:
        raise ValueError('Yayın imzalı kurulum dosyası içermiyor; otomatik kurulum engellendi.')
    if type(raw.get('size')) is not int or not 0<raw['size']<=MAX_INSTALLER:
        raise ValueError('Kurulum boyutu geçersiz.')
    for key in ('sha256','signer_sha256'):
        if not isinstance(raw.get(key),str) or not re.fullmatch('[a-fA-F0-9]{64}',raw[key]):
            raise ValueError('Yayın doğrulama bilgisi eksik.')
    return {**raw,'sha256':raw['sha256'].lower(),'signer_sha256':raw['signer_sha256'].lower()}


def verify_signature(path):
    if sys.platform!='win32':raise ValueError('Otomatik kurulum yalnız Windows kurulum sürümünde desteklenir.')
    # A fixed script reads an argument via environment. Paths are never interpolated into code.
    script="""$ErrorActionPreference='Stop';$s=Get-AuthenticodeSignature -LiteralPath $env:ATLAS_VERIFY_FILE;if($s.Status -ne 'Valid' -or !$s.SignerCertificate){throw 'Untrusted Authenticode signature'};$sha=[Security.Cryptography.SHA256]::Create();@{status='Valid';signer_sha256=([BitConverter]::ToString($sha.ComputeHash($s.SignerCertificate.RawData))).Replace('-','').ToLower()}|ConvertTo-Json -Compress"""
    env={**os.environ,'ATLAS_VERIFY_FILE':str(Path(path).resolve())}
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],env=env,capture_output=True,text=True,timeout=40,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise ValueError('Dosyanın güvenilir yayıncı imzası doğrulanamadı. Otomatik kurulum yapılmadı.')
    try:return json.loads(result.stdout)['signer_sha256'].lower()
    except (ValueError,KeyError):raise ValueError('Yayıncı imzası okunamadı.') from None


def stream_installer(url,path,manifest,progress=lambda *a:None):
    total=0;digest=hashlib.sha256()
    try:
        with open_url(url) as response, path.open('xb') as out:
            while True:
                chunk=response.read(128*1024)
                if not chunk:break
                total+=len(chunk)
                if total>manifest['size']:raise ValueError('İndirilen dosya beklenenden büyük.')
                out.write(chunk);digest.update(chunk);progress(total,manifest['size'])
        if total!=manifest['size'] or digest.hexdigest()!=manifest['sha256']:
            raise ValueError('Kurulum dosyasının SHA256 veya boyut kontrolü başarısız; dosya silindi.')
    except Exception:
        path.unlink(missing_ok=True)
        raise


class Updater:
    def __init__(self,root):
        self.root=Path(root);self.guard=threading.Lock();self.lock=threading.RLock()
        self.state={'state':'idle','current':__version__,'message':'GitHub güncellemeleri henüz kontrol edilmedi.'}
        self.release=None;self.manifest=None;self.ready_path=None;self.exit_requested=threading.Event()

    def snapshot(self):
        with self.lock:return dict(self.state)

    def set(self,**values):
        with self.lock:self.state.update(values)

    def check(self):
        if not self.guard.acquire(blocking=False):raise ValueError('Güncelleme işlemi zaten çalışıyor.')
        self.set(state='checking',message='GitHub üzerindeki kararlı yayın kontrol ediliyor.')
        def worker():
            try:
                release=release_info(read_json(LATEST))
                if not release:
                    self.release=None;self.set(state='current',message='Kurulu sürüm güncel.');return
                manifest=validate_manifest(read_json(release['manifest_url']),release)
                self.release=release;self.manifest=manifest
                self.set(state='available',latest=release['version'],notes=release['notes'],release_url=release['release_url'],message='Yeni sürüm hazır. İndirildikten sonra yayıncı imzası doğrulanacak.')
            except urllib.error.HTTPError as exc:
                self.set(state='no_release' if exc.code==404 else 'error',message='Henüz güncelleme kanalı için yayınlanmış kararlı sürüm yok.' if exc.code==404 else 'GitHub güncelleme servisine erişilemedi. Mevcut sürüm kullanılabilir.')
            except Exception as exc:
                self.set(state='error',message=str(exc) if type(exc) is ValueError else 'Güncelleme kontrolü tamamlanamadı. Mevcut sürüm kullanılabilir.')
            finally:self.guard.release()
        threading.Thread(target=worker,daemon=True).start()
        return {'message':'Güncelleme kontrolü başladı.'}

    def supported_install(self):
        if sys.platform!='win32' or not getattr(sys,'frozen',False):
            raise ValueError('Otomatik kurulum Windows Setup ile kurulan sürüm içindir; kaynak/taşınabilir sürümü elle güncelle.')
        install=Path(sys.executable).resolve().parent
        if self.root.resolve().is_relative_to(install):raise ValueError('Otomatik güncelleme için kütüphane kurulum klasöründen ayrı tutulmalı.')
        if not (install/'unins000.exe').is_file():raise ValueError('Bu bir taşınabilir sürüm. Otomatik kurulum için Setup sürümünü kullan.')
        return install

    def download(self):
        if not self.guard.acquire(blocking=False):raise ValueError('Güncelleme işlemi zaten çalışıyor.')
        if not self.release or not self.manifest:
            self.guard.release();raise ValueError('Önce güncellemeleri kontrol et.')
        release=dict(self.release);manifest=dict(self.manifest)
        self.set(state='downloading',downloaded=0,total=manifest['size'],message='Kurulum doğrulama için indiriliyor.')
        def worker():
            path=None
            try:
                self.supported_install()
                anchor=verify_signature(sys.executable)
                if anchor!=manifest['signer_sha256']:raise ValueError('Yeni sürüm farklı yayıncıya ait. Otomatik kurulum engellendi.')
                import tempfile
                directory=Path(tempfile.mkdtemp(prefix='release-',dir=self.update_dir()))
                path=directory/release['name']
                if shutil.disk_usage(directory).free<manifest['size']*4:raise ValueError('Güncelleme için yeterli boş alan yok.')
                stream_installer(release['url'],path,manifest,lambda done,total:self.set(downloaded=done,total=total))
                if verify_signature(path)!=anchor:raise ValueError('İndirilen kurulumun yayıncı imzası eşleşmedi.')
                self.ready_path=path
                self.set(state='ready',message='Güncelleme doğrulandı. Yeniden başlat düğmesiyle kurulabilir.')
            except Exception as exc:
                if path:path.unlink(missing_ok=True)
                self.set(state='blocked',message=str(exc) if type(exc) is ValueError else 'İndirme veya doğrulama başarısız. Kurulum başlatılmadı.')
            finally:self.guard.release()
        threading.Thread(target=worker,daemon=True).start()
        return {'message':'Güvenli güncelleme hazırlığı başladı.'}

    def update_dir(self):
        directory=self.root/'updates';directory.mkdir(parents=True,exist_ok=True)
        return directory

    def install(self):
        if not self.guard.acquire(blocking=False):raise ValueError('Güncelleme işlemi zaten çalışıyor.')
        try:
            directory=self.supported_install()
            if self.state.get('state')!='ready' or not self.ready_path or not self.manifest:raise ValueError('Doğrulanmış güncelleme hazır değil.')
            path=self.ready_path
            with path.open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
            if path.stat().st_size!=self.manifest['size'] or digest!=self.manifest['sha256']:
                raise ValueError('Hazırlanan kurulum dosyası değişmiş. Yeniden indir.')
            if verify_signature(sys.executable)!=self.manifest['signer_sha256'] or verify_signature(path)!=self.manifest['signer_sha256']:
                raise ValueError('Yayıncı imzası değişti; kurulum engellendi.')
            helper=Path(__file__).resolve().parent.parent/'scripts'/'apply_update.ps1'
            copied=path.parent/'apply-update.ps1';shutil.copyfile(helper,copied)
            plan={'parent_pid':os.getpid(),'installer':str(path),'install_dir':str(directory),
                  'exe':str(Path(sys.executable).resolve()),'sha256':self.manifest['sha256'],
                  'signer_sha256':self.manifest['signer_sha256'],'version':self.release['version'],
                  'backup':str(path.parent/'previous-version'),'log':str(path.parent/'update.log'),
                  'ready':str(path.parent/'helper-ready')}
            plan_path=path.parent/'plan.json';plan_path.write_text(json.dumps(plan),encoding='utf-8')
            process=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(copied),'-PlanPath',str(plan_path)],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+10
            while not Path(plan['ready']).exists():
                if process.poll() is not None or time.monotonic()>deadline:
                    raise ValueError('Güncelleme yardımcısı başlatılamadı; uygulama kapatılmadı. Windows betik politikasını zorlamadan kurulum iptal edildi.')
                time.sleep(.1)
            self.set(state='installing',message='Uygulama kapanıyor. Güncellemeden sonra yeniden açılacak.')
            # Give the local HTTP response time to reach the UI before closing the window.
            threading.Timer(1,self.exit_requested.set).start()
            return {'message':'Doğrulanmış güncelleme kuruluyor; uygulama yeniden açılacak.'}
        finally:self.guard.release()
