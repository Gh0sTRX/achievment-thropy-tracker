# Achievement Atlas

**A local-first, open-source achievement companion for PC gamers.** Track your games, unlocks, next goals, and artwork in a console-inspired desktop interface. Xbox is the first supported platform; the data model is designed for future adapters, including PlayStation where legitimate access is available.

> **Status: v0.5 pre-release / community prototype.** CSV import and the local UI are tested. Direct Microsoft/Xbox sign-in, Xbox Live synchronization, and third-party artwork downloads require real accounts/network access and have **not** been end-to-end verified in this release. This is not affiliated with Microsoft, Xbox, Sony or TrueAchievements.

## What's working

- **Your account, not a hard-coded gamer profile:** start with a fictional four-game demo, or import your own earned and locked **TrueAchievements CSV** exports.
- **Discover your next goal:** transparent, rule-based recommendations; pinned targets, near-completion titles, higher Gamerscore possibilities, and warnings about achievements marked unavailable in the imported dataset.
- **Honest progress labels:** measurable per-achievement progress appears only if an API actually supplies current/target progress. TrueAchievements rarity ratios are **not** assumed to be difficulty or time estimates.
- **Xbox connection (experimental):** an optional [OpenXbox/xbox-webapi-python](https://github.com/OpenXbox/xbox-webapi-python) integration can open Microsoft sign-in, discover Title IDs, and query Xbox 360 / Xbox One achievements. It requires user authorization; API access and endpoint availability can change.
- **Artwork Studio:** optionally use your own SteamGridDB API key to choose game covers and hero images; cache images locally. Official Xbox achievement icon URLs are cached when available. No scraped artwork or proprietary assets ship in the repository.
- **Offline-first and private:** locally stored JSON library and preferences; server binds to `127.0.0.1` only. Your imported profile, account tokens and artwork cache are ignored by Git.

## Run on Windows

1. Install **Python 3.11+**.
2. Extract or clone the repository.
3. Double-click `BASLAT_TARAYICI.bat` to run in your default browser, or `BASLAT_WINDOWS.bat` for the optional native window (`pip install pywebview`).
4. Import your **earned and locked** TrueAchievements CSV files under the Import section.
5. To try the experimental Xbox connection, run `XBOX_BILESENINI_KUR.bat`, then use **Xbox / Microsoft sign-in** in the app.

Without any Xbox dependency, run:

```bash
python run.py --browser
```

OpenXbox is **optional**, and third-party sites can block automated requests. A standalone Xbox developer/API key is not needed for the OpenXbox OAuth path, but Microsoft might restrict its API access.

## Test

```bash
python -m unittest discover -s tests -v
node --check atlas/web/app.js   # optional JavaScript syntax check
```

The test suite runs with Python's standard library and uses temporary local data, not real accounts.

## Project structure

```text
atlas/
  core.py              # portable library, CSV import, persistence, guarded live updates
  recommendations.py   # auditable recommendation engine
  artwork.py           # allow-listed artwork providers, image cache
  xbox.py              # optional OpenXbox adapter / 360 and One models
  server.py            # localhost-only HTTP API and desktop window host
  web/                 # responsive HTML, JS, CSS
run.py                 # launcher
tests/                 # automated regression tests
.github/workflows/     # CI on Windows and Linux
```

## Roadmap / contributing

The next milestones are API sign-in verification against a **consenting tester account**, safe Xbox Title ID matching, a reliable licensed artwork pipeline, installable Windows builds, configurable recommendation rules, and a separate PlayStation provider if permitted by the platform's terms. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/PROVIDERS.md](docs/PROVIDERS.md).

We welcome issue reports and PRs. **Never submit passwords, session tokens, private achievement exports, or proprietary media files.**

## Downloads and Code signing policy

Windows builds will be published on [GitHub Releases](https://github.com/Gh0sTRX/achievment-thropy-tracker/releases). The project has **applied** to SignPath Foundation; **signing has not been approved or activated**. An EXE uploaded manually to a release is **unsigned** unless a valid signature is independently verified. A verifiable GitHub Actions release-build pipeline is still required before SignPath signing can begin.

- [**Code signing policy**](CODE_SIGNING_POLICY.md) — release provenance, approved artifacts, reviewer/approver roles and signing rules.
- [**Privacy Policy**](PRIVACY.md) — local storage, optional Xbox/Microsoft login, SteamGridDB and other external services.
- [Security policy](SECURITY.md) — local server and credential handling.

**Planned signed-release attribution (once approved):** Free code signing provided by SignPath.io, certificate by [SignPath Foundation](https://signpath.org/).

Release notes must also link to the Code signing policy and Privacy Policy and clearly state whether that specific EXE is signed or unsigned.

## Privacy and licensing

Data is saved to your user profile's local `AchievementAtlas` application-data folder. Microsoft login tokens, if you choose to use Xbox sign-in, are handled by the separate OpenXbox dependency and kept outside this repository. See [SECURITY.md](SECURITY.md).

Application code is **MIT licensed** ([LICENSE](LICENSE)). Xbox, PlayStation, game covers, achievement icons, and trademarks belong to their respective owners. Distributing code does not grant rights to redistribute those assets.