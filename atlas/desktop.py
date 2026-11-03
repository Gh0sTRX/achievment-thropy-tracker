"""Native Windows window; external browser is only an explicit optional mode."""
import threading
import time


def open_window(url, smoke_report=None):
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
            from pathlib import Path
            import json
            Path(smoke_report).write_text(json.dumps({'ok':True,'renderer':'edgechromium','checks':['native window','HTML loaded','JavaScript app ready','data status visible']}), encoding='utf-8')
        except Exception as exc:
            errors.append(str(exc))
        finally:
            window.destroy()
    webview.start(verify if smoke_report else None, gui='edgechromium')
    if errors:raise RuntimeError('; '.join(errors))
