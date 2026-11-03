# Achievement Atlas

**A local-first, open-source Windows achievement and trophy companion.** Achievement Atlas brings your recorded Xbox and PlayStation activity into a cinematic desktop interface with game libraries, achievement details, a Quest Board, a collection museum, and user-chosen *real* game artwork.

> **Development build v0.14.1 (pre-release).** The core import and UI have automated test coverage. Network-dependent Xbox and PSN public-profile adapters require a separately authorized operator session and have **not** been verified end-to-end with a real target account. PC/Steam achievements remain **planned**; platform filters do not imply a live account integration. This is an independent community project, not affiliated with Microsoft, Sony, Valve, TrueAchievements or SignPath.

## What works in the source

- **TrueAchievements CSV import** for Xbox earned and locked achievement exports, including cautious date normalization and local backup/migration protections.
- **Experimental live Xbox (OpenXbox) and PlayStation (PSNAWP) adapters:** public-profile queries via an operator-owned authenticated session, subject to provider availability, permissions and rate limits. No tokens or production credentials are bundled.
- **Atlas Ultimate v5.1:** Cinematic / Blades-inspired / NXE-inspired / XMB-inspired looks, platform-separated library, Game Universe, pinned goals, Hall of Fame, timeline and optional keyboard/gamepad-oriented Console Mode.
- **Artwork Studio:** choose real game cover/hero/logo art via user files, verified Xbox/PSN candidate URLs or optional SteamGridDB search. Artwork is cached locally; copyrighted game images are not bundled.
- **Optional Turkish achievement notes:** source-linked Brave Search + OpenAI summaries. **Automatic paid-provider calls are disabled by default and need explicit consent.** Manual generation is a separate action. Source-linked summaries are not guaranteed correct.
- **Local data and privacy:** data is stored in your user's app-data area; the local interface binds to `127.0.0.1`; Windows service credentials configured through the app use DPAPI protection. See [PRIVACY.md](PRIVACY.md) for the exact scope and exceptions.

## Installation

Download the latest verified **development pre-release** from [GitHub Releases](https://github.com/Gh0sTRX/achievment-thropy-tracker/releases/tag/development). The Windows Setup.exe is built by GitHub Actions on Windows; it does not require a separate Python installation. Read [KURULUM.txt](KURULUM.txt) and [README_TR.md](README_TR.md).

For source development, use Python 3.11+:

```sh
python -m pip install -r requirements-platforms.txt
python run.py --browser
python -m unittest discover -s tests -v
node tests/test_ui_model.cjs
node tests/test_art_transition.cjs
```

SDKs and image-processing dependencies are optional for some offline workflows. Real Xbox/PSN provider access is not part of automated CI.

## Build and update trust

The Windows build workflow uses PyInstaller + Inno Setup, runs regression and native installer checks and verifies GitHub OIDC/Sigstore provenance before publishing the **development** update channel. This does **not** provide a trusted Windows Authenticode publisher signature or guarantee freedom from malware. SignPath Foundation application is pending; do not assume approved signing. Stable automatic updates require a separately trusted signing certificate.

The development updater verifies SHA-256, attested build identity and authorized GitHub workflow/source. See [docs/UPDATES_TR.md](docs/UPDATES_TR.md), [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md) and [docs/WINDOWS_DOWNLOAD_TR.md](docs/WINDOWS_DOWNLOAD_TR.md).

## Release and technical audit

- [0.14.1 release notes (TR)](docs/RELEASE_NOTES_0_14_1_TR.md)
- [Ultimate v5.1 audit and remaining work (TR)](docs/ATLAS_V5_1_INTEGRATION_AUDIT_TR.md)
- [Xbox/PSN public-profile setup and limits (TR)](docs/PUBLIC_PROFILES_TR.md)
- [Privacy Policy](PRIVACY.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

The project code is MIT licensed. Trademarks and third-party game images remain the property of their owners. Never upload real OAuth tokens, NPSSO secrets, private profile exports, proprietary media, or API keys to public issues or commits.
