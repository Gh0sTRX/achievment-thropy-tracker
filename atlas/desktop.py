"""Native Windows window; external browser is only an explicit optional mode."""
import threading
import time


def open_window(url, smoke_report=None, shutdown_event=None):
    import webview
    import sys
    from pathlib import Path
    icon_path=Path(__file__).resolve().parent.parent/'assets'/'achievement-atlas.ico'
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('AchievementAtlas.Desktop')
    window = webview.create_window('Achievement Atlas', url, width=1500, height=950,
        min_size=(980, 640), background_color='#07130f', hidden=False)
    errors = []
    icon_set=[]
    icon_ready=threading.Event()
    def verify_native_icon():
        try:
            if sys.platform=='win32':icon_set.append(icon_path.is_file() and window.native.Icon is not None)
        finally:icon_ready.set()
    window.events.shown += verify_native_icon
    def verify():
        try:
            if not window.events.loaded.wait(timeout=40):
                raise RuntimeError('Desktop document did not load')
            deadline = time.monotonic()+20
            while time.monotonic()<deadline:
                ready = window.evaluate_js("Boolean(window.uiLoaded && document.getElementById('publicUsername') && document.getElementById('providerWizard') && document.getElementById('providerSetupState'))")
                if ready:break
                time.sleep(.2)
            else:raise RuntimeError('Desktop UI did not become ready')
            if sys.platform=='win32' and (not icon_ready.wait(10) or not icon_set or not icon_set[0]):raise RuntimeError('Taskbar icon was not applied')
            window.evaluate_js("navigate('artwork'); true")
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                if window.evaluate_js("document.querySelectorAll('.source-card').length === 11"):break
                time.sleep(.2)
            else:raise RuntimeError('Artwork source panel did not load')
            if not window.evaluate_js("switchPlatform('pc'); document.getElementById('platformNote').textContent.includes('Steam') && document.querySelector('#publicPlatform option[value=pc]') !== null"):
                raise RuntimeError('PC provider availability state failed')
            if not window.evaluate_js("switchPlatform('psn'); navigate('account'); document.getElementById('providerSecret').type==='password' && !document.getElementById('providerPsnHelp').classList.contains('hidden') && document.getElementById('providerSteamHelp').classList.contains('hidden') && document.getElementById('sourceStatus').classList.contains('hidden')"):
                raise RuntimeError('Native PSN setup or hidden global status failed')
            window.evaluate_js("navigate('updates'); true")
            if not window.evaluate_js("Boolean(document.getElementById('checkUpdate') && document.getElementById('installUpdate').classList.contains('hidden'))"):
                raise RuntimeError('Update screen exposed an unverified installation')
            window.evaluate_js("navigate('account'); true")
            if not window.evaluate_js("document.body.click(); page === 'account'"):
                raise RuntimeError('Platform event scope changed the active page')
            for screen in ('quests','hall','profile'):
                if not window.evaluate_js("navigate('"+screen+"'); !document.getElementById('"+screen+"').classList.contains('hidden')"):
                    raise RuntimeError('Ultimate screen failed: '+screen)
            if not window.evaluate_js("typeof AtlasModel === 'object' && AtlasModel.progress([]).ratio === 0"):
                raise RuntimeError('Ultimate data projection failed')
            # Explicit self-test only: synthetic in-memory UI records, never saved as a profile.
            if not window.evaluate_js("""(() => {
                ACTIVE_PLATFORM='all';ACTIVE_DEVICE='all';selectedGame=null;
                DATA.library={...DATA.library,games:[{id:'native-smoke-game',name:'Native smoke fixture',platform:'xbox',devices:['xbox360'],platform_edition:'360'}],achievements:[{id:'native-smoke-ach',game_id:'native-smoke-game',game_name:'Native smoke fixture',name:'Native smoke achievement',platform:'xbox',points:10,unlocked:true,unlock_time:'2026-11-05T10:00:00+03:00',description:'Synthetic provider description',source:'xbox'}]};
                navigate('games');const card=document.querySelector('#gameGrid [data-gid]');card.focus();card.click();
                if(page!=='universe'||!location.hash.startsWith('#/game/'))return false;
                document.querySelector('[data-tab=achievements]').click();
                const row=document.querySelector('#universeContent .achievement-row');
                if(!row?.querySelector('.ach-icon')||!row.querySelector('time')||!row.textContent.includes('Synthetic provider description')||!row.textContent.includes('Xbox API'))return false;
                row.querySelector('[data-ach]').click();
                if(!document.querySelector('.inline-achievement')||document.getElementById('achievementDrawer').open)return false;
                document.querySelector('[data-inline-close]').click();
                if(document.getElementById('detailHero').clientHeight>80)return false;
                AtlasSearch.open('Native smoke');
                if(!document.querySelector('#atlasSearch[open]')||!document.querySelector('[data-search-result]'))return false;
                document.querySelector('#atlasSearch').close();history.back();return true;
            })()"""):
                raise RuntimeError('Native game route, tabs or universal search failed')
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                if window.evaluate_js("page==='games' && Boolean(document.activeElement?.matches('#gameGrid [data-gid]'))"):break
                time.sleep(.1)
            else:raise RuntimeError('Native history/focus restoration failed')
            from pathlib import Path
            import json
            Path(smoke_report).write_text(json.dumps({'ok':True,'renderer':'edgechromium','checks':['taskbar icon','Ultimate screens','honest empty metrics','native window','HTML loaded','JavaScript app ready','global status banner hidden','11 artwork sources','platform switch','PC Steam provider entry (not live account verification)','PSN in-app setup with secret field and scoped help','synthetic Game Universe metadata/date/icon element/inline/compact art/route/tabs/search/back/focus','update screen blocks unverified install']}), encoding='utf-8')
        except Exception as exc:
            errors.append(str(exc))
        finally:
            window.destroy()
    closed=threading.Event()
    window.events.closed += lambda:closed.set()
    def watch_update():
        while not closed.wait(.2):
            if shutdown_event is not None and shutdown_event.is_set():
                window.destroy();return
    webview.start(verify if smoke_report else watch_update, gui='edgechromium', icon=str(icon_path))
    if errors:raise RuntimeError('; '.join(errors))
