import unittest
from atlas.dates import normalize_unlock_date
from atlas.core import build_library

class DateTests(unittest.TestCase):
    def test_iso_and_timezone(self):
        self.assertEqual(normalize_unlock_date('2026-11-03'), '2026-11-03')
        self.assertEqual(normalize_unlock_date('2026-11-03T21:20:05Z'), '2026-11-03T21:20:05+00:00')
        self.assertEqual(normalize_unlock_date('2026-11-03 21:20:05+03:00'),'2026-11-03T21:20:05+03:00')

    def test_named_month_and_explicit_numeric(self):
        self.assertEqual(normalize_unlock_date('3 Nov 2026 at 9:10 PM'),'2026-11-03T21:10:00')
        self.assertEqual(normalize_unlock_date('November 3, 2026 09:10'),'2026-11-03T09:10:00')
        self.assertEqual(normalize_unlock_date('13/11/2026 14:20'),'2026-11-13T14:20:00')
        self.assertEqual(normalize_unlock_date('11/13/2026'),'2026-11-13')
        self.assertEqual(normalize_unlock_date('2026/11/03'),'2026-11-03')

    def test_never_infer_ambiguous_or_invalid_date(self):
        for value in ('03/11/2026','03/04/2026','2026-02-30','31 Feb 2026','12/12/26','yesterday',None):
            with self.subTest(value=value):
                self.assertEqual(normalize_unlock_date(value),'')

    def test_csv_import_preserves_original_and_normalizes(self):
        header='GameName,AchievementName,AchievementPageURL,Gamerscore,UnlockDate\n'
        url='https://www.trueachievements.com/a123/example-achievement'
        csv=header+f'Example,One,{url},10,3 Nov 2026 at 9:10 PM\n'
        x=build_library(csv,'')
        a=x['achievements'][0]
        self.assertEqual(a['unlock_time'],'2026-11-03T21:10:00')
        self.assertEqual(a['unlock_time_raw'],'3 Nov 2026 at 9:10 PM')

    def test_ambiguous_csv_preserved_but_excluded_from_timeline(self):
        csv=('GameName,AchievementName,AchievementPageURL,Gamerscore,UnlockDate\n'
             'Example,One,https://www.trueachievements.com/a123/example,10,03/04/2026\n')
        x=build_library(csv,'')
        a=x['achievements'][0]
        self.assertEqual(a['unlock_time'],'')
        self.assertEqual(a['unlock_time_raw'],'03/04/2026')

if __name__=='__main__':unittest.main()
