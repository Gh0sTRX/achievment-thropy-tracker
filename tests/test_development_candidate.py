import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from scripts.verify_development_candidate import verify_candidate
from test_development_updates import manifest


class CandidateTests(TestCase):
    def test_original_push_identity_is_preserved(self):
        with TemporaryDirectory() as temp:
            root=Path(temp); data=manifest()
            (root/'development-manifest.json').write_text(json.dumps(data))
            with patch('scripts.verify_development_candidate.verify_bundle', return_value={'verified':True}) as verify:
                self.assertTrue(verify_candidate(root, data['run_id'], data['source_commit'])['verified'])
                verify.assert_called_once_with(root/'update-bundle.json', data, root/data['installer'])

    def test_other_run_or_commit_is_rejected_before_promotion(self):
        with TemporaryDirectory() as temp:
            root=Path(temp); data=manifest()
            (root/'development-manifest.json').write_text(json.dumps(data))
            with patch('scripts.verify_development_candidate.verify_bundle') as verify:
                for run,commit in [(1,data['source_commit']),(data['run_id'],'b'*40)]:
                    with self.assertRaises(ValueError): verify_candidate(root,run,commit)
                verify.assert_not_called()
