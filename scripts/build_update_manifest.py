"""Generate the release contract after final installer signing."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from atlas import __version__
from atlas.updater import REPOSITORY, verify_signature

installer=Path(sys.argv[1])
if installer.name!=f'AchievementAtlas-{__version__}-Windows-x64-Setup.exe':
    raise SystemExit('Installer/version mismatch')
try:
    signer=verify_signature(installer)
    signed=True
except ValueError:
    signer=None;signed=False
with installer.open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
manifest={'schema':1,'repository':REPOSITORY,'version':__version__,'installer':installer.name,
          'size':installer.stat().st_size,'sha256':digest,'signed':signed,'signer_sha256':signer}
(installer.parent/'update-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Update manifest:',__version__,'signed='+str(signed))
