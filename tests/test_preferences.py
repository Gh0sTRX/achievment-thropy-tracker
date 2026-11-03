import tempfile
import unittest
from atlas.core import Library, atomic_write
from atlas.preferences import validate

class PreferencesTests(unittest.TestCase):
    def test_migrate_persist_and_preserve_ids_and_pins(self):
        with tempfile.TemporaryDirectory() as d:
            s=Library(d);s.library['games']=[{'id':'xbox:360','platform':'xbox'},{'id':'psn:ps4','platform':'psn'}]
            s.state['pins']=['keep'];s.save()
            old=Library(d);old.set_preferences({'theme_mode':'psn','platform_filter':'all','focus_game_id':'xbox:360','library_layout':'collection'})
            new=Library(d)
            self.assertEqual(new.state['ui']['theme_mode'],'psn');self.assertEqual(new.state['pins'],['keep'])
            self.assertEqual(new.library,old.library)
    def test_invalid_preferences_are_atomic(self):
        for values in ({'theme_mode':'demo'},{'focus_game_id':'missing'},{'hero_contrast':float('nan')},{'font_scale':8},{'reduced_motion':'yes'},{'token':'secret'}):
            with self.assertRaises(ValueError):validate(values,[])
