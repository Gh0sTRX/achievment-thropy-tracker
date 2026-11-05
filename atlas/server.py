"""Localhost-only, no cloud server; import-first architecture with optional Xbox sync."""
from __future__ import annotations
import asyncio
import base64
import math
import json
import gzip
import re
import mimetypes
import os
import queue
import secrets
import threading
import time
import urllib.error
import webbrowser
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer,HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, unquote
from .core import Library,normalize
from . import recommendations,artwork,accounts
from . import xbox, public_profiles, guides, settings, media_sync, updater, sync_control

BASE=Path(__file__).resolve().parent

def safe_error(exc,limit=250):
    message=str(exc) if type(exc) in (ValueError,xbox.DirectError) else type(exc).__name__
    for field in settings.FIELDS:
        value=settings.get(field)
        if field not in ('ATLAS_GUIDE_MODEL','ATLAS_AUTO_GUIDES') and value:message=message.replace(value,'[gizlendi]')
    return re.sub(r'https?://\S+','[URL gizlendi]',message)[:limit]

class Controller:
    def __init__(self,root=None):
        self.store=Library(root)
        settings.activate(self.store.root)
        self.active_matches=[]
        self.enrichment_batches={}
        self.start_guard=threading.Lock()
        self.public_guard=threading.Lock()
        self.guide_guard=threading.Lock()
        self.guide_stop=threading.Event()
        self.media_guard=threading.Lock()
        self.public_stop=threading.Event()
        self.media_stop=threading.Event()
        self.icons_stop=threading.Event()
        self.xbox_stop=threading.Event()
        self.updates=updater.Updater(self.store.root)
        self.allow_update_install=False
        self.action_guard=threading.RLock()
        self._report_cache=None

    def status(self,known_library_token=None):
        with self.store.lock:
            token=self.store.content_token()
            unchanged=known_library_token==token
            payload=self.store.payload(include_library=not unchanged);revision=self.store.revision
            library=payload['library'] if payload['library'] is not None else self.store.library;pins=payload['state']['pins']
            cache_key=(token,tuple(pins))
            cached_reports=self._report_cache
            if cached_reports and cached_reports[0]==cache_key:
                reports=cached_reports[1]
            else:
                reports={}
                for platform in ('xbox','psn','pc'):
                    games=[g for g in library['games'] if g.get('platform')==platform]
                    ids={g['id'] for g in games}
                    scoped={**library,'games':games,'achievements':[a for a in library['achievements'] if a['game_id'] in ids]}
                    reports[platform]={'recommendations':recommendations.rank(scoped,pins),'insights':recommendations.insights(scoped)}
                reports['all']={'recommendations':recommendations.rank(library,pins),'insights':recommendations.insights(library)}
                self._report_cache=(cache_key,reports)
        return {'revision':revision,'library_token':token,'library_unchanged':unchanged,'library':payload, 'recommendations':reports['all']['recommendations'],
                'insights':reports['all']['insights'],'platform_reports':reports,
                'provider_access':accounts.snapshot(self.store),'providers':public_profiles.readiness(), 'guides_ready':guides.configured(),
                'settings':settings.status(), 'data_status':self.data_status(), 'update':self.updates.snapshot(),
                'update_blockers':self.update_blockers()}

    def data_status(self):
        job = self.store.status.get('public_job') or {}
        count = len(self.store.library['achievements'])
        if job.get('running'): return {'state':'syncing', 'message':f"Gerçek başarımlar alınıyor · {job.get('done',0)}/{job.get('total') or '?'} oyun · {job.get('message','')}"}
        if job.get('error'): return {'state':'error', 'message':job['error']}
        warnings = self.store.state.get('sync_warnings') or []
        if warnings:
            names = ', '.join(w['game'] for w in warnings[:3])+ (f' · +{len(warnings)-3} diğer' if len(warnings)>3 else '')
            return {'state':'partial', 'message':f'{count} kayıt mevcut. {len(warnings)} oyunun verisi yenilenemedi: {names}. Bu oyunların önceki kayıtları korundu.'}
        if count: return {'state':'stored', 'message':f"{count} kaynak kaydı · Son eşitleme: {self.store.state.get('sync_at') or 'CSV içe aktarımı'}"}
        if self.store.status.get('connected'): return {'state':'empty', 'message':'Xbox oturumu açık; henüz başarım indirilmedi. Gerçek verileri yenile.'}
        return {'state':'empty', 'message':'Henüz gerçek başarım verisi yok. Kullanıcı adını sorgula veya TrueAchievements CSV aktar. Örnek oyun gösterilmez.'}

    def update_blockers(self):
        """Human-readable active tasks; reporting does not reveal credentials."""
        current = self.store.status
        blockers = []
        if self.public_guard.locked() or (current.get('public_job') or {}).get('running'):
            blockers.append('Profil eşitlemesi')
        if self.guide_guard.locked() or (current.get('guide_job') or {}).get('running'):
            blockers.append('Türkçe rehber araştırması')
        if self.media_guard.locked() or (current.get('media_job') or {}).get('running'):
            blockers.append('Oyun görselleri indirmesi')
        if (current.get('art_job') or {}).get('running'):
            blockers.append('Başarım ikonları indirmesi')
        if (current.get('job') or {}).get('running'):
            blockers.append('Xbox eşitlemesi')
        if current.get('login_running') or current.get('reconnect_running'):
            blockers.append('Xbox oturum işlemi')
        return blockers

    def install_update(self):
        if not self.allow_update_install:raise ValueError('Güncellemeyi masaüstü uygulamasından başlat.')
        blockers = self.update_blockers()
        if blockers:
            raise ValueError('Güncelleme bekliyor: ' + ', '.join(blockers) + '. İşlemleri güvenle durdurup bitmesini bekle.')
        with self.store.lock:self.store.save()
        return self.updates.install()

    def export_archive(self):
        return self.store.export_archive()

    def restore_archive(self, data):
        if data.get('confirm') is not True:
            raise ValueError('Arşivi geri yüklemek için açık onay gerekli.')
        blockers = self.update_blockers()
        if blockers:
            raise ValueError('Geri yükleme bekliyor: ' + ', '.join(blockers))
        if self.updates.snapshot().get('state') == 'installing':
            raise ValueError('Güncelleme sırasında arşiv geri yüklenemez.')
        return self.store.restore_archive(data.get('archive'))

    def sync_linked_profile(self):
        profile = self.store.state.get('linked_profile') or {}
        if not profile.get('gamertag'): raise ValueError('Önce Xbox oturumunu aç.')
        return self.public_sync({'platform':'xbox', 'username':self.store.state.get('public_profiles',{}).get('xbox',{}).get('username') or profile['gamertag']})

    def save_settings(self, data):
        if self.public_guard.locked() or self.guide_guard.locked() or (self.store.status.get('job') or {}).get('running') or self.store.status.get('login_running'):
            raise ValueError('Ayarları değiştirmeden önce çalışan işlemin bitmesini bekle.')
        result=settings.save(self.store.root, data.get('values', {}), data.get('clear', []))
        for platform,key in accounts.FIELDS.items():
            if key in data.get('values',{}) or key in data.get('clear',[]):
                accounts.remember(self.store,platform,'configured' if public_profiles.readiness().get(platform) else 'not_configured')
        return result

    def provider_setup(self,data):
        if self.public_guard.locked() or (self.store.status.get('job') or {}).get('running') or self.store.status.get('login_running'):raise ValueError('Önce çalışan hesap işleminin bitmesini bekle.')
        platform=str(data.get('platform',''))
        if platform not in accounts.LABELS:raise ValueError('Platform seç.')
        username=public_profiles.validate(platform,data.get('username',''))
        secret=str(data.get('secret') or '').strip()
        if secret:
            if platform not in accounts.FIELDS:raise ValueError('Xbox için Microsoft erişim düğmesini kullan.')
            if platform=='psn' and data.get('consent') is not True:raise ValueError('Yalnız kendi yetkili PSN oturumunu kullanmayı onayla.')
            settings.save(self.store.root,{accounts.FIELDS[platform]:secret},[])
        with self.store.lock:
            self.store.state.setdefault('provider_inputs',{})[platform]=username
            self.store.state.setdefault('provider_access',{})[platform]={'state':'configured' if public_profiles.readiness().get(platform) else 'not_configured'}
            self.store.save()
        return {'message':'Bu platformun ayarı kaydedildi. Canlı bağlantıyı ayrı düğmeyle doğrula.'}

    def provider_test(self,data):
        platform=str(data.get('platform',''))
        username=public_profiles.validate(platform,data.get('username',''))
        if not public_profiles.readiness().get(platform):return accounts.remember(self.store,platform,'not_configured',message='Uygulamada kurulum yap.')
        try:
            identity=accounts.probe(platform,username)
            return accounts.remember(self.store,platform,'verified',message='Servis erişimi çevrimiçi doğrulandı. Başarım arşivi henüz eşitlenmedi.',**identity)
        except Exception as exc:
            state,message=accounts.failure(exc)
            return accounts.remember(self.store,platform,state,message=message)

    def record_activity(self,platform,kind,job):
        from datetime import datetime,timezone
        from copy import deepcopy
        with self.store.lock:
            event={'platform':platform,'kind':kind,'at':datetime.now(timezone.utc).isoformat(),'account_id':(self.store.state.get('public_profiles',{}).get(platform) or {}).get('id'),'username':job.get('username',''),'cancelled':bool(job.get('cancelled')),'error':job.get('error',''),'message':job.get('message',''),'report':deepcopy(job.get('report'))}
            history=self.store.state.setdefault('activity_history',[]);history.append(event);del history[:-100];self.store.save()

    def public_sync(self, data):
        platform = str(data.get('platform', ''))
        username = public_profiles.validate(platform, data.get('username', ''))
        if not public_profiles.readiness()[platform]:
            raise ValueError('Bu platformun veri servisi kurulmamış. Hesap & Veri → Uygulamada kurulum yap adımlarını tamamla.')
        if not self.public_guard.acquire(blocking=False):
            raise ValueError('Profil eşitlemesi zaten çalışıyor.')
        if (self.store.status.get('job') or {}).get('running'):
            self.public_guard.release()
            raise ValueError('Xbox eşitlemesinin bitmesini bekle.')
        self.public_stop.clear()
        self.store.status['public_job'] = {'running': True, 'done': 0, 'total': 0,
                                           'message': 'Profil sorgulanıyor…', 'error': '', 'platform':platform,'provider':'steam' if platform=='pc' else platform,'username':username}
        def progress(done, total, name):
            with self.store.lock:
                self.store.status['public_job'].update(done=done, total=total, message=name)
        def worker():
            try:
                with self.store.lock:
                    profile=self.store.state.get('public_profiles',{}).get(platform,{})
                    prior=self.store.payload()['library']
                    cache={'id':profile.get('id'),'games':prior['games'],'achievements':prior['achievements'],'schema_root':self.store.root/'cache'/'steam-schemas'}
                snapshot = public_profiles.fetch(platform, username, progress, stop=self.public_stop.is_set,cache=cache,force=data.get('force') is True)
                if self.public_stop.is_set():raise sync_control.Cancelled()
                report = self.store.apply_public_profile(snapshot)
                with self.store.lock:
                    self.store.status['public_job']['report']={**report,'failed_titles':snapshot.get('warnings',[])}
                    self.store.state.setdefault('sync_warnings_by_platform',{})[platform]=snapshot.get('warnings',[])
                    self.store.state.setdefault('provider_access',{})[platform]={'state':'verified','username':snapshot['username'],'id':snapshot['id'],'checked_at':snapshot['synced_at']}
                    self.store.status['public_job']['message'] = f"{snapshot['username']}: {report['games']} oyun, {report['achievements']} {'kupa' if platform=='psn' else 'başarım'} kaydedildi."
                if self.public_stop.is_set():
                    self.store.status['public_job']['message']='Profil kaydedildi; sonraki indirmeler durduruldu.'
                    return
                self.download_media({'platform':platform})
                if settings.get('ATLAS_AUTO_GUIDES','0') == '1' and guides.configured() and not self.public_stop.is_set():
                    try:self.generate_guides({'platform': platform})
                    except ValueError:self.store.status['guide_job']={'platform':platform,'running':False,'error':'İsteğe bağlı rehber servisi kullanılamadı. Hesap verileri kaydedildi.'}
            except sync_control.Cancelled:
                self.store.status['public_job'].update(cancelled=True,message='Eşitleme durduruldu; önceki arşiv korundu.')
            except Exception as exc:
                # Only application-authored messages are safe for the browser.
                state,message=accounts.failure(exc)
                accounts.remember(self.store,platform,state,message=message)
                self.store.status['public_job']['error'] = safe_error(exc,350)
            finally:
                self.store.status['public_job']['running'] = False
                self.record_activity(platform,'profile',self.store.status['public_job'])
                self.public_guard.release()
        threading.Thread(target=worker, daemon=True).start()
        return {'message': 'Herkese açık profil eşitlemesi başladı.'}

    def download_media(self,data=None):
        data=data or {}
        platform=data.get('platform') or None
        gid=data.get('game_id') or None
        if gid:platform=self.art_game(data).get('platform')
        if not self.media_guard.acquire(blocking=False):return {'message':'Görsel indirmesi zaten çalışıyor.'}
        self.media_stop.clear()
        self.store.status['media_job']={'running':True,'done':0,'total':0,'message':'Görsel kaynakları kontrol ediliyor.','platform':platform,'game_id':gid}
        def progress(done,total,name):self.store.status['media_job'].update(done=done,total=total,message=name)
        def worker():
            try:
                report=media_sync.download(self.store,progress,stop=self.media_stop.is_set,platform=platform,game_id=gid)
                self.store.status['media_job'].update(report=report,cancelled=self.media_stop.is_set(),message=('İndirme durduruldu; tamamlanan görseller korundu. ' if self.media_stop.is_set() else '')+f"{report['downloaded']} indirildi; {report['cached']} önbellekte; {report['missing_source']} kaynaksız; {report['failed']} başarısız; {report['blocked']} engellendi. {'; '.join(report['errors'])}")
            except Exception as exc:self.store.status['media_job']['message']='Görsel indirmesi: '+type(exc).__name__
            finally:
                self.store.status['media_job']['running']=False
                self.record_activity(platform,'media',self.store.status['media_job'])
                self.media_guard.release()
        threading.Thread(target=worker,daemon=True).start()
        return {'message':'Mevcut oyunların resmi kapak/logo ve başarım ikonları indiriliyor.'}

    def stop_downloads(self,data):
        kind=data.get('kind','all')
        if kind not in ('all','profile','media'):raise ValueError('İşlem türü geçersiz.')
        if kind in ('all','profile'):self.public_stop.set();self.xbox_stop.set()
        if kind in ('all','media'):self.media_stop.set();self.icons_stop.set()
        if kind=='all':self.guide_stop.set()
        for key in (('public_job','job') if kind=='profile' else ('media_job','art_job') if kind=='media' else ('public_job','job','media_job','art_job','guide_job')):
            if (self.store.status.get(key) or {}).get('running'):self.store.status[key]['stopping']=True
        return {'message':'Durdurma istendi. Devam eden ağ isteği kapanırken tamamlanmış dosyalar korunacak.'}

    def stop_guides(self):
        self.guide_stop.set()
        return {'message': 'Rehber araştırması mevcut istek tamamlandığında duracak.'}

    def generate_guides(self, data):
        if not guides.configured():
            raise ValueError('İsteğe bağlı Türkçe rehber için Gelişmiş Ayarlar bölümünde Brave/OpenAI servisini yapılandır. Hesap eşitlemesi bundan bağımsızdır.')
        if not self.guide_guard.acquire(blocking=False):
            raise ValueError('Rehber araştırması zaten çalışıyor.')
        with self.store.lock:
            items = [dict(a) for a in self.store.library['achievements']
                if (not data.get('game_id') or a['game_id'] == data['game_id'])
                and (not data.get('platform') or a.get('platform') == data['platform'])
                and (a.get('guide') or {}).get('fingerprint') != guides.fingerprint(a)]
        self.guide_stop.clear()
        self.store.status['guide_job'] = {'running': True, 'done': 0, 'total': len(items), 'error': '', 'platform':data.get('platform')}
        def worker():
            try:
                for i, a in enumerate(items):
                    if self.guide_stop.is_set():
                        self.store.status['guide_job']['error'] = 'Araştırma durduruldu; tamamlanan rehberler korundu.'
                        break
                    try:
                        guide = guides.create(a, stop=self.guide_stop.is_set)
                        with self.store.lock:
                            current = next((x for x in self.store.library['achievements'] if x['id'] == a['id']), None)
                            if current and guides.fingerprint(current) == guides.fingerprint(a):
                                current['guide'] = guide
                                self.store.save()
                    except guides.Cancelled:
                        self.store.status['guide_job'].update(cancelled=True,error='Araştırma durduruldu; tamamlanan rehberler korundu.')
                        break
                    except Exception as exc:
                        job=self.store.status['guide_job']
                        job.setdefault('failures',[]).append({'id':a['id'],'reason':str(exc)[:180] if type(exc) is ValueError else type(exc).__name__})
                        if type(exc) is not ValueError or 'servisine erişilemedi' in str(exc):raise
                    finally:self.store.status['guide_job']['done'] = i+1
            except Exception as exc:
                self.store.status['guide_job']['error'] = (str(exc) if type(exc) is ValueError else type(exc).__name__)[:250]
            finally:
                self.store.status['guide_job']['running'] = False
                self.record_activity(data.get('platform'),'guides',self.store.status['guide_job'])
                self.guide_guard.release()
        threading.Thread(target=worker, daemon=True).start()
        return {'message': f'{len(items)} kupa için Türkçe kaynak araştırması başladı.'}

    def import_csv(self,data):
        if self.public_guard.locked():raise ValueError('Profil eşitlemesinin bitmesini bekle.')
        if self.store.state.get('public_profiles'):
            raise ValueError('Kullanıcı adıyla oluşturulan arşiv CSV ile birleştirilmez. CSV için ayrı bir veri klasörü kullan.')
        return self.store.import_csv(str(data.get('earned','')),str(data.get('locked','')),str(data.get('gamertag','')))

    def set_pin(self,data):return self.store.set_pin(str(data.get('id','')),bool(data.get('pinned')))

    def set_sgdb_key(self,data):
        key=str(data.get('key','')).strip()
        if len(key)<6 or len(key)>400:raise ValueError('SteamGridDB API key invalid')
        self.store.steamgriddb_key=key
        return {'message':'Artwork API key held in memory for this session, not written to the project.'}

    def search_art(self,data):
        return {'matches':artwork.search_game(str(data.get('name','')),self.store.steamgriddb_key)}

    def choices_art(self,data):
        return {'choices':artwork.candidates(data.get('sgdb_id'),self.store.steamgriddb_key)}

    def art_game(self, data):
        game=next((g for g in self.store.library['games'] if g['id']==str(data.get('game_id',''))),None)
        if not game:raise ValueError('Önce kütüphanenden bir oyun seç.')
        return game

    def save_art(self, data, metadata):
        from datetime import datetime, timezone
        with self.store.lock:
            game=self.art_game(data);kind=str(data.get('kind','hero'))
            previous=(game.get('artwork_meta') or {}).get(kind,{})
            original=previous.get('original_url',game.get(kind+'_url',''))
            game.setdefault('artwork_meta',{})[kind]={**metadata,'original_url':original if original!='local' else '',
                'saved_at':datetime.now(timezone.utc).isoformat()}
            game[kind+'_url']='local';game['image_source']=metadata['provider']
            self.store.save()
        return {'message':'Görsel oyununa kaydedildi. Çevrimdışıyken de kullanılabilir.'}

    def upload_art(self, data):
        game=self.art_game(data);kind=str(data.get('kind','hero'))
        if kind not in ('cover','hero','logo','banner','screenshot'):raise ValueError('Geçersiz görsel kategorisi.')
        encoded=data.get('image','')
        if not isinstance(encoded,str) or len(encoded)>10_666_672:raise ValueError('Görsel en fazla 8 MB olabilir.')
        try:raw=base64.b64decode(encoded,validate=True)
        except (ValueError,TypeError):raise ValueError('Görsel dosyası okunamadı.') from None
        meta=artwork.store_bytes(self.store.root,kind,game['id'],raw)
        return self.save_art(data,{**meta,'provider':'user_file','provider_id':'', 'source_url':'',
            'rights_note':'Kullanıcının seçtiği yerel dosya; dağıtım izni doğrulanmadı.'})

    def reset_art(self, data):
        with self.store.lock:
            game=self.art_game(data);kind=str(data.get('kind','hero'))
            if kind not in ('cover','hero','logo','banner','screenshot'):raise ValueError('Geçersiz görsel kategorisi.')
            meta=game.setdefault('artwork_meta',{}).pop(kind,{})
            if game.get(kind+'_url')=='local':game[kind+'_url']=meta.get('original_url','')
            artwork.remove_cached(self.store.root,kind,game['id'])
            self.store.save()
        return {'message':'Özel görsel kaldırıldı; varsa önceki kaynak görseli kullanılacak.'}

    def theme_art(self,data):
        theme=str(data.get('theme','auto'))
        if theme not in ('auto','ember','ice','forest','dusk','sunrise'):raise ValueError('Tema geçersiz.')
        x=float(data.get('x',50));y=float(data.get('y',38))
        overlay=float(data.get('overlay',.68));blur=float(data.get('blur',0))
        if not math.isfinite(overlay) or not .5<=overlay<=.85 or not math.isfinite(blur) or not 0<=blur<=12:raise ValueError('Görsel görünüm değeri geçersiz.')
        if not all(math.isfinite(v) and 0<=v<=100 for v in (x,y)):raise ValueError('Odak konumu geçersiz.')
        with self.store.lock:
            game=self.art_game(data)
            game['art_theme']={'preset':theme,'x':x,'y':y,'overlay':overlay,'blur':blur}
            self.store.save()
        return {'message':'Görsel odağı ve atmosfer bu oyun için kaydedildi.'}

    def save_notes(self,data):
        notes=data.get('notes','')
        if not isinstance(notes,str) or len(notes)>8000:raise ValueError('Not en fazla 8000 karakter olabilir.')
        with self.store.lock:
            game=self.art_game(data)
            game['notes']=notes
            self.store.save()
        return {'message':'Oyun notların bu cihazda kaydedildi.'}

    def select_art(self,data):
        game=self.art_game(data);gid=game['id'];kind=str(data.get('kind',''))
        if kind not in ('cover','hero','logo'):raise ValueError('Image type unknown')
        url=str(data.get('url',''))
        candidate=next((c for c in self.store.live_artwork.get(gid,[]) if c['kind']==kind and c['url']==url),None)
        if not candidate:raise ValueError('Önce oyun ve sürüm eşleşmesini onaylayıp bir arama sonucu seç.')
        if (game.get('artwork_meta') or {}).get(kind,{}).get('provider')=='user_file' and not data.get('replace_local'):
            raise ValueError('Bu oyun için yerel dosya seçilmiş. Değiştirmek için önce özel görseli sıfırla.')
        meta=artwork.cache_image(self.store.root,kind,gid,url)
        return self.save_art(data,{**meta,'provider':'SteamGridDB','provider_id':candidate.get('provider_id',''),
            'source_url':candidate.get('source_url','https://www.steamgriddb.com/'),
            'rights_note':candidate.get('rights_note','Topluluk görseli; hak sahipliği bağımsızdır.')})

    def get_art_choices(self,data):
        gid=str(data.get('game_id',''))
        game=next((g for g in self.store.library['games'] if g['id']==gid),None)
        if not game:raise ValueError('Game unknown')
        if data.get('confirmed') is not True:raise ValueError('Oyun ve sürüm eşleşmesini onayla; diğer platform kimlikleri otomatik eşleştirilmez.')
        choices=artwork.candidates(data.get('sgdb_id'),self.store.steamgriddb_key)
        with self.store.lock:
            current=next((g for g in self.store.library['games'] if g['id']==gid),None)
            fields=('platform','title_id','platform_edition','devices')
            if not current or any(current.get(k)!=game.get(k) for k in fields):
                raise ValueError('Oyun kaydı değişti; sürüm eşleşmesini yeniden onayla.')
            self.store.live_artwork[gid]=choices
            current['artwork_match']={'provider':'SteamGridDB','provider_id':str(int(data['sgdb_id'])),'game_id':gid,
                'platform':current.get('platform'),'title_id':current.get('title_id'),'platform_edition':current.get('platform_edition'),
                'devices':list(current.get('devices',[])),'confirmed':True}
            official=[c for c in current.get('art_candidates',[]) if c.get('provider')!='SteamGridDB']
            current['art_candidates']=official+[{**c,'provider':'SteamGridDB','confirmed_game_id':gid} for c in choices]
            self.store.save()
        return {'choices':choices}

    def xbox_login(self):
        xbox._sdk() # Check installed before spawn
        store=self.store
        with self.start_guard:
            if store.status.get('login_running'):raise ValueError('Login already running')
            store.status.update({'login_running':True,'message':'Opening official Microsoft sign-in in your browser…'})
        state=secrets.token_urlsafe(32)
        q=queue.Queue(maxsize=1)
        class Callback(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                request=urlsplit(self.path)
                params=parse_qs(request.query)
                if request.path!='/auth/callback' or self.headers.get('Host') not in ('localhost:8080','127.0.0.1:8080'):
                    return self.send_error(404)
                if len(params.get('state',[]))!=1 or not secrets.compare_digest(params['state'][0],state):
                    return self.send_error(403,'OAuth state mismatch')
                if 'error' in params: value=('error',str(params['error'][0])[:200])
                elif len(params.get('code',[]))==1:value=('code',params['code'][0])
                else:return self.send_error(400)
                try:q.put_nowait(value)
                except queue.Full:return self.send_error(409)
                content=b'<html><body style="font:18px Segoe UI;background:#071912;color:#e6f6e6;padding:70px"><h1>Achievement Atlas</h1><p>Sign-in reply received. Return to the app.</p></body></html>'
                self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
        try:
            callback=HTTPServer(('127.0.0.1',8080),Callback)
            callback.timeout=1
        except OSError as exc:
            store.status.update({'login_running':False,'message':'Port 8080 is already in use.'})
            raise ValueError('Microsoft redirect port 8080 unavailable') from exc
        def worker():
            try:
                sdk=xbox._sdk();client_id=sdk[4]; redirect=sdk[6]
                url='https://login.live.com/oauth20_authorize.srf?'+urlencode({
                    'client_id':client_id,'response_type':'code','approval_prompt':'auto',
                    'scope':'Xboxlive.signin Xboxlive.offline_access',
                    'redirect_uri':redirect,'state':state})
                webbrowser.open(url)
                deadline=time.monotonic()+300; response=None
                while time.monotonic()<deadline:
                    callback.handle_request()
                    try:response=q.get_nowait();break
                    except queue.Empty:continue
                if not response:raise ValueError('Microsoft login timed out')
                if response[0]=='error':raise ValueError('Microsoft declined sign-in: '+response[1])
                # Verify profile BEFORE writing tokens to disk.
                SDK,Manager,_,Signed,*_=sdk
                async def exchange():
                    async with Signed() as session:
                        manager=Manager(session,sdk[4],sdk[5],sdk[6]);await manager.request_tokens(response[1])
                        api=SDK(manager);profile=xbox.normalize_profile(xbox._dump(await api.profile.get_profile_by_xuid(str(api.xuid))),str(api.xuid))
                        expected=accounts.xbox_archive_name(store).strip()
                        if expected and normalize(expected)!=normalize(profile['gamertag']):
                            raise ValueError(f"Imported profile ({expected}) does not match connected Xbox account ({profile['gamertag']}); data not mixed.")
                        p=sdk[-1];p.parent.mkdir(parents=True,exist_ok=True)
                        tmp=p.with_suffix('.pending');tmp.write_text(manager.oauth.model_dump_json(),encoding='utf-8');os.replace(tmp,p)
                        return profile
                profile=asyncio.run(exchange())
                with store.lock:
                    store.state['linked_profile']=profile;store.status.update({'connected':True,'message':'Xbox connected: '+profile['gamertag']})
                    store.save()
                self.sync_linked_profile()
            except Exception as exc:
                store.status.update({'connected':False,'message':'Xbox sign-in failed: '+safe_error(exc,280)})
            finally:
                store.status['login_running']=False;callback.server_close()
        threading.Thread(target=worker,daemon=True).start()
        return {'message':'Official Microsoft sign-in opened in your browser.'}

    def xbox_reconnect(self):
        profile=asyncio.run(xbox.account_info())
        expected=accounts.xbox_archive_name(self.store).strip()
        if expected and normalize(expected)!=normalize(profile['gamertag']):
            raise ValueError('Xbox account does not match the imported profile.')
        with self.store.lock:
            self.store.state['linked_profile']=profile;self.store.status.update({'connected':True,'message':'Xbox connected: '+profile['gamertag']})
            self.store.save()
        self.sync_linked_profile()
        return {'profile':profile, 'message':'Xbox oturumu doğrulandı; gerçek oyunlar ve başarımlar indiriliyor.'}

    def xbox_discover(self):
        if not public_profiles.readiness().get('xbox'):raise ValueError('Önce uygulama içinde Xbox erişimini kur.')
        found=asyncio.run(xbox.account_titles())
        with self.store.lock:self.active_matches=found
        games=self.store.library['games']
        suggestions=[]
        for item in found:
            exact=[g for g in games if normalize(g['name'])==normalize(item['name'])]
            suggestions.append({**item,'matches':[{'id':g['id'],'name':g['name'],'edition':g.get('platform_edition')} for g in exact if g.get('platform')=='xbox']})
        return {'titles':suggestions,'message':f'{len(found)} titles found; choose game mappings explicitly.'}

    def preview_enrichment(self,data):
        from copy import deepcopy
        from . import enrichment
        import secrets
        with self.store.lock:
            game=deepcopy(self.art_game(data))
            if game.get('platform')!='xbox' or not game.get('title_id'):
                raise ValueError('Önce Xbox erişimini kur ve keşfedilen oyun/edisyon kimliğini Hesap & Veri ekranında açıkça onayla.')
            items=deepcopy([a for a in self.store.library['achievements'] if a['game_id']==game['id']])
            library_token=self.store.content_token()
        info=asyncio.run(xbox.account_info())
        profile=self.store.state.get('public_profiles',{}).get('xbox',{})
        if profile.get('id') and str(profile['id'])!=str(info['xuid']):raise ValueError('Bu Xbox arşivinin hesabı ile yetkili oturum farklı. Kazanılma tarihleri başka hesaptan alınmaz.')
        if not profile.get('id') and not accounts.xbox_archive_name(self.store):raise ValueError('Xbox arşivinin oyuncu adı bilinmiyor. Hesap & Veri ekranında Xbox kullanıcı adını doğrulayıp kaydet.')
        if not profile.get('id') and accounts.xbox_archive_name(self.store) and normalize(info['gamertag'])!=normalize(accounts.xbox_archive_name(self.store)):raise ValueError('CSV oyuncusu ile Xbox oturumu eşleşmiyor.')
        records=asyncio.run(xbox.title_achievements(game['title_id'],game.get('platform_edition') or 'auto'))
        pairs=enrichment.proposals(game,items,records);token=secrets.token_hex(16)
        self.enrichment_batches={token:{'game':game,'pairs':pairs,'library_token':library_token}}
        return {'token':token,'game':game['name'],'platform':game['platform'],'edition':game.get('platform_edition'),'title_id':game['title_id'],'pairs':[{'local_id':p['local_id'],'name':p['remote']['name'],'provider_id':str(p['remote']['id'])} for p in pairs]}

    def confirm_enrichment(self,data):
        from . import enrichment
        batch=self.enrichment_batches.get(data.get('token'))
        if not batch or data.get('confirmed') is not True:raise ValueError('Önerilen her başarım kimliğini inceleyip açıkça onayla.')
        selected=data.get('selected')
        if not isinstance(selected,list) or not selected:raise ValueError('Onaylanacak başarım seç.')
        result=enrichment.apply(self.store,batch,selected);self.enrichment_batches.clear();return result

    def xbox_map(self,data):
        gid=str(data.get('game_id','')); tid=str(data.get('title_id',''))
        game=next((g for g in self.store.library['games'] if g['id']==gid),None)
        candidate=next((x for x in self.active_matches if x['titleId']==tid and x.get('platform')==data.get('edition')),None)
        if data.get('confirmed') is not True or not game or game.get('platform')!='xbox' or not candidate:raise ValueError('Choose a discovered Xbox title first')
        if normalize(game['name'])!=normalize(candidate['name']):
            raise ValueError('Different title name; automatic unsafe mapping prevented')
        with self.store.lock:
            if any(g.get('platform')=='xbox' and g.get('title_id')==tid and g.get('platform_edition')==candidate.get('platform') for g in self.store.library['games'] if g['id']!=gid):
                raise ValueError('Title ID is mapped to another edition')
            if game.get('title_id')!=tid or game.get('platform_edition')!=candidate.get('platform'):
                game.pop('artwork_match',None);game['art_candidates']=[]
            game['title_id']=tid;game['platform_edition']=candidate.get('platform') or 'auto'
            from . import editions
            editions.apply(game,editions.xbox_devices(candidate,generation='1' if candidate.get('platform')=='360' else '2') or (['xbox360'] if candidate.get('platform')=='360' else game.get('devices',[])))
            game['title_identity_confirmed']=True
            image=candidate.get('cover_url','')
            if artwork.safe_url(image) and game.get('cover_url')!='local':game['cover_url']=image;game['image_source']='Xbox TitleHub'
            self.store.save()
        return {'message':'Mapped '+game['name']+' to Xbox Title ID '+tid}

    def xbox_sync(self,data):
        if self.public_guard.locked():raise ValueError('Profil eşitlemesinin bitmesini bekle.')
        if self.store.status.get('connected'):
            return self.sync_linked_profile()
        target=(self.store.state.get('public_profiles') or {}).get('xbox')
        linked=self.store.state.get('linked_profile') or {}
        if target and target['id']!=str(linked.get('xuid','')):
            raise ValueError('Bu arşiv herkese açık hedef profile ait. Kullanıcı adıyla yenileme düğmesini kullan.')
        gid=str(data.get('game_id',''))
        games=[g for g in self.store.library['games'] if g.get('platform')=='xbox' and g.get('title_id') and (not gid or g['id']==gid)]
        if not games:raise ValueError('Map a title ID first')
        if self.store.status.get('job',{}).get('running'):raise ValueError('Sync already running')
        self.xbox_stop.clear()
        self.store.status['job']={'running':True,'total':len(games),'done':0,'errors':[]}
        def worker():
            async def sync():
                async with xbox.authenticated_client() as (client,xuid):
                    profile=self.store.state.get('linked_profile') or {}
                    if str(profile.get('xuid',''))!=str(xuid):raise ValueError('Profile XUID changed. Login again.')
                    for index,game in enumerate(games):
                        if self.xbox_stop.is_set():break
                        try:
                            records=await xbox.fetch_title_achievements(client,xuid,game['title_id'],game.get('platform_edition') or 'auto')
                            report=self.store.apply_live_game(game['id'],records)
                            self.store.status['message']=f"{game['name']} · {report['updated']} newly earned"
                        except Exception as e:
                            self.store.status['job']['errors'].append({'game':game['name'],'reason':safe_error(e,100)})
                            if any(x in str(e) for x in ('429','403','401')):break
                        finally:self.store.status['job']['done']=index+1
            try:asyncio.run(sync())
            except Exception as e:self.store.status['message']='Sync failed: '+safe_error(e)
            finally:self.store.status['job']['running']=False
        threading.Thread(target=worker,daemon=True).start()
        return {'message':'Xbox sync started. Existing earned achievements will not be revoked.'}

    def cache_icons(self,data):
        ids=data.get('ids') or []
        if not isinstance(ids,list) or not 1<=len(ids)<=60:raise ValueError('Select 1–60 achievements')
        index={a['id']:a for a in self.store.library['achievements']}
        selected=[]
        for ident in dict.fromkeys(str(i) for i in ids):
            if ident not in index:raise ValueError('Unknown achievement')
            if index[ident].get('icon_url') and not artwork.cached(self.store.root,'icon',ident):selected.append(index[ident])
        if self.store.status.get('art_job',{}).get('running'):raise ValueError('Image download is already running')
        self.icons_stop.clear()
        self.store.status['art_job']={'running':True,'done':0,'total':len(selected),'found':0,'message':''}
        def worker():
            for i,a in enumerate(selected):
                if self.icons_stop.is_set():break
                try:
                    if artwork.safe_url(a['icon_url']):
                        artwork.cache_image(self.store.root,'icon',a['id'],a['icon_url'])
                        self.store.status['art_job']['found']+=1
                except urllib.error.HTTPError as exc:
                    if exc.code in (403,429):
                        self.store.status['art_job']['message']='Provider blocked downloads. Stopped without bypassing access controls.';break
                except (OSError,ValueError,urllib.error.URLError):pass
                finally:self.store.status['art_job']['done']=i+1
            self.store.status['art_job']['running']=False
        threading.Thread(target=worker,daemon=True).start()
        return {'message':f'{len(selected)} official icon URLs queued. Missing URLs cannot be invented.'}

def accepts_gzip(header):
    values={}
    for item in str(header).split(','):
        parts=item.strip().split(';');coding=parts[0].strip().lower()
        quality=1.0
        for part in parts[1:]:
            key,separator,value=part.strip().partition('=')
            if key.lower()=='q' and separator:
                try:quality=float(value)
                except ValueError:quality=0.0
        values[coding]=quality if math.isfinite(quality) and 0<=quality<=1 else 0.0
    return values.get('gzip',values.get('*',0))>0


class Handler(BaseHTTPRequestHandler):
    server_version='AchievementAtlas/0.5'
    def log_message(self,*args):pass
    def allowed(self):
        port=self.server.server_port
        host=self.headers.get('Host')
        origin=self.headers.get('Origin')
        return host in (f'localhost:{port}',f'127.0.0.1:{port}') and origin in (None,f'http://localhost:{port}',f'http://127.0.0.1:{port}')
    def blob(self,data,mimetype):
        self.send_response(200);self.send_header('Content-Type',mimetype)
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)))
        self.end_headers();self.wfile.write(data)
    def reply(self,value,status=200,compress=False):
        data=json.dumps(value,ensure_ascii=False).encode('utf-8')
        compressed=False
        if compress and len(data)>=2048 and accepts_gzip(self.headers.get('Accept-Encoding','')):
            packed=gzip.compress(data,compresslevel=3,mtime=0)
            if len(packed)<len(data):data=packed;compressed=True
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        if compress:self.send_header('Vary','Accept-Encoding')
        if compressed:self.send_header('Content-Encoding','gzip')
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if not self.allowed():return self.reply({'error':'Host or Origin is not allowed'},403)
        path=urlsplit(self.path).path
        if path in ('/','/index.html'):
            body=(BASE/'web'/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token).encode('utf-8')
            return self.blob(body,'text/html; charset=utf-8')
        if path in ('/ui/search.js','/ui/foundation.js','/ui/foundation.css','/ui/motion.js','/ui/motion.css','/ui/shell.js','/ui/shell.css','/ui/ultimate.js','/ui/ultimate.css','/app.js','/visuals.js','/ultimate.js','/model.js','/provider_setup.js','/achievement_row.js','/inline.js','/art_transition.js','/style.css','/ultimate.css'):
            return self.blob((BASE/'web'/path[1:]).read_bytes(), 'text/javascript' if path.endswith('.js') else 'text/css')
        if path=='/brand/atlas-mark.svg':return self.blob((BASE.parent/'assets'/'atlas-mark.svg').read_bytes(),'image/svg+xml')
        if path=='/api/status':
            c=self.server.controller
            with c.store.lock:
                return self.reply({'revision':c.store.revision,'status':c.store.status,'data_status':c.data_status(),'provider_access':accounts.snapshot(c.store),'update':c.updates.snapshot(),
                                   'update_blockers':c.update_blockers()})
        if path=='/api/data':return self.reply(self.server.controller.status(self.headers.get('X-Atlas-Library-Token')),compress=True)
        if path=='/api/art/health':return self.reply(media_sync.health(self.server.controller.store))
        if path=='/api/art/sources':return self.reply(artwork.sources())
        seg=path.split('/')
        if len(seg)==5 and seg[1]=='art' and seg[2] in artwork.CATEGORIES:
            category=seg[2];ident=unquote(seg[3])
            # /art/{kind}/{id}/file; no arbitrary filesystem traversal.
            if seg[4]=='file' and re_id(ident):
                p=artwork.cached(self.server.controller.store.root,category,ident)
                if p:return self.blob(p.read_bytes(),{'.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'}[p.suffix])
        return self.reply({'error':'Not found'},404)
    def do_POST(self):
        if not self.allowed() or self.headers.get('X-Atlas-Token')!=self.server.token:
            return self.reply({'error':'Forbidden'},403)
        if not self.headers.get('Content-Type','').startswith('application/json'):
            return self.reply({'error':'JSON required'},415)
        try:
            n=int(self.headers.get('Content-Length','0'))
            path=urlsplit(self.path).path
            limit=50_000_000 if path=='/api/archive/restore' else 12_000_000
            if n<2 or n>limit:return self.reply({'error':'Request too large'},413)
            data=json.loads(self.rfile.read(n))
            if not isinstance(data,dict):raise ValueError('Expected JSON object')
            path=urlsplit(self.path).path
            methods={
               '/api/import':self.server.controller.import_csv,
               '/api/archive/export':lambda d:self.server.controller.export_archive(),
               '/api/archive/restore':self.server.controller.restore_archive,
               '/api/settings':self.server.controller.save_settings,
               '/api/downloads/stop':self.server.controller.stop_downloads,
               '/api/providers/setup':self.server.controller.provider_setup,
               '/api/providers/test':self.server.controller.provider_test,
               '/api/profiles/sync':self.server.controller.public_sync,
               '/api/guides/generate':self.server.controller.generate_guides,
               '/api/guides/stop':lambda d:self.server.controller.stop_guides(),
               '/api/pin':self.server.controller.set_pin,
               '/api/game/notes':self.server.controller.save_notes,
               '/api/preferences':lambda d:self.server.controller.store.set_preferences(d),
               '/api/art/health':lambda d:media_sync.health(self.server.controller.store,d.get('platform')),
               '/api/enrichment/preview':self.server.controller.preview_enrichment,
               '/api/enrichment/confirm':self.server.controller.confirm_enrichment,
               '/api/art/key':self.server.controller.set_sgdb_key,
               '/api/art/search':self.server.controller.search_art,
               '/api/art/choices':self.server.controller.get_art_choices,
               '/api/art/select':self.server.controller.select_art,
               '/api/art/upload':self.server.controller.upload_art,
               '/api/art/reset':self.server.controller.reset_art,
               '/api/art/theme':self.server.controller.theme_art,
               '/api/media/download':self.server.controller.download_media,
               '/api/xbox/login':lambda d:self.server.controller.xbox_login(),
               '/api/xbox/reconnect':lambda d:self.server.controller.xbox_reconnect(),
               '/api/xbox/discover':lambda d:self.server.controller.xbox_discover(),
               '/api/xbox/map':self.server.controller.xbox_map,
               '/api/xbox/sync':self.server.controller.xbox_sync,
               '/api/icons':self.server.controller.cache_icons,
               '/api/update/check':lambda d:self.server.controller.updates.check(),
               '/api/update/download':lambda d:self.server.controller.updates.download(),
               '/api/update/install':lambda d:self.server.controller.install_update(),
            }
            if path not in methods:return self.reply({'error':'Unknown action'},404)
            with self.server.controller.action_guard:
                if self.server.controller.updates.snapshot().get('state')=='installing':raise ValueError('Güncelleme kuruluyor; uygulamanın yeniden açılmasını bekle.')
                result=methods[path](data)
            return self.reply(result)
        except (ValueError,KeyError,xbox.DirectError,urllib.error.HTTPError,urllib.error.URLError) as e:
            return self.reply({'error':safe_error(e,350)},400)
        except Exception:
            return self.reply({'error':'Unexpected application error; credentials omitted from logs.'},500)

