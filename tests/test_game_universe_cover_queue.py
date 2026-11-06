"""Library-wide Game Universe cover repair; no title-based auto matches."""
import io
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from atlas.core import Library
from atlas import artwork, media_sync


def png():
    out = io.BytesIO()
    Image.new('RGB', (16, 24), (40, 80, 130)).save(out, format='PNG')
    return out.getvalue()


class CoverInventoryTests(unittest.TestCase):
    def test_entire_library_paginated_not_just_three_games(self):
        with TemporaryDirectory() as root:
            store = Library(root)
            store.library['games'] = [
                {'id': f'game{i:02d}', 'platform': ('xbox', 'psn', 'pc')[i % 3],
                 'name': f'Game {i:02d}', 'platform_edition': 'known'}
                for i in range(27)
            ] + [{'id': 'netflix', 'name': 'Netflix', 'platform': 'xbox'}]
            artwork.store_bytes(store.root, 'cover', 'game00', png())
            a = media_sync.cover_inventory(store, offset=0, limit=20)
            b = media_sync.cover_inventory(store, offset=20, limit=20)
            self.assertEqual((a['total_games'], a['covered'], a['missing']), (27, 1, 26))
            self.assertEqual(len(a['items']), 20)
            self.assertEqual(len(b['items']), 6)
            self.assertTrue(a['has_more'])
            self.assertFalse(b['has_more'])
            self.assertEqual(len({x['game_id'] for x in a['items'] + b['items']}), 26)
            self.assertTrue(all(x['state'] == 'missing_source' for x in a['items'] + b['items']))
            only_pc = media_sync.cover_inventory(store, platform='pc')
            self.assertEqual(only_pc['total_games'], 9)
            with self.assertRaises(ValueError):
                media_sync.cover_inventory(store, offset=-1)
            with self.assertRaises(ValueError):
                media_sync.cover_inventory(store, limit=999)

    def test_downloads_only_known_cover_sources_not_icons_or_fake_titles(self):
        with TemporaryDirectory() as root:
            store = Library(root)
            store.library['games'] = [
                {'id': 'game-one', 'platform': 'xbox', 'name': 'Imported CSV',
                 'cover_url': 'https://xboxlive.com/real-cover.png', 'platform_edition': '360'},
                {'id': 'game-two', 'platform': 'psn', 'name': 'Unknown CSV', 'platform_edition': 'ps4'}
            ]
            store.library['achievements'] = [
                {'id': 'ach-one', 'game_id': 'game-one', 'platform': 'xbox',
                 'icon_url': 'https://xboxlive.com/icon.png'}
            ]
            with patch.object(artwork, 'fetch', return_value=(png(), 'image/png')) as request:
                report = media_sync.download(store, covers_only=True)
            self.assertEqual(report['planned'], 2)
            self.assertEqual(report['downloaded'], 1)
            self.assertEqual(report['missing_source'], 1)
            request.assert_called_once_with('https://xboxlive.com/real-cover.png')
            self.assertIsNotNone(artwork.game_cached(store.root, store.library['games'][0], 'cover'))
            self.assertIsNone(artwork.cached(store.root, 'icon', 'ach-one'))
            self.assertEqual(media_sync.cover_inventory(store)['covered'], 1)

    def test_identity_conflicts_and_user_art_are_not_overwritten(self):
        with TemporaryDirectory() as root:
            store = Library(root)
            store.library['games'] = [
                {'id': 'edition-a', 'name': 'Known Edition', 'platform': 'xbox',
                 'platform_edition': '360', 'title_id': '100',
                 'cover_url': 'local', 'artwork_meta': {'cover': {
                     'game_id': 'edition-a', 'platform': 'xbox',
                     'platform_edition': '360', 'title_id': '200',
                     'provider': 'Xbox TitleHub', 'source_url': 'https://xboxlive.com/wrong'}}},
                {'id': 'edition-b', 'name': 'Chosen Cover', 'platform': 'pc',
                 'platform_edition': 'steam', 'cover_url': 'local',
                 'artwork_meta': {'cover': {'provider': 'user_file'}}}
            ]
            artwork.store_bytes(store.root, 'cover', 'edition-b', png())
            before = artwork.cached(store.root, 'cover', 'edition-b').read_bytes()
            inventory = media_sync.cover_inventory(store)
            self.assertEqual(inventory['covered'], 1)
            self.assertEqual(inventory['missing'], 1)
            self.assertEqual(inventory['items'][0]['state'], 'identity_mismatch')
            with patch.object(artwork, 'fetch') as request:
                media_sync.download(store, covers_only=True)
                request.assert_not_called()
            self.assertEqual(artwork.cached(store.root, 'cover', 'edition-b').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
