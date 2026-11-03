"""Crash-safe normal persistence and exact restoration of legacy JSON fields."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from atlas import journal
from atlas.core import Library


class TwoFileJournalTests(unittest.TestCase):
    def test_two_json_files_advance_together_and_cleanup_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = Library(root)
            store.library['gamertag'] = 'Real Player'
            store.state['pins'] = ['abc']
            store.save()
            self.assertEqual(Library(root).library['gamertag'], 'Real Player')
            self.assertEqual(Library(root).state['pins'], ['abc'])
            for name in ('.atlas-save-pending.json',
                         '.atlas-save-library.previous', '.atlas-save-state.previous'):
                self.assertFalse((root / name).exists())

    def test_failure_after_first_replace_restores_exact_previous_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = Library(root)
            store.library['gamertag'] = 'First Player'
            store.state['unknown_legacy_field'] = {'keep': 'unchanged'}
            store.save()
            before = [(root / n).read_bytes() for n in ('library.json', 'state.json')]
            old = journal._atomic_bytes
            failed = [False]

            def fail_second(path, data):
                if Path(path).name == 'state.json' and not failed[0]:
                    failed[0] = True
                    raise OSError('injected disk failure')
                return old(path, data)

            store.library['gamertag'] = 'Second Player'
            with patch.object(journal, '_atomic_bytes', side_effect=fail_second):
                with self.assertRaisesRegex(OSError, 'injected disk failure'):
                    store.save()
            self.assertEqual([(root / n).read_bytes()
                              for n in ('library.json', 'state.json')], before)
            self.assertEqual(store.library['gamertag'], 'First Player')
            self.assertEqual(store.state['unknown_legacy_field'], {'keep': 'unchanged'})
            self.assertFalse((root / '.atlas-save-pending.json').exists())

    def test_next_boot_rolls_back_abandoned_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = Library(root)
            store.library['gamertag'] = 'Original'
            store.state['legacy'] = ['unknown', 'kept']
            store.save()
            original_library = (root / 'library.json').read_bytes()
            original_state = (root / 'state.json').read_bytes()
            journal._atomic_bytes(root / '.atlas-save-library.previous', original_library)
            journal._atomic_bytes(root / '.atlas-save-state.previous', original_state)
            journal._atomic_bytes(root / '.atlas-save-pending.json',
                                  json.dumps({'format': 'atlas-save-v1',
                                              'existed': [True, True]}).encode())
            journal._atomic_bytes(root / 'library.json', b'{"gamertag":"Incomplete"}')
            recovered = Library(root)
            self.assertEqual(recovered.library['gamertag'], 'Original')
            self.assertEqual(recovered.state['legacy'], ['unknown', 'kept'])
            self.assertEqual((root / 'library.json').read_bytes(), original_library)
            self.assertEqual((root / 'state.json').read_bytes(), original_state)

    def test_bad_marker_never_overwrites_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'library.json').write_text('{"untouched":true}')
            (root / '.atlas-save-pending.json').write_text('{"format":"unknown"}')
            with self.assertRaisesRegex(ValueError, 'yarıda kalmış'):
                Library(root)
            self.assertEqual((root / 'library.json').read_text(),
                             '{"untouched":true}')

    def test_empty_initial_state_rolls_back_to_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.atlas-save-pending.json').write_text(json.dumps({
                'format':'atlas-save-v1', 'existed':[False, False]
            }))
            (root / 'library.json').write_text('{"partial":true}')
            self.assertTrue(journal.recover_pending(root))
            self.assertFalse((root / 'library.json').exists())
            self.assertFalse((root / 'state.json').exists())


if __name__ == '__main__':
    unittest.main()