def re_id(v):
    import re
    return bool(re.fullmatch(r'[a-zA-Z0-9:_-]{2,120}',v))

class LocalApp(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,root=None):
        super().__init__(('127.0.0.1',0),Handler)
        self.controller=Controller(root)
        self.token=secrets.token_urlsafe(36)
    @property
    def url(self):return f'http://127.0.0.1:{self.server_port}/'

def main(browser=False, root=None, desktop_report=None):
    from . import instance
    lock=instance.acquire()
    if lock is False:return
    try:app=LocalApp(root)
    except Exception:
        instance.release(lock);raise
    t=threading.Thread(target=app.serve_forever,daemon=True);t.start()
    app.controller.allow_update_install=not browser and not desktop_report
    if not desktop_report:app.controller.updates.check()
    if not desktop_report and app.controller.store.state.get('linked_profile') and xbox.has_tokens():
        def resume():
            app.controller.store.status['reconnect_running']=True
            try:app.controller.xbox_reconnect()
            except Exception as exc:
                message=str(exc) if type(exc) in (ValueError,xbox.DirectError) else type(exc).__name__
                app.controller.store.status['public_job']={'running':False,'error':'Xbox yenilemesi başarısız: '+message[:250]}
            finally:app.controller.store.status['reconnect_running']=False
        threading.Thread(target=resume,daemon=True).start()
    try:
        if browser:
            webbrowser.open(app.url)
            input('Uygulamayi kapatmak icin Enter tusuna bas...')
        else:
            from .desktop import open_window
            open_window(app.url, smoke_report=desktop_report, shutdown_event=app.controller.updates.exit_requested)
    finally:
        app.shutdown()
        app.server_close()
        instance.release(lock)
