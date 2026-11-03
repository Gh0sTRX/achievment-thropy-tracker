"""Reverify an existing push artifact before manual promotion; never rebuild it."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atlas.provenance import verify_bundle
from atlas.updater import validate_development_manifest


def verify_candidate(root, run_id, commit):
    root = Path(root)
    manifest = validate_development_manifest(json.loads((root/'development-manifest.json').read_text(encoding='utf-8')))
    if manifest['run_id'] != int(run_id) or manifest['source_commit'] != commit:
        raise ValueError('Candidate does not match the selected push run and commit')
    return verify_bundle(root/'update-bundle.json', manifest, root/manifest['installer'])


if __name__ == '__main__':
    print(json.dumps(verify_candidate(sys.argv[1], os.environ['CANDIDATE_RUN_ID'], os.environ['CANDIDATE_COMMIT'])))
