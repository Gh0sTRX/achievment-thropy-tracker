from enum import Enum
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from atlas import public_profiles as public

class PsnPartialTests(unittest.TestCase):
    def test_all_devices_and_discard_partial_title_rows(self):
        class Platform(Enum):PS3='PS3';PS4='PS4';PS5='PS5';VITA='PSVITA'
        titles=[NS(np_communication_id='NP'+str(i),title_platform={p},title_name=p.value,title_icon_url='') for i,p in enumerate(Platform)]
        trophy=NS(trophy_id=0,earned=True,earned_date_time=None,trophy_name='First',trophy_detail='',trophy_icon_url='',trophy_group_id='001',trophy_type=NS(value='gold'),progress=None,trophy_progress_target_value=None)
        def trophies(npid,*args,**kwargs):
            self.assertIsNone(kwargs['limit']);self.assertEqual(kwargs['trophy_group_id'],'all')
            yield trophy
            if npid=='NP1':raise RuntimeError('secret headers must not leak')
        user=NS(account_id='123',online_id='Player1',trophy_titles=lambda **kw:titles,trophies=trophies)
        sdk=NS(PSNAWP=lambda secret:NS(user=lambda **kw:user))
        with patch.dict('sys.modules',{'psnawp_api':sdk}),patch.object(public.settings,'get',return_value='service-session'):
            result=public.fetch('psn','Player1')
        self.assertEqual(len(result['games']),3);self.assertEqual(len(result['achievements']),3)
        self.assertEqual(result['failed_title_ids'],['NP1'])
        self.assertEqual({d for g in result['games'] for d in g['devices']},{'ps3','ps5','psvita'})
        self.assertNotIn('secret',str(result['warnings']))
