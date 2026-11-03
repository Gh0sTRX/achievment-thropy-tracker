import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from atlas import settings
from atlas.server import Controller


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.root=TemporaryDirectory()
        self.env=patch.dict(os.environ, {k:'' for k in settings.FIELDS})
        # Absence, unlike an explicitly empty variable, allows local settings.
        self.env.start()
        for k in settings.FIELDS:os.environ.pop(k, None)
        settings.activate(self.root.name)
    def tearDown(self):
        self.env.stop()
        settings._values={}
        self.root.cleanup()

    def test_roundtrip_and_never_return_secrets(self):
        result=settings.save(self.root.name, {'ATLAS_PSN_NPSSO':'a'*64, 'OPENAI_API_KEY':'private-value'}, [])
        self.assertNotIn('private-value', json.dumps(result))
        self.assertNotIn('a'*64, json.dumps(result))
        self.assertEqual(settings.read(self.root.name)['OPENAI_API_KEY'],'private-value')
        settings.activate(self.root.name)
        self.assertEqual(settings.get('OPENAI_API_KEY'),'private-value')
        path=Path(self.root.name)/'settings.json'
        if os.name=='nt':
            self.assertNotIn('private-value',path.read_text())
        else:
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_blank_preserves_clear_removes_and_environment_wins(self):
        settings.save(self.root.name, {'OPENAI_API_KEY':'local-value'}, [])
        settings.save(self.root.name, {'OPENAI_API_KEY':''}, [])
        self.assertEqual(settings.get('OPENAI_API_KEY'),'local-value')
        with patch.dict(os.environ, {'OPENAI_API_KEY':'environment-value'}):
            self.assertEqual(settings.get('OPENAI_API_KEY'),'environment-value')
        settings.save(self.root.name, {}, ['OPENAI_API_KEY'])
        self.assertFalse(settings.get('OPENAI_API_KEY'))

    def test_invalid_input_does_not_overwrite_existing_settings(self):
        settings.save(self.root.name, {'OPENAI_API_KEY':'kept'}, [])
        for data in ({'ATLAS_XBOX_TOKEN_FILE':'/nonexistent/file'}, {'ATLAS_PSN_NPSSO':'too-short'}, {'UNKNOWN':'x'}, {'ATLAS_AUTO_GUIDES':'yes'}):
            with self.assertRaises(ValueError):settings.save(self.root.name,data,[])
            self.assertEqual(settings.read(self.root.name)['OPENAI_API_KEY'],'kept')

    def test_controller_only_exposes_presence_and_blocks_busy_edits(self):
        c=Controller(self.root.name)
        c.save_settings({'values':{'OPENAI_API_KEY':'private-value'}})
        self.assertNotIn('private-value',json.dumps(c.status()))
        c.guide_guard.acquire()
        try:
            with self.assertRaises(ValueError):c.save_settings({'clear':['OPENAI_API_KEY']})
        finally:c.guide_guard.release()
        self.assertEqual(settings.get('OPENAI_API_KEY'),'private-value')

    def test_auto_guides_default_is_off(self):
        self.assertFalse(settings.status()['auto_guides'])
