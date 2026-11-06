import unittest
from scripts.require_release_tests import test_status


class ReleaseGateTests(unittest.TestCase):
    def row(self,**changes):
        return {**{'id':1,'head_sha':'a'*40,'head_branch':'codex/public-profile-trophies','event':'push','path':'.github/workflows/tests.yml','status':'completed','conclusion':'success'},**changes}
    def test_exact_source_success_required(self):
        self.assertTrue(test_status([self.row()],'a'*40))
        for changes in ({'head_sha':'b'*40},{'head_branch':'other'},{'event':'pull_request'},{'path':'.github/workflows/windows-package.yml'},{'status':'in_progress'}):
            self.assertFalse(test_status([self.row(**changes)],'a'*40))
        self.assertFalse(test_status([],'a'*40))
    def test_failed_or_cancelled_latest_run_refuses_publication(self):
        for result in ('failure','cancelled','skipped',None):
            with self.assertRaises(ValueError):test_status([self.row(),self.row(id=2,conclusion=result)],'a'*40)
