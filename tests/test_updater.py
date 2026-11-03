import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from atlas import updater
from atlas.server import Controller


def release():
    tag='v99.0.0';name='AchievementAtlas-99.0.0-Windows-x64-Setup.exe'
    base=f'https://github.com/{updater.REPOSITORY}/releases/download/{tag}/'
    return {'tag_name':tag,'draft':False,'prerelease':False,'body':'Version notes',
            'assets':[{'name':n,'browser_download_url':base+n} for n in (name,'update-manifest.json')]}


def manifest(data=b'verified installer'):
    return {'schema':1,'repository':updater.REPOSITORY,'version':'99.0.0',
            'installer':'AchievementAtlas-99.0.0-Windows-x64-Setup.exe','signed':True,
            'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'signer_sha256':'a'*64}


def wait(manager):
    deadline=time.monotonic()+3
    while manager.guard.locked() and time.monotonic()<deadline:time.sleep(.005)
    assert not manager.guard.locked()


class ReleaseTests(unittest.TestCase):
    def test_numeric_versions_and_no_downgrade(self):
        self.assertGreater(updater.version('0.11.0'),updater.version('0.9.0'))
        self.assertIsNone(updater.release_info(release(),current='99.0.0'))
        self.assertIsNone(updater.release_info(release(),current='100.0.0'))
        for invalid in ('v1.2.3-beta','v1.2','../1.2.3','1.2.3.exe'):
            with self.assertRaises(ValueError):updater.version(invalid)

    def test_other_repo_and_prereleases_rejected(self):
        r=release();r['prerelease']=True
        with self.assertRaises(ValueError):updater.release_info(r)
        r=release();r['assets'][0]['browser_download_url']='https://github.com/other/repo/setup.exe'
        with self.assertRaises(ValueError):updater.release_info(r)

    def test_unsigned_bad_hash_and_wrong_version_manifest_rejected(self):
        info=updater.release_info(release())
        for key,value in [('signed',False),('version','0.1.0'),('sha256','bad'),('size',updater.MAX_INSTALLER+1),('repository','other/repo')]:
            with self.assertRaises(ValueError):updater.validate_manifest({**manifest(),key:value},info)

    def test_redirects_do_not_allow_private_or_arbitrary_hosts(self):
        self.assertTrue(updater.safe_url('https://release-assets.githubusercontent.com/file?token=opaque'))
        for url in ('https://127.0.0.1/file','http://github.com/file','https://github.com.evil.test/x','https://user:pass@github.com/x','https://github.com:444/x'):
            self.assertFalse(updater.safe_url(url))

    def test_tampered_download_is_deleted(self):
        with TemporaryDirectory() as root:
            path=Path(root)/'setup.exe'
            with patch.object(updater,'open_url',return_value=io.BytesIO(b'tampered')):
                with self.assertRaises(ValueError):updater.stream_installer('https://github.com/file',path,manifest())
            self.assertFalse(path.exists())

    def test_streamed_hash_match_succeeds(self):
        data=b'verified installer'
        with TemporaryDirectory() as root:
            path=Path(root)/'setup.exe'
            with patch.object(updater,'open_url',return_value=io.BytesIO(data)):
                updater.stream_installer('https://github.com/file',path,manifest(data))
            self.assertEqual(path.read_bytes(),data)


class UpdaterTests(unittest.TestCase):
    def test_available_release_and_signed_download(self):
        data=b'verified installer'
        with TemporaryDirectory() as root:
            u=updater.Updater(root,channel="stable")
            with patch.object(updater,'read_json',side_effect=[release(),manifest(data)]):u.check();wait(u)
            self.assertEqual(u.snapshot()['state'],'available')
            with patch.object(u,'supported_install',return_value=Path(root)),patch.object(updater,'verify_signature',return_value='a'*64),patch.object(updater,'open_url',return_value=io.BytesIO(data)):
                u.download();wait(u)
            self.assertEqual(u.snapshot()['state'],'ready')
            self.assertFalse(u.exit_requested.is_set())

    def test_different_publisher_blocks_before_download(self):
        with TemporaryDirectory() as root:
            u=updater.Updater(root,channel="stable");u.release=updater.release_info(release());u.manifest=manifest()
            with patch.object(u,'supported_install',return_value=Path(root)),patch.object(updater,'verify_signature',return_value='b'*64),patch.object(updater,'open_url') as network:
                u.download();wait(u)
            self.assertEqual(u.snapshot()['state'],'blocked');network.assert_not_called()
            self.assertIsNone(u.ready_path)

    def test_unsigned_current_app_cannot_bootstrap_publisher_trust(self):
        with TemporaryDirectory() as root:
            u=updater.Updater(root,channel="stable");u.release=updater.release_info(release());u.manifest=manifest()
            with patch.object(u,'supported_install',return_value=Path(root)),patch.object(updater,'verify_signature',side_effect=ValueError('Unsigned')),patch.object(updater,'open_url') as network:
                u.download();wait(u)
            self.assertEqual(u.snapshot()['state'],'blocked');network.assert_not_called()

    def test_unsigned_manifest_never_becomes_available(self):
        with TemporaryDirectory() as root:
            u=updater.Updater(root,channel="stable")
            with patch.object(updater,'read_json',side_effect=[release(),{**manifest(),'signed':False}]):u.check();wait(u)
            self.assertEqual(u.snapshot()['state'],'error')
            self.assertIsNone(u.release)

    def test_offline_check_keeps_library_and_process_alive(self):
        with TemporaryDirectory() as root:
            c=Controller(root);before=json.dumps(c.store.payload())
            with patch.object(updater,'read_json',side_effect=OSError('offline')):c.updates.check();wait(c.updates)
            self.assertEqual(c.updates.snapshot()['state'],'error')
            self.assertEqual(json.dumps(c.store.payload()),before)
            self.assertFalse(c.updates.exit_requested.is_set())

    def test_busy_sync_blocks_restart(self):
        with TemporaryDirectory() as root:
            c=Controller(root);c.allow_update_install=True;c.public_guard.acquire()
            try:
                with patch.object(c.updates,'install') as install:
                    with self.assertRaises(ValueError):c.install_update()
                    install.assert_not_called()
            finally:c.public_guard.release()
