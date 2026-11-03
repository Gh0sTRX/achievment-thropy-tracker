from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from atlas import updater,provenance
from test_updater import wait


def manifest():
    import hashlib
    return {'schema':2,'channel':'development','auth':'github-attestation','repository':updater.REPOSITORY,
       'version':'99.0.0','installer':'AchievementAtlas-99.0.0-Windows-x64-Setup.exe',
       'sha256':hashlib.sha256(b'installer').hexdigest(),'size':9,'run_id':123456,'source_commit':'a'*40,'authenticode_signed':False}


def statement():
    m=manifest();ref='refs/heads/codex/public-profile-trophies'
    return {'_type':'https://in-toto.io/Statement/v1','predicateType':'https://slsa.dev/provenance/v1',
       'subject':[{'name':m['installer'],'digest':{'sha256':m['sha256']}}],
       'predicate':{'buildDefinition':{'buildType':'https://actions.github.io/buildtypes/workflow/v1',
          'externalParameters':{'workflow':{'repository':'https://github.com/'+updater.REPOSITORY,'path':provenance.WORKFLOW,'ref':ref}},
          'internalParameters':{'github':{'repository_id':'1444083648','repository_owner_id':'118396811','event_name':'push','runner_environment':'github-hosted'}},
          'resolvedDependencies':[{'uri':'git+https://github.com/'+updater.REPOSITORY+'@'+ref,'digest':{'gitCommit':'a'*40}}]},
          'runDetails':{'metadata':{'invocationId':'https://github.com/'+updater.REPOSITORY+'/actions/runs/123456/attempts/1'}}}}


def release():
    base='https://github.com/'+updater.REPOSITORY+'/releases/download/development/'
    return {'tag_name':'development','prerelease':True,'draft':False,'assets':[{'name':n,'browser_download_url':base+n} for n in [manifest()['installer'],'development-manifest.json','update-bundle.json']]}


class DevelopmentTests(unittest.TestCase):
    def test_unsigned_windows_artifact_requires_github_attestation_contract(self):
        self.assertFalse(updater.validate_development_manifest(manifest())['authenticode_signed'])
        for key,value in [('auth','none'),('repository','other/repo'),('source_commit','bad'),('installer','other.exe')]:
            with self.assertRaises(ValueError):updater.validate_development_manifest({**manifest(),key:value})

    def test_same_version_requires_newer_attested_run(self):
        self.assertIsNotNone(updater.development_info(release(),manifest(),current='99.0.0',current_run=123455))
        self.assertIsNone(updater.development_info(release(),manifest(),current='99.0.0',current_run=123456))
        self.assertIsNone(updater.development_info(release(),manifest(),current='100.0.0',current_run=0))

    def test_statement_binds_subject_repo_branch_commit_and_run(self):
        self.assertTrue(provenance.validate_statement(statement(),manifest())['verified'])
        cases=[]
        s=statement();s['subject'][0]['digest']['sha256']='0'*64;cases.append(s)
        s=statement();s['predicate']['buildDefinition']['externalParameters']['workflow']['ref']='refs/heads/other';cases.append(s)
        s=statement();s['predicate']['buildDefinition']['internalParameters']['github']['repository_id']='1';cases.append(s)
        s=statement();s['predicate']['buildDefinition']['internalParameters']['github']['event_name']='pull_request';cases.append(s)
        s=statement();s['predicate']['buildDefinition']['internalParameters']['github']['event_name']='workflow_dispatch';cases.append(s)
        s=statement();s['predicate']['runDetails']['metadata']['invocationId']='https://github.com/'+updater.REPOSITORY+'/actions/runs/999/attempts/1';cases.append(s)
        for s in cases:
            with self.assertRaises(ValueError):provenance.validate_statement(s,manifest())

    def test_invalid_bundle_is_rejected_by_real_verifier(self):
        with TemporaryDirectory() as root:
            bundle=Path(root)/'bundle.json';bundle.write_text('{}')
            with self.assertRaises(ValueError):provenance.verify_bundle(bundle,manifest())

    def test_production_root_loads_without_network_or_user_cache(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            self.assertIsNotNone(provenance.verifier())

    def test_development_download_verifies_proof_before_binary(self):
        with TemporaryDirectory() as root:
            u=updater.Updater(root)
            with patch.object(updater,'read_json',side_effect=[release(),manifest()]):u.check();wait(u)
            self.assertEqual(u.snapshot()['state'],'available')
            with patch.object(u,'supported_install',return_value=Path(root)),patch.object(updater,'read_json',return_value={}),patch.object(provenance,'verify_bundle',side_effect=ValueError('Untrusted proof')),patch.object(updater,'open_url') as network:
                u.download();wait(u)
            network.assert_not_called();self.assertEqual(u.snapshot()['state'],'blocked')

    def test_provenance_verified_download_needs_no_authenticode(self):
        with TemporaryDirectory() as root:
            u=updater.Updater(root)
            with patch.object(updater,'read_json',side_effect=[release(),manifest()]):u.check();wait(u)
            with patch.object(u,'supported_install',return_value=Path(root)),patch.object(updater,'read_json',return_value={}),patch.object(provenance,'verify_bundle',return_value={'verified':True}),patch.object(updater,'open_url',return_value=io.BytesIO(b'installer')),patch.object(updater,'verify_signature',side_effect=AssertionError('Development does not need PKI')):
                u.download();wait(u)
            self.assertEqual(u.snapshot()['state'],'ready')
            self.assertIsNotNone(u.proof_path)
