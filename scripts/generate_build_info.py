import json
import os
from pathlib import Path
Path('spec/build-info.json').write_text(json.dumps({'run_id':int(os.environ['GITHUB_RUN_ID']),
 'commit':os.environ['GITHUB_SHA'],'ref':os.environ['GITHUB_REF']}),encoding='utf-8')
