import unittest
from atlas.artwork import safe_url,suffix
class ArtTests(unittest.TestCase):
    def test_allowlist(self):
        self.assertTrue(safe_url('https://cdn2.steamgriddb.com/asset.png'))
        self.assertTrue(safe_url('https://store-images.s-microsoft.com/image.jpg'))
        self.assertFalse(safe_url('https://xboxlive.com.evil.example/'))
        self.assertFalse(safe_url('http://localhost/private'))
        self.assertFalse(safe_url('https://127.0.0.1/private'))
        self.assertFalse(safe_url('https://user:pass@xboxlive.com/image.jpg'))
    def test_signature(self):
        self.assertEqual(suffix(b'\x89PNG\r\n\x1a\nabc'),'.png')
        self.assertEqual(suffix(b'NOT IMAGE'),None)
if __name__=='__main__':unittest.main()