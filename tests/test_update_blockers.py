"""v0.15: active update blockers are explicit and never silently bypassed."""
import json
import tempfile
import threading
import unittest
from urllib.request import urlopen

from atlas.server import Controller, LocalApp


class UpdateBlockerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.controller = Controller(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_clean_session_has_no_blockers(self):
        self.assertEqual(self.controller.update_blockers(), [])
        self.assertEqual(self.controller.status()['update_blockers'], [])

    def test_active_guards_are_reported_without_credentials(self):
        with self.controller.public_guard:
            with self.controller.guide_guard:
                with self.controller.media_guard:
                    found = self.controller.update_blockers()
        self.assertIn('Profil eşitlemesi', found)
        self.assertIn('Türkçe rehber araştırması', found)
        self.assertIn('Oyun görselleri indirmesi', found)

    def test_update_refuses_active_work_before_running_updater(self):
        self.controller.allow_update_install = True
        with self.controller.public_guard:
            with self.assertRaisesRegex(ValueError, 'Profil eşitlemesi'):
                self.controller.install_update()

    def test_icon_download_and_xbox_login_also_block_update(self):
        self.controller.store.status['art_job'] = {'running': True}
        self.controller.store.status['login_running'] = True
        found = self.controller.update_blockers()
        self.assertIn('Başarım ikonları indirmesi', found)
        self.assertIn('Xbox oturum işlemi', found)

    def test_stop_is_cooperative_and_never_force_kills(self):
        self.controller.store.status['public_job'] = {'running': True}
        self.assertIn('Profil eşitlemesi', self.controller.update_blockers())
        self.controller.stop_downloads({'kind': 'all'})
        self.assertTrue(self.controller.public_stop.is_set())
        self.assertTrue(self.controller.guide_stop.is_set())
        self.assertIn('Profil eşitlemesi', self.controller.update_blockers())


class UpdateBlockerHttpTests(unittest.TestCase):
    def test_status_exposes_blockers_to_frontend_without_session_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            app = LocalApp(d)
            worker = threading.Thread(target=app.serve_forever, daemon=True)
            worker.start()
            try:
                app.controller.store.status['media_job'] = {'running': True}
                for suffix in ('api/status', 'api/data'):
                    with urlopen(app.url + suffix) as response:
                        body = json.load(response)
                    self.assertIn('Oyun görselleri indirmesi', body['update_blockers'])
            finally:
                app.shutdown()
                app.server_close()
                worker.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
