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
    with tempfile.TemporaryDirectory() as root:
        settings.save(root, {'OPENAI_API_KEY': 'self-test-placeholder'}, [])
        assert settings.read(root)['OPENAI_API_KEY'] == 'self-test-placeholder'
        app = LocalApp(root)
        thread = threading.Thread(target=app.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(app.url, timeout=10) as response:
                html = response.read().decode()
            assert 'publicUsername' in html and '__TOKEN__' not in html
            for path in ('app.js', 'style.css', 'api/data'):
                with urlopen(app.url+path, timeout=10) as response:
                    assert response.status == 200 and response.read()
        finally:
            app.shutdown(); app.server_close(); thread.join(timeout=5)
    result = {'ok': True, 'version': __version__, 'python': sys.version.split()[0],
              'checks': ['Xbox SDK import', 'PSN SDK import', 'local settings roundtrip',
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
    args = parser.parse_args()
    if args.self_test:
        self_test(args.report)
    else:
        from atlas.server import main
        main(browser=args.browser, root=args.data_dir)


if __name__ == '__main__':
    cli()
