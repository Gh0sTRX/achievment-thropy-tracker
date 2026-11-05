# Code signing policy — Achievement Atlas

**Status (November 3, 2026): Application submitted to SignPath Foundation; approval and production signing are pending.** No existing release should be described as SignPath-signed unless its Authenticode signature has actually been verified.

> Free code signing provided by SignPath.io, certificate by [SignPath Foundation](https://signpath.org/).

This attribution describes the **intended provider if the application is accepted**, not an assertion that SignPath has already signed any binary. SignPath Foundation will appear as the signing publisher, not the individual developer, for any successfully signed releases under that certificate.

## Scope: which artifacts may be signed

- Only **Achievement Atlas Windows application executables or installers** produced from the public source and build scripts of [Gh0sTRX/achievment-thropy-tracker](https://github.com/Gh0sTRX/achievment-thropy-tracker) are eligible.
- Only a reproducible, provenance-verifiable **GitHub Actions release build**, running on a trusted GitHub-hosted runner from an identifiable release tag or approved commit, may be submitted to SignPath.
- The [unit workflow](.github/workflows/tests.yml) and [Windows packaging workflow](.github/workflows/windows-package.yml) now test and build the v0.15.1 application and subsequent unreleased source, native window, installer and uninstall path. Packaging can optionally use a configured trusted Authenticode certificate; it is **not an approved SignPath Foundation workflow**. SignPath-specific configuration, review and approval are still pending.
- Manually compiled or manually uploaded EXE files may be published as **unsigned preliminary releases**, but must **not** be represented as verified SignPath builds and must not be submitted for Foundation signing without an approved origin-verification pipeline.
- Third-party applications, game binaries, commercial artwork, bundled upstream runtime components and files downloaded by users are not signed as if they were original Achievement Atlas code. The provenance and license of all packaged dependencies must be reviewed.

## Existing development updates versus Windows signing

The `development` prerelease channel uses GitHub OIDC/Sigstore SLSA build provenance,
validated against a bundled, pinned production trust root and fixed repository,
owner, workflow, allowed push refs, commit/run and installer digest. Its manifest
is distinct from the stable Authenticode manifest. This proves accepted build
origin and byte identity; it does **not** give the EXE a trusted Windows publisher
certificate, establish malware-free behavior or imply SignPath approval.

The existing workflow can automatically publish development artifacts after its
checks on trusted development/main push refs; PR builds do not publish. Versioned
stable publication additionally requires a valid Authenticode-signed installer.
SignPath's manual approval rules below apply if/when SignPath signing is configured;
they are not a claim that current development uploads were approved by SignPath.
Inspect each artifact's actual `signed` / `authenticode_signed` report. A future
non-SignPath certificate's real publisher must be reported accurately as well.
This audit creates only a review branch/PR and validation artifacts, **no new Release**.

## Maintainer and signing roles

The project is presently maintained under the GitHub account [@Gh0sTRX](https://github.com/Gh0sTRX). Roles are assigned as follows until an explicit public policy revision:

| Role | Member | Responsibility |
| --- | --- | --- |
| **Committer / author** | [@Gh0sTRX](https://github.com/Gh0sTRX) | Owns the official repository, writes and merges trusted source and build changes. |
| **Reviewer** | [@Gh0sTRX](https://github.com/Gh0sTRX) | Reviews incoming contributions and build/release changes before merging. |
| **Signing approver** | [@Gh0sTRX](https://github.com/Gh0sTRX) | Independently checks release provenance, tests, dependencies and signing requests before approving each release in SignPath. |

Contributor changes not directly authored by the trusted committer require review before merge. The maintainer must enable and maintain **multi-factor authentication** for GitHub and SignPath. Roles and account membership must be updated here whenever the team changes.

## Release and signing requirements (when approved)

1. Changes enter the public repository through reviewed commits. Review release scripts, build dependencies, permissions and workflow changes especially carefully.
2. A versioned release tag points to the exact public commit used by the trusted GitHub Actions build workflow. Source, build logs and artifacts must be traceable to that commit.
3. Automated Python and JavaScript checks must pass, and the produced Windows EXE/installer must be tested. The build must not introduce malware, unwanted programs, undocumented data collection, proprietary source code or licensing violations.
4. SignPath's trusted build-system verification and **origin verification** must be enabled. Artifact configuration must enforce the product name **Achievement Atlas** and coherent version metadata across every submitted artifact.
5. Each signing request is reviewed and **manually approved** by the named signing approver. No automatic approval is allowed.
6. Only then should the signed artifact be published to the [GitHub Releases page](https://github.com/Gh0sTRX/achievment-thropy-tracker/releases) with the source revision, version, checksum and clear signature status. Verify the resulting Authenticode publisher and signature before announcing it as signed.
7. Each release page must link to this **Code signing policy** and the [Privacy Policy](PRIVACY.md). Signed releases should include the exact attribution: **"Free code signing provided by SignPath.io, certificate by SignPath Foundation"**.

All SignPath-related policies and restrictions, including any certificate suspension or revocation, apply. If a suspected signing or distribution violation is reported, the maintainer will investigate and coordinate with SignPath Foundation.

## Privacy

[Achievement Atlas Privacy Policy](PRIVACY.md).

The application is local-first. It does not send personal information to external systems during ordinary offline use; network communications include startup GitHub update checks, reconnect/sync with saved Xbox access, post-sync artwork retrieval, explicit public Xbox/PSN lookups, optional Brave/OpenAI guide calls, and opened external links. Automatic guide generation requires the explicit preference in the audited code. See the privacy policy for actual data fields, credential storage, provider billing and deletion controls.

## For users verifying downloads

- Until a release explicitly states it has been signed **and** that signature verifies, treat it as **unsigned**.
- An EXE signed under an approved SignPath Foundation configuration should show its actual valid Authenticode publisher; **SignPath Foundation** is the intended publisher under that program, not a claim about current unsigned artifacts. A GitHub release upload alone is not evidence of code signing.
- Prefer assets from the [official Releases page](https://github.com/Gh0sTRX/achievment-thropy-tracker/releases), compare published SHA-256 checksums, and inspect the linked source commit and CI history.
- Windows SmartScreen or other security prompts may still occur; code signing is not a malware-free guarantee.

## Reporting concerns

Report suspected compromise or signing-policy breaches to the maintainer via [SECURITY.md](SECURITY.md). If a SignPath Foundation certificate appears to have been misused, [SignPath Foundation's terms](https://signpath.org/terms) explain its reporting process.

**Official project:** https://github.com/Gh0sTRX/achievment-thropy-tracker
