"""Fail closed unless the exact push commit passed the complete test workflow."""
import json
import os
import re
import time
from urllib.request import Request,urlopen


def test_status(runs,commit):
    matches=[r for r in runs if r.get('head_sha')==commit and r.get('event')=='push'
             and r.get('head_branch')=='codex/public-profile-trophies'
             and r.get('path')=='.github/workflows/tests.yml']
    if not matches:return False
    latest=max(matches,key=lambda r:r['id'])
    if latest.get('status')!='completed':return False
    if latest.get('conclusion')!='success':raise ValueError('Exact-source test workflow did not pass')
    return True


def main():
    commit=os.environ['CANDIDATE_COMMIT'];repo=os.environ['GH_REPO']
    if repo!='Gh0sTRX/achievment-thropy-tracker' or not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Unexpected release source')
    request=Request(f'https://api.github.com/repos/{repo}/actions/runs?head_sha={commit}&event=push&per_page=100',
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','User-Agent':'Atlas-release-gate'})
    deadline=time.monotonic()+900
    while time.monotonic()<deadline:
        with urlopen(request,timeout=30) as response:result=json.load(response)
        if test_status(result['workflow_runs'],commit):
            print('Exact-source complete test workflow passed:',commit);return
        time.sleep(10)
    raise TimeoutError('Complete test workflow has not passed; publication refused')


if __name__=='__main__':main()
