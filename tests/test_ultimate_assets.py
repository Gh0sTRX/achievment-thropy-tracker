import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from atlas.server import LocalApp


class UltimateAssetsTests(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.TemporaryDirectory()
        self.app = LocalApp(self.data.name)
        self.thread = threading.Thread(target=self.app.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.app.shutdown()
        self.app.server_close()
        self.thread.join(timeout=3)
        self.data.cleanup()

    def test_native_theme_css_and_js_are_allowlisted(self):
        with urlopen(self.app.url + "ui/shell.css") as response:
            self.assertIn("text/css", response.headers["Content-Type"])
            self.assertIn(b"Atlas native skin system", response.read())
        with urlopen(self.app.url + "ui/shell.js") as response:
            self.assertIn("text/javascript", response.headers["Content-Type"])
            self.assertIn(b"const SKINS", response.read())

    def test_main_page_uses_one_native_shell_and_console(self):
        with urlopen(self.app.url) as response:
            html = response.read().decode("utf-8")
        self.assertIn('/ui/shell.css', html)
        self.assertIn('/ui/shell.js', html)
        self.assertNotIn('src="/ui/ultimate.js"', html)
        self.assertNotIn('href="/ui/ultimate.css"', html)
        self.assertIn('id="atlasThemeSkin"', html)
        self.assertIn('id="atlasConsole"', html)
        self.assertIn('id="timeline"', html)
        self.assertIn('/app.js', html)

    def test_static_allowlist_does_not_serve_arbitrary_path(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(self.app.url + "ui/something-private.js")
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
