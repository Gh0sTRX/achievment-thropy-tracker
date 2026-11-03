"""Localhost-only, no cloud server; import-first architecture with optional Xbox sync."""
from __future__ import annotations
import asyncio
import base64
import math
import json
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
from urllib.parse import parse_qs, urlencode, urlsplit
from .core import Library,normalize
from . import recommendations,artwork
from . import xbox, public_profiles, guides, settings, media_sync, updater, sync_control

BASE=Path(__file__).resolve().parent

class Controller:
    def __init__(self,root=None):
        self.store=Library(root)
        settings.activate(self.store.root)
        self.active_matches=[]
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

    def status(self):
        payload=self.store.payload();library=payload['library'];pins=payload['state']['pins']
        reports={}
        for platform in ('xbox','psn','pc'):
            games=[g for g in library['games'] if g.get('platform')==platform]
            ids={g['id'] for g in games}
            scoped={**library,'games':games,'achievements':[a for a in library['achievements'] if a['game_id'] in ids]}
            reports[platform]={'recommendations':recommendations.rank(scoped,pins),'insights':recommendations.insights(scoped)}
        reports['all']={'recommendations':recommendations.rank(library,pins),'insights':recommendations.insights(library)}
        return {'revision':self.store.revision,'library':payload, 'recommendations':recommendations.rank(library,pins),
                'insights':recommendations.insights(library),'platform_reports':reports,
                'providers':public_profiles.readiness(), 'guides_ready':guides.configured(),
                'settings':settings.status(), 'data_status':self.data_status(), 'update':self.updates.snapshot()}

    def data_status(self):
        job = self.store.status.get('public_job') or {}
        count = len(self.store.library['achievements'])
        if job.get('running'): return {'state':'syncing', 'message':f"Gerçek başarımlar alınıyor · {job.get('done',0)}/{job.get('total') or '?'} oyun · {job.get('message','')}"}
        if job.get('error'): return {'state':'error', 'message':job['error']}
        warnings = self.store.state.get('sync_warnings') or []
        if warnings:
            names = ', '.join(w['game'] for w in warnings[:3])
            return {'state':'partial', 'message':f'{count} kayıt mevcut. {len(warnings)} oyunun verisi yenilenemedi: {names}. Bu oyunların önceki kayıtları korundu.'}
        if count: return {'state':'stored', 'message':f"{count} kaynak kaydı · Son eşitleme: {self.store.state.get('sync_at') or 'CSV içe aktarımı'}"}
        if self.store.status.get('connected'): return {'state':'empty', 'message':'Xbox oturumu açık; henüz başarım indirilmedi. Gerçek verileri yenile.'}
        return {'state':'empty', 'message':'Henüz gerçek başarım verisi yok. Kullanıcı adını sorgula veya TrueAchievements CSV aktar. Örnek oyun gösterilmez.'}

    def install_update(self):
        if not self.allow_update_install:raise ValueError('Güncellemeyi masaüstü uygulamasından başlat.')
        if self.public_guard.locked() or self.guide_guard.locked() or self.media_guard.locked() or self.store.status.get('login_running') or self.store.status.get('reconnect_running') or (self.store.status.get('job') or {}).get('running'):
            raise ValueError('Güncellemeden önce çalışan eşitleme/indirme işlemlerinin bitmesini bekle.')
        with self.store.lock:self.store.save()
        return self.updates.install()

    def sync_linked_profile(self):
        profile = self.store.state.get('linked_profile') or {}
        if not profile.get('gamertag'): raise ValueError('Önce Xbox oturumunu aç.')
        return self.public_sync({'platform':'xbox', 'username':profile['gamertag']})

    def save_settings(self, data):
        if self.public_guard.locked() or self.guide_guard.locked() or (self.store.status.get('job') or {}).get('running') or self.store.status.get('login_running'):
            raise ValueError('Ayarları değiştirmeden önce çalışan işlemin bitmesini bekle.')
        return settings.save(self.store.root, data.get('values', {}), data.get('clear', []))

    def public_sync(self, data):
        platform = str(data.get('platform', ''))
        username = public_profiles.validate(platform, data.get('username', ''))
        if not public_profiles.readiness()[platform]:
            raise ValueError('Bu platformun veri servisi kurulmamış. Kurulum için docs/PUBLIC_PROFILES_TR.md dosyasına bak. Oyuncunun hesabını bağlaması gerekmez.')
        if not self.public_guard.acquire(blocking=False):
            raise ValueError('Profil eşitlemesi zaten çalışıyor.')
        if (self.store.status.get('job') or {}).get('running'):
            self.public_guard.release()
            raise ValueError('Xbox eşitlemesinin bitmesini bekle.')
        self.public_stop.clear()
        self.store.status['public_job'] = {'running': True, 'done': 0, 'total': 0,
                                           'message': 'Profil sorgulanıyor…', 'error': ''}
        def progress(done, total, name):
            with self.store.lock:
                self.store.status['public_job'].update(done=done, total=total, message=name)
        def worker():
            try:
                with self.store.lock:
                    profile=self.store.state.get('public_profiles',{}).get(platform,{})
                    prior=self.store.payload()['library']
                    cache={'id':profile.get('id'),'games':prior['games'],'achievements':prior['achievements']}
                snapshot = public_profiles.fetch(platform, username, progress, stop=self.public_stop.is_set,cache=cache,force=data.get('force') is True)
                if self.public_stop.is_set():raise sync_control.Cancelled()
                report = self.store.apply_public_profile(snapshot)
                with self.store.lock:
                    self.store.status['public_job']['message'] = f"{snapshot['username']}: {report['games']} oyun, {report['achievements']} kupa kaydedildi."
                self.download_media()
                if guides.configured():
                    try:self.generate_guides({'platform': platform})
                    except ValueError as exc:self.store.status['public_job']['message'] += ' '+str(exc)
            except sync_control.Cancelled:
                self.store.status['public_job'].update(cancelled=True,message='Eşitleme durduruldu; önceki arşiv korundu.')
            except Exception as exc:
                # Only application-authored messages are safe for the browser.
                message = str(exc) if type(exc) is ValueError else type(exc).__name__
                self.store.status['public_job']['error'] = message[:350]
            finally:
                self.store.status['public_job']['running'] = False
                self.public_guard.release()
        threading.Thread(target=worker, daemon=True).start()
        return {'message': 'Herkese açık profil eşitlemesi başladı.'}

    def download_media(self):
        if not self.media_guard.acquire(blocking=False):return {'message':'Görsel indirmesi zaten çalışıyor.'}
        self.media_stop.clear()
        self.store.status['media_job']={'running':True,'done':0,'total':0,'message':'Kapak, logo ve ikonlar kontrol ediliyor.'}
        def progress(done,total,name):self.store.status['media_job'].update(done=done,total=total,message=name)
        def worker():
            try:
                report=media_sync.download(self.store,progress,stop=self.media_stop.is_set)
                self.store.status['media_job'].update(report=report,cancelled=self.media_stop.is_set(),message=('İndirme durduruldu; tamamlanan görseller korundu. ' if self.media_stop.is_set() else '')+f"{report['downloaded']} görsel kaydedildi; {len(report['missing'])} görsel kaynakta bulunamadı. {'; '.join(report['errors'])}")
            except Exception as exc:self.store.status['media_job']['message']='Görsel indirmesi: '+type(exc).__name__
            finally:self.store.status['media_job']['running']=False;self.media_guard.release()
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
            raise ValueError('Rehber veri servisi kurulmamış. docs/PUBLIC_PROFILES_TR.md dosyasına bak.')
        if not self.guide_guard.acquire(blocking=False):
            raise ValueError('Rehber araştırması zaten çalışıyor.')
        with self.store.lock:
            items = [dict(a) for a in self.store.library['achievements']
                if (not data.get('game_id') or a['game_id'] == data['game_id'])
                and (not data.get('platform') or a.get('platform') == data['platform'])
                and (a.get('guide') or {}).get('fingerprint') != guides.fingerprint(a)]
        self.guide_stop.clear()
        self.store.status['guide_job'] = {'running': True, 'done': 0, 'total': len(items), 'error': ''}
        def worker():
            try:
                for i, a in enumerate(items):
                    if self.guide_stop.is_set():
                        self.store.status['guide_job']['error'] = 'Araştırma durduruldu; tamamlanan rehberler korundu.'
                        break
                    try:
                        guide = guides.create(a)
                        with self.store.lock:
                            current = next((x for x in self.store.library['achievements'] if x['id'] == a['id']), None)
                            if current and guides.fingerprint(current) == guides.fingerprint(a):
                                current['guide'] = guide
                                self.store.save()
                    except Exception as exc:
                        job=self.store.status['guide_job']
                        job.setdefault('failures',[]).append({'id':a['id'],'reason':str(exc)[:180] if type(exc) is ValueError else type(exc).__name__})
                        if type(exc) is not ValueError or 'servisine erişilemedi' in str(exc):raise
                    finally:self.store.status['guide_job']['done'] = i+1
            except Exception as exc:
                self.store.status['guide_job']['error'] = (str(exc) if type(exc) is ValueError else type(exc).__name__)[:250]
            finally:
                self.store.status['guide_job']['running'] = False
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
        self.store.live_artwork[gid]=choices
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
                        expected=store.library.get('gamertag','').strip()
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
                store.status.update({'connected':False,'message':'Xbox sign-in failed: '+str(exc)[:280]})
            finally:
                store.status['login_running']=False;callback.server_close()
        threading.Thread(target=worker,daemon=True).start()
        return {'message':'Official Microsoft sign-in opened in your browser.'}

    def xbox_reconnect(self):
        profile=asyncio.run(xbox.account_info())
        expected=self.store.library.get('gamertag','').strip()
        if expected and normalize(expected)!=normalize(profile['gamertag']):
            raise ValueError('Xbox account does not match the imported profile.')
        with self.store.lock:
            self.store.state['linked_profile']=profile;self.store.status.update({'connected':True,'message':'Xbox connected: '+profile['gamertag']})
            self.store.save()
        self.sync_linked_profile()
        return {'profile':profile, 'message':'Xbox oturumu doğrulandı; gerçek oyunlar ve başarımlar indiriliyor.'}

    def xbox_discover(self):
        if not self.store.status.get('connected'):raise ValueError('Sign in first')
        found=asyncio.run(xbox.account_titles())
        with self.store.lock:self.active_matches=found
        games=self.store.library['games']
        suggestions=[]
        for item in found:
            exact=[g for g in games if normalize(g['name'])==normalize(item['name'])]
            suggestions.append({**item,'matches':[{'id':g['id'],'name':g['name']} for g in exact]})
        return {'titles':suggestions,'message':f'{len(found)} titles found; choose game mappings explicitly.'}

    def xbox_map(self,data):
        gid=str(data.get('game_id','')); tid=str(data.get('title_id',''))
        game=next((g for g in self.store.library['games'] if g['id']==gid),None)
        candidate=next((x for x in self.active_matches if x['titleId']==tid),None)
        if not game or not candidate:raise ValueError('Choose a discovered title first')
        if normalize(game['name'])!=normalize(candidate['name']):
            raise ValueError('Different title name; automatic unsafe mapping prevented')
        with self.store.lock:
            if any(g.get('title_id')==tid for g in self.store.library['games'] if g['id']!=gid):
                raise ValueError('Title ID is mapped to another edition')
            game['title_id']=tid;game['platform_edition']=candidate.get('platform') or 'auto'
            image=candidate.get('cover_url','')
            if artwork.safe_url(image):game['cover_url']=image;game['image_source']='Xbox TitleHub'
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
        games=[g for g in self.store.library['games'] if g.get('title_id') and (not gid or g['id']==gid)]
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
                            self.store.status['job']['errors'].append({'game':game['name'],'reason':str(e)[:100]})
                            if any(x in str(e) for x in ('429','403','401')):break
                        finally:self.store.status['job']['done']=index+1
            try:asyncio.run(sync())
            except Exception as e:self.store.status['message']='Sync failed: '+str(e)[:250]
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
    def reply(self,value,status=200):
        data=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if not self.allowed():return self.reply({'error':'Host or Origin is not allowed'},403)
        path=urlsplit(self.path).path
        if path in ('/','/index.html'):
            body=(BASE/'web'/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token).encode('utf-8')
            return self.blob(body,'text/html; charset=utf-8')
        if path in ('/ui/ultimate.js','/ui/ultimate.css','/app.js','/visuals.js','/ultimate.js','/model.js','/inline.js','/style.css','/ultimate.css'):
            return self.blob((BASE/'web'/path[1:]).read_bytes(), 'text/javascript' if path.endswith('.js') else 'text/css')
        if path=='/brand/atlas-mark.svg':return self.blob((BASE.parent/'assets'/'atlas-mark.svg').read_bytes(),'image/svg+xml')
        if path=='/api/status':
            c=self.server.controller
            with c.store.lock:
                return self.reply({'revision':c.store.revision,'status':c.store.status,'data_status':c.data_status(),'update':c.updates.snapshot()})
        if path=='/api/data':return self.reply(self.server.controller.status())
        if path=='/api/art/sources':return self.reply(artwork.sources())
        seg=path.split('/')
        if len(seg)==5 and seg[1]=='art' and seg[2] in artwork.CATEGORIES:
            category=seg[2];ident=seg[3]
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
            if n<2 or n>12_000_000:return self.reply({'error':'Request too large'},413)
            data=json.loads(self.rfile.read(n))
            if not isinstance(data,dict):raise ValueError('Expected JSON object')
            path=urlsplit(self.path).path
            methods={
               '/api/import':self.server.controller.import_csv,
               '/api/settings':self.server.controller.save_settings,
               '/api/downloads/stop':self.server.controller.stop_downloads,
               '/api/profiles/sync':self.server.controller.public_sync,
               '/api/guides/generate':self.server.controller.generate_guides,
               '/api/guides/stop':lambda d:self.server.controller.stop_guides(),
               '/api/pin':self.server.controller.set_pin,
               '/api/game/notes':self.server.controller.save_notes,
               '/api/preferences':lambda d:self.server.controller.store.set_preferences(d),
               '/api/art/key':self.server.controller.set_sgdb_key,
               '/api/art/search':self.server.controller.search_art,
               '/api/art/choices':self.server.controller.get_art_choices,
               '/api/art/select':self.server.controller.select_art,
               '/api/art/upload':self.server.controller.upload_art,
               '/api/art/reset':self.server.controller.reset_art,
               '/api/art/theme':self.server.controller.theme_art,
               '/api/media/download':lambda d:self.server.controller.download_media(),
               '/api/xbox/login':lambda d:self.server.controller.xbox_login(),
               '/api/xbox/reconnect':lambda d:self.server.controller.xbox_reconnect(),
               '/api/xbox/discover':lambda d:self.server.controller.sync_linked_profile(),
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
            return self.reply({'error':str(e)[:350]},400)
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
