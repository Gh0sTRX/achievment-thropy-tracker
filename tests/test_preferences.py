import tempfile
import unittest
from atlas.core import Library, atomic_write
from atlas.preferences import validate

class PreferencesTests(unittest.TestCase):
    def test_migrate_persist_and_preserve_ids_and_pins(self):
        with tempfile.TemporaryDirectory() as d:
            s=Library(d);s.library['games']=[{'id':'xbox:360','platform':'xbox'},{'id':'psn:ps4','platform':'psn'}]
            s.state['pins']=['keep'];s.save()
            old=Library(d);old.set_preferences({'theme_mode':'psn','platform_filter':'all','focus_game_id':'xbox:360','library_layout':'collection','theme_skin':'xmb'})
            new=Library(d)
            self.assertEqual(new.state['ui']['theme_mode'],'psn');self.assertEqual(new.state['ui']['theme_skin'],'xmb');self.assertEqual(new.state['pins'],['keep'])
            self.assertEqual(new.library,old.library)
    def test_invalid_preferences_are_atomic(self):
        for values in ({'theme_mode':'demo'},{'theme_skin':'demo'},{'focus_game_id':'missing'},{'hero_contrast':float('nan')},{'font_scale':8},{'reduced_motion':'yes'},{'token':'secret'}):
            with self.assertRaises(ValueError):validate(values,[])
    def test_art_treatment_and_notes_survive_sync(self):
        from atlas.server import Controller
        with tempfile.TemporaryDirectory() as d:
            c=Controller(d);g={'id':'xgame','platform':'xbox','title_id':'123','name':'Fixture'}
            snap={'platform':'xbox','id':'1','username':'Test','synced_at':'2026-11-03','games':[g],'achievements':[]}
            c.store.apply_public_profile(snap)
            c.theme_art({'game_id':'xgame','theme':'auto','x':10,'y':80,'overlay':.8,'blur':3})
            c.save_notes({'game_id':'xgame','notes':'Local note <script>'})
            c.store.apply_public_profile(snap)
            saved=c.store.library['games'][0]
            self.assertEqual(saved['notes'],'Local note <script>');self.assertEqual(saved['art_theme']['overlay'],.8)
            for values in ({'overlay':float('nan')},{'blur':13}):
                with self.assertRaises(ValueError):c.theme_art({'game_id':'xgame',**values})
