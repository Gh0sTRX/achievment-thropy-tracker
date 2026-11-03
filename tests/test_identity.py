"""Identity boundaries: display name reuse, stable IDs, cross-platform guards."""
import tempfile
import unittest
from copy import deepcopy

from atlas import identity, public_profiles
from atlas.core import Library


def snapshot(platform='xbox', account='123', name='Player'):
    game = public_profiles.game(platform, 'title-1', 'Example', 'unknown')
    achievement = public_profiles.achievement(game, {'id': '0', 'name': 'Test',
                                                     'unlocked': True, 'gamerscore': 10})
    return {'platform': platform, 'id': account, 'username': name,
            'games': [game], 'achievements': [achievement],
            'synced_at': '2026-11-04T00:00:00Z'}


class AccountIdentityTests(unittest.TestCase):
    def test_same_id_name_change_keeps_unlock_history(self):
        with tempfile.TemporaryDirectory() as root:
            store = Library(root)
            store.apply_public_profile(snapshot(name='Player'))
            store.apply_public_profile(snapshot(name='New Gamertag'))
            self.assertEqual(store.state['public_profiles']['xbox']['id'], '123')
            self.assertEqual(store.state['public_profiles']['xbox']['username'], 'New Gamertag')
            self.assertTrue(store.library['achievements'][0]['unlocked'])

    def test_same_visible_name_different_xuid_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            store = Library(root)
            store.apply_public_profile(snapshot(account='123'))
            before = store.export_archive()
            with self.assertRaisesRegex(ValueError, 'farklı bir hesap kimliğine'):
                store.apply_public_profile(snapshot(account='999'))
            self.assertEqual(store.export_archive()['sha256'], before['sha256'])

    def test_different_display_names_do_not_merge_two_accounts(self):
        with tempfile.TemporaryDirectory() as root:
            store = Library(root)
            store.apply_public_profile(snapshot(account='123', name='First'))
            store.apply_public_profile(snapshot(account='999', name='Second'))
            self.assertEqual(store.state['public_profiles']['xbox']['id'], '999')
            self.assertEqual(len(list((store.root / 'profiles').glob('*.json'))), 2)

    def test_provider_scope_identity_never_uses_username_only(self):
        self.assertNotEqual(identity.provider_key('xbox', '123'),
                            identity.provider_key('psn', '123'))
        self.assertNotEqual(identity.display_key('Somebody#1234'),
                            identity.display_key('Somebody'))
        identity.verify_requested_name('xbox', 'Player', 'player')
        with self.assertRaisesRegex(ValueError, 'uyuşmuyor'):
            identity.verify_requested_name('xbox', 'Player', 'SomeoneElse')

    def test_cross_provider_and_game_links_are_rejected(self):
        doc = snapshot('xbox')
        doc['achievements'][0]['platform'] = 'psn'
        with self.assertRaisesRegex(ValueError, 'oyun/platform'):
            identity.validate_snapshot(doc)
        doc = snapshot('xbox')
        doc['achievements'][0]['game_id'] = 'missing-game'
        with self.assertRaisesRegex(ValueError, 'oyun/platform'):
            identity.validate_snapshot(doc)

    def test_missing_stable_id_is_rejected_before_disk_writes(self):
        with tempfile.TemporaryDirectory() as root:
            store = Library(root)
            bad = snapshot()
            bad['id'] = ''
            with self.assertRaisesRegex(ValueError, 'kalıcı kimlik'):
                store.apply_public_profile(bad)
            self.assertFalse((store.root / 'library.json').exists())

    def test_id_suffix_and_unicode_are_not_confused(self):
        self.assertEqual(identity.display_key('  MÄLI #111  '), 'mäli #111')
        self.assertNotEqual(identity.display_key('Mali #111'), identity.display_key('Mali #112'))


if __name__ == '__main__':
    unittest.main()
