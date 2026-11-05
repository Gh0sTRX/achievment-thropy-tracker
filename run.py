"""Source and frozen application entry point."""
import argparse
import json
import sys
import tempfile
import threading
from pathlib import Path
from urllib.request import urlopen
from atlas import __version__


def self_test(report=None):
    from atlas.server import LocalApp
    from atlas import xbox, settings
    from psnawp_api import PSNAWP
    from psnawp_api.models.trophies import PlatformType
    xbox._sdk()
    assert PSNAWP and PlatformType.PS4
    from atlas.pc import provider
    assert provider('steam').validate('76561198000000000')=='76561198000000000'
    with tempfile.TemporaryDirectory() as root:
        settings.save(root, {'OPENAI_API_KEY': 'self-test-placeholder'}, [])
        assert settings.read(root)['OPENAI_API_KEY'] == 'self-test-placeholder'
        import io
        from PIL import Image
        from atlas import artwork
        tiny=io.BytesIO();Image.new('RGB',(16,16),(12,30,50)).save(tiny,format='PNG')
        assert artwork.store_bytes(root,'hero','selftest',tiny.getvalue())['width']==16
        assert len(artwork.sources()['providers'])==11
        from atlas.provenance import verifier
        verifier()
        app = LocalApp(root)
        thread = threading.Thread(target=app.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(app.url, timeout=10) as response:
                html = response.read().decode()
            assert 'publicUsername' in html and '__TOKEN__' not in html
            for path in ('app.js', 'visuals.js', 'style.css', 'api/data', 'api/art/sources'):
                with urlopen(app.url+path, timeout=10) as response:
                    assert response.status == 200 and response.read()
        finally:
            app.shutdown(); app.server_close(); thread.join(timeout=5)
    result = {'ok': True, 'version': __version__, 'python': sys.version.split()[0],
              'checks': ['Xbox SDK import', 'PSN SDK import', 'Steam provider import (no live request)', 'local settings roundtrip',
                         'HTTP server', 'HTML and static assets', 'JSON API']}
    if report:
        Path(report).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


def cli():
    parser = argparse.ArgumentParser(description='Achievement Atlas')
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--data-dir', help='Kütüphane ve ayarlar için ayrı klasör')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--report')
    parser.add_argument('--desktop-test', action='store_true')
    parser.add_argument('--verify-dev-update', action='store_true')
    parser.add_argument('--manifest')
    parser.add_argument('--bundle')
    parser.add_argument('--installer')
    parser.add_argument('--verification-report')
    args = parser.parse_args()
    if args.verify_dev_update:
        from atlas import updater,provenance
        try:
            manifest=updater.validate_development_manifest(json.loads(Path(args.manifest).read_text(encoding='utf-8')))
            result=provenance.verify_bundle(Path(args.bundle),manifest,Path(args.installer))
            Path(args.verification_report).write_text(json.dumps(result),encoding='utf-8')
        except Exception:
            if args.verification_report:Path(args.verification_report).write_text(json.dumps({'verified':False}),encoding='utf-8')
            raise SystemExit(2)
    elif args.self_test:
        self_test(args.report)
    else:
        from atlas.server import main
        if args.desktop_test:
            if not args.report:parser.error('--desktop-test requires --report')
            try:
                with tempfile.TemporaryDirectory() as root:
                    main(root=root, desktop_report=args.report)
            except Exception as exc:
                Path(args.report).write_text(json.dumps({'ok':False,'error':type(exc).__name__+': '+str(exc)[:500]}),encoding='utf-8')
                raise SystemExit(2)
        else:
            try:main(browser=args.browser, root=args.data_dir)
            except Exception as exc:
                if sys.platform == 'win32':
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(None, 'Masaüstü penceresi açılamadı. Microsoft Edge WebView2 Runtime kurulu olmalı.\n\n'+type(exc).__name__+': '+str(exc)[:400], 'Achievement Atlas', 16)
                raise


if __name__ == '__main__':
    cli()
