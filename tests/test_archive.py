"""v0.15 archive safety: checksums, ID isolation, rollback and localhost auth."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from atlas import archive
from atlas.core import Library
from atlas.server import Controller, LocalApp

EARNED = ("GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,UnlockDate\n"
          "Game A,First,https://www.trueachievements.com/a456/first-achievement,20,25,1.25,,2026-01-01\n")
LOCKED = ("GameName,AchievementName,AchievementPageURL,Gamerscore,TAScore,TARatio,DLCName,Unachieveable\n"
          "Game A,Second,https://www.trueachievements.com/a457/second-achievement,30,40,1.35,,\n")


class LocalArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Library(self.root)
        self.store.import_csv(EARNED, LOCKED, 'Player')
        self.store.set_pin('ta:457', True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_export_contains_exact_records_but_no_credentials(self):
        self.store.state['oauth_token'] = 'do-not-export'
        self.store.state['provider_secret'] = 'private-secret'
        result = self.store.export_archive()
        self.assertEqual(result['format'], archive.FORMAT)
        self.assertEqual(len(archive.verify_archive(result)['library']['achievements']), 2)
        self.assertIn('ta:457', result['data']['state']['pins'])
        self.assertNotIn('oauth_token', result['data']['state'])
        self.assertNotIn('provider_secret', json.dumps(result))

    def test_restore_round_trip_saves_recovery_copy(self):
        old = self.store.export_archive()
        self.store.state['pins'] = []
        self.store.library['games'] = []
        self.store.library['achievements'] = []
        self.store.save()
        report = self.store.restore_archive(old)
        self.assertEqual(report['games'], 1)
        self.assertEqual(report['achievements'], 2)
        fresh = Library(self.root)
        self.assertEqual(fresh.state['pins'], ['ta:457'])
        self.assertEqual({a['id'] for a in fresh.library['achievements']}, {'ta:456', 'ta:457'})
        recovery = list((self.root / 'recovery').glob('pre-restore-*.json'))
        self.assertEqual(len(recovery), 1)
        self.assertEqual(archive.verify_archive(json.loads(recovery[0].read_text()))['library']['games'], [])
        self.assertFalse((self.root / '.atlas-restore-pending.json').exists())

    def test_modified_archive_is_rejected_without_writing(self):
        document = self.store.export_archive()
        document['data']['library']['games'][0]['name'] = 'Tampered'
        before = (self.root / 'library.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'değiştirilmiş'):
            self.store.restore_archive(document)
        self.assertEqual((self.root / 'library.json').read_bytes(), before)
        self.assertFalse((self.root / 'recovery').exists())

    def test_duplicate_and_cross_platform_records_rejected(self):
        document = self.store.export_archive()
        document['data']['library']['achievements'].append(
            dict(document['data']['library']['achievements'][0]))
        with self.assertRaisesRegex(ValueError, 'tekrarı|kimliği'):
            archive.make_archive(document['data']['library'], document['data']['state'])
        document = self.store.export_archive()
        document['data']['library']['achievements'][0]['platform'] = 'psn'
        with self.assertRaisesRegex(ValueError, 'platform'):
            archive.make_archive(document['data']['library'], document['data']['state'])

    def test_unknown_format_and_broken_hash_rejected(self):
        document = self.store.export_archive()
        document['format'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'Desteklenmeyen'):
            archive.verify_archive(document)
        document = self.store.export_archive()
        document['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'değiştirilmiş'):
            archive.verify_archive(document)

    def test_recover_interrupted_two_file_restore_on_next_start(self):
        backup = self.store.export_archive()
        folder = self.root / 'recovery'
        folder.mkdir()
        name = 'pre-restore-20261104T000000Z-123456abcdef.json'
        (folder / name).write_text(json.dumps(backup), encoding='utf-8')
        (self.root / '.atlas-restore-pending.json').write_text(
            json.dumps({'backup': name}), encoding='utf-8')
        (self.root / 'library.json').write_text('{"games": []}', encoding='utf-8')
        (self.root / 'state.json').write_text('{"pins": []}', encoding='utf-8')
        reloaded = Library(self.root)
        self.assertEqual(len(reloaded.library['achievements']), 2)
        self.assertEqual(reloaded.state['pins'], ['ta:457'])
        self.assertFalse((self.root / '.atlas-restore-pending.json').exists())

    def test_failed_write_rolls_back_both_files(self):
        backup = self.store.export_archive()
        self.store.set_pin('ta:457', False)
        baseline = self.store.export_archive()
        original = archive._write_json
        failed = [False]
        def one_failure(path, data):
            if Path(path).name == 'state.json' and not failed[0]:
                failed[0] = True
                raise OSError('simulated failure')
            return original(path, data)
        with patch.object(archive, '_write_json', side_effect=one_failure):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.store.restore_archive(backup)
        reloaded = Library(self.root)
        self.assertEqual(reloaded.state['pins'], baseline['data']['state']['pins'])
        self.assertEqual(reloaded.library, baseline['data']['library'])


class ArchiveApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = LocalApp(self.tmp.name)
        self.thread = threading.Thread(target=self.app.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.app.shutdown()
        self.app.server_close()
        self.thread.join(timeout=3)
        self.tmp.cleanup()

    def post(self, path, value, token=True):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['X-Atlas-Token'] = self.app.token
        request = Request(self.app.url + path, data=json.dumps(value).encode(),
                          headers=headers, method='POST')
        return urlopen(request)

    def test_export_requires_secret_token(self):
        with self.assertRaises(HTTPError) as ctx:
            self.post('api/archive/export', {}, token=False)
        self.assertEqual(ctx.exception.code, 403)
        with self.post('api/archive/export', {}) as response:
            exported = json.load(response)
        self.assertEqual(exported['format'], archive.FORMAT)

    def test_restore_roundtrip_http(self):
        with self.post('api/archive/export', {}) as response:
            snapshot = json.load(response)
        with self.post('api/archive/restore', {'archive': snapshot, 'confirm': True}) as response:
            report = json.load(response)
        self.assertEqual(report['games'], 0)
        self.assertEqual(report['achievements'], 0)

    def test_restore_needs_explicit_confirmation_even_with_local_token(self):
        with self.post('api/archive/export', {}) as response:
            snapshot = json.load(response)
        with self.assertRaises(HTTPError) as ctx:
            self.post('api/archive/restore', {'archive': snapshot})
        self.assertEqual(ctx.exception.code, 400)
        self.assertIn('onay', ctx.exception.read().decode())
        self.assertFalse((Path(self.tmp.name) / 'recovery').exists())

    def test_restore_is_refused_while_sync_active(self):
        with self.post('api/archive/export', {}) as response:
            snapshot = json.load(response)
        self.app.controller.store.status['public_job'] = {'running': True}
        with self.assertRaises(HTTPError) as ctx:
            self.post('api/archive/restore', {'archive': snapshot, 'confirm': True})
        self.assertEqual(ctx.exception.code, 400)
        self.assertIn('Profil eşitlemesi', ctx.exception.read().decode())
        self.assertFalse((Path(self.tmp.name) / 'recovery').exists())


if __name__ == '__main__':
    unittest.main()
