"""Native Windows window; external browser is only an explicit optional mode."""
import threading
import time


def open_window(url, smoke_report=None, shutdown_event=None):
    import webview
    window = webview.create_window('Achievement Atlas', url, width=1500, height=950,
        min_size=(980, 640), background_color='#07130f', hidden=False)
    errors = []
    def verify():
        try:
            if not window.events.loaded.wait(timeout=40):
                raise RuntimeError('Desktop document did not load')
            deadline = time.monotonic()+20
            while time.monotonic()<deadline:
                ready = window.evaluate_js("Boolean(document.getElementById('publicUsername') && document.getElementById('sourceStatus') && document.getElementById('sourceStatus').textContent.length)")
                if ready:break
                time.sleep(.2)
            else:raise RuntimeError('Desktop UI did not become ready')
            window.evaluate_js("navigate('artwork'); true")
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                if window.evaluate_js("document.querySelectorAll('.source-card').length === 11"):break
                time.sleep(.2)
            else:raise RuntimeError('Artwork source panel did not load')
            if not window.evaluate_js("switchPlatform('pc'); document.getElementById('platformNote').textContent.includes('planlanıyor')"):
                raise RuntimeError('PC planned-state failed')
            window.evaluate_js("switchPlatform('psn'); navigate('account'); true")
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
            from pathlib import Path
            import json
            Path(smoke_report).write_text(json.dumps({'ok':True,'renderer':'edgechromium','checks':['Ultimate screens','honest empty metrics','native window','HTML loaded','JavaScript app ready','data status visible','11 artwork sources','platform switch','PC planned state','simple account screen','update screen blocks unverified install']}), encoding='utf-8')
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
    webview.start(verify if smoke_report else watch_update, gui='edgechromium')
    if errors:raise RuntimeError('; '.join(errors))
