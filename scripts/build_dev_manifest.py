import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from atlas.provenance import REPOSITORY,verify_bundle

root=Path(sys.argv[1]);stable=json.loads((root/'update-manifest.json').read_text())
installer=root/stable['installer']
with installer.open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
manifest={'schema':2,'channel':'development','auth':'github-attestation','repository':REPOSITORY,
 'version':stable['version'],'installer':installer.name,'size':installer.stat().st_size,'sha256':digest,
 'run_id':int(os.environ['GITHUB_RUN_ID']),'source_commit':os.environ['GITHUB_SHA'],'authenticode_signed':stable['signed']}
(root/'development-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
result=verify_bundle(root/'update-bundle.json',manifest,installer)
(root/'development-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Verified development build',result['run_id'],result['commit'])
