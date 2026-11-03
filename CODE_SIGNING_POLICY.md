# Code signing policy — Achievement Atlas

**Status (November 3, 2026): Application submitted to SignPath Foundation; approval and production signing are pending.** No existing release should be described as SignPath-signed unless its Authenticode signature has actually been verified.

> Free code signing provided by SignPath.io, certificate by [SignPath Foundation](https://signpath.org/).

This attribution describes the **intended provider if the application is accepted**, not an assertion that SignPath has already signed any binary. SignPath Foundation will appear as the signing publisher, not the individual developer, for any successfully signed releases under that certificate.

## Scope: which artifacts may be signed

- Only **Achievement Atlas Windows application executables or installers** produced from the public source and build scripts of [Gh0sTRX/achievment-thropy-tracker](https://github.com/Gh0sTRX/achievment-thropy-tracker) are eligible.
- Only a reproducible, provenance-verifiable **GitHub Actions release build**, running on a trusted GitHub-hosted runner from an identifiable release tag or approved commit, may be submitted to SignPath.
- The current [GitHub Actions test workflow](.github/workflows/tests.yml) tests the project; **it is not yet a production EXE build-and-sign workflow**. A separate audited release workflow and SignPath configuration must be created before requesting production signatures.
- Manually compiled or manually uploaded EXE files may be published as **unsigned preliminary releases**, but must **not** be represented as verified SignPath builds and must not be submitted for Foundation signing without an approved origin-verification pipeline.
- Third-party applications, game binaries, commercial artwork, bundled upstream runtime components and files downloaded by users are not signed as if they were original Achievement Atlas code. The provenance and license of all packaged dependencies must be reviewed.

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

The application is local-first. It does not send personal information to external systems during ordinary offline use; network communications occur when the user explicitly starts Microsoft/Xbox login or sync, artwork retrieval, or opens external links. See the privacy policy for the exact data stored locally, token handling and third-party providers (Microsoft, OpenXbox, SteamGridDB, TrueAchievements).

## For users verifying downloads

- Until a release explicitly states it has been signed **and** that signature verifies, treat it as **unsigned**.
- A signed Windows EXE should show a valid Authenticode signature with **SignPath Foundation** as publisher. A GitHub release upload alone is not evidence of code signing.
- Prefer assets from the [official Releases page](https://github.com/Gh0sTRX/achievment-thropy-tracker/releases), compare published SHA-256 checksums, and inspect the linked source commit and CI history.
- Windows SmartScreen or other security prompts may still occur; code signing is not a malware-free guarantee.

## Reporting concerns

Report suspected compromise or signing-policy breaches to the maintainer via [SECURITY.md](SECURITY.md). If a SignPath Foundation certificate appears to have been misused, [SignPath Foundation's terms](https://signpath.org/terms) explain its reporting process.

**Official project:** https://github.com/Gh0sTRX/achievment-thropy-tracker
