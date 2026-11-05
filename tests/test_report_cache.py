import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from atlas.server import Controller
from atlas import recommendations

class ReportCacheTests(unittest.TestCase):
    def test_reports_reuse_content_and_invalidate_for_pins_or_library(self):
        with TemporaryDirectory() as root:
            c=Controller(root)
            with patch.object(recommendations,'rank',wraps=recommendations.rank) as rank:
                first=c.status();second=c.status()
                self.assertEqual(rank.call_count,4)
                self.assertEqual(first['platform_reports'],second['platform_reports'])
                c.store.save();c.status();self.assertEqual(rank.call_count,4)
                c.store.state['pins']=['fixture-pin'];c.store.save();c.status();self.assertEqual(rank.call_count,8)
                c.store.library['gamertag']='Changed';c.store.save();c.status();self.assertEqual(rank.call_count,12)
