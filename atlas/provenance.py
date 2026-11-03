"""Certificate-free development updates authenticated by GitHub OIDC + Sigstore."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

REPOSITORY='Gh0sTRX/achievment-thropy-tracker'
WORKFLOW='.github/workflows/windows-package.yml'
TRUSTED_REFS=('refs/heads/codex/public-profile-trophies','refs/heads/main')
ROOT_SHA256='6494e21ea73fa7ee769f85f57d5a3e6a08725eae1e38c755fc3517c9e6bc0b66'


def build_info():
    try:
        raw=json.loads((Path(__file__).resolve().parent.parent/'spec'/'build-info.json').read_text())
        return {'run_id':int(raw['run_id']),'commit':str(raw['commit'])}
    except (OSError,ValueError,KeyError,TypeError):return {'run_id':0,'commit':''}


def verifier():
    from sigstore.models import TrustedRoot
    from sigstore.verify import Verifier
    root=Path(__file__).resolve().parent.parent/'spec'/'sigstore-trusted-root.json'
    if hashlib.sha256(root.read_bytes()).hexdigest()!=ROOT_SHA256:
        raise ValueError('Güncelleme güven kökü değiştirilmiş; doğrulama iptal edildi.')
    return Verifier(trusted_root=TrustedRoot.from_file(str(root)))


def validate_statement(statement,manifest):
    if statement.get('_type')!='https://in-toto.io/Statement/v1' or statement.get('predicateType')!='https://slsa.dev/provenance/v1':
        raise ValueError('Güncellemenin köken kanıtı türü geçersiz.')
    matching=[s for s in statement.get('subject',[]) if PurePosixPath(str(s.get('name','')).replace('\\','/')).name==manifest['installer'] and s.get('digest',{}).get('sha256')==manifest['sha256']]
    if len(matching)!=1:raise ValueError('Köken kanıtı indirilen kurulum dosyasına ait değil.')
    predicate=statement.get('predicate',{});definition=predicate.get('buildDefinition',{})
    workflow=definition.get('externalParameters',{}).get('workflow',{})
    if definition.get('buildType')!='https://actions.github.io/buildtypes/workflow/v1' or workflow.get('repository')!='https://github.com/'+REPOSITORY or workflow.get('path')!=WORKFLOW or workflow.get('ref') not in TRUSTED_REFS:
        raise ValueError('Güncelleme yetkili GitHub deposunda/workflow dalında üretilmemiş.')
    github=definition.get('internalParameters',{}).get('github',{})
    if str(github.get('repository_id'))!='1444083648' or str(github.get('repository_owner_id'))!='118396811' or github.get('event_name')!='push' or github.get('runner_environment')!='github-hosted':
        raise ValueError('GitHub derleme kimliği beklenen geliştirme kanalına ait değil.')
    run=predicate.get('runDetails',{}).get('metadata',{}).get('invocationId','')
    if not re.fullmatch(r'https://github\.com/'+re.escape(REPOSITORY)+r'/actions/runs/'+str(manifest['run_id'])+r'/attempts/\d+',run):
        raise ValueError('Derleme numarası köken kanıtıyla eşleşmiyor.')
    dependencies=definition.get('resolvedDependencies',[])
    if not any(d.get('digest',{}).get('gitCommit')==manifest['source_commit'] and d.get('uri')=='git+https://github.com/'+REPOSITORY+'@'+workflow['ref'] for d in dependencies):
        raise ValueError('Kaynak commit bilgisi köken kanıtıyla eşleşmiyor.')
    return {'verified':True,'run_id':manifest['run_id'],'commit':manifest['source_commit'],'workflow_ref':workflow['ref'],'sha256':manifest['sha256']}


def verify_bundle(bundle_path,manifest,installer=None):
    try:
        from sigstore.models import Bundle
        from sigstore.verify.policy import AnyOf,Identity
        if bundle_path.stat().st_size>512_000:raise ValueError('Köken kanıtı çok büyük.')
        bundle=Bundle.from_json(bundle_path.read_bytes())
        policy=AnyOf([Identity(identity=f'https://github.com/{REPOSITORY}/{WORKFLOW}@{ref}',issuer='https://token.actions.githubusercontent.com') for ref in TRUSTED_REFS])
        payload_type,payload=verifier().verify_dsse(bundle,policy)
        if payload_type!='application/vnd.in-toto+json':raise ValueError('Beklenmeyen imzalı içerik türü.')
        result=validate_statement(json.loads(payload),manifest)
        if installer is not None:
            if installer.stat().st_size!=manifest['size']:raise ValueError('Kurulum boyutu değişmiş.')
            with installer.open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
            if digest!=manifest['sha256']:raise ValueError('Kurulum içeriği köken kanıtıyla eşleşmiyor.')
        return result
    except ValueError:raise
    except Exception as exc:
        raise ValueError('GitHub derleme imzası doğrulanamadı: '+type(exc).__name__) from None
