# Privacy Policy — Achievement Atlas

**Reviewed source:** v0.14.0 / Ultimate v5.1 audit, November 3, 2026.
**Project:** [Gh0sTRX/achievment-thropy-tracker](https://github.com/Gh0sTRX/achievment-thropy-tracker).
This describes the source in this audit branch. The already published 0.14 binary
is not updated merely by editing this document; in particular, its automatic-guide
consent defect is corrected here and requires a later reviewed application update.

## Local-first storage and network behavior

The application runs a Python HTTP server on `127.0.0.1` and displays it in a native
WebView2 window or an explicitly selected browser. It has no maintainer-hosted
library service, built-in advertising or analytics. Local HTTP is not encrypted;
a per-process token and Host/Origin checks protect write operations. This is not
protection from malware running as your Windows user or a professional security audit.

Offline CSV use needs no account or API key. Network activity is **not limited to
a single button click**: startup checks GitHub for updates; a saved linked Xbox
session can reconnect/synchronize on startup; successful profile sync queues missing
artwork downloads. Public-profile lookup, login, guide generation and artwork search
also make the provider requests below. Remote image URLs rendered by the UI and
external links can contact their hosts from the browser/WebView itself.

## Data stored on your device

The default application folder is `%LOCALAPPDATA%\AchievementAtlas` on Windows
(with `%APPDATA%` as a fallback); on other systems it uses `$XDG_DATA_HOME` or
`~/.local/share/` under `AchievementAtlas`. `--data-dir` can select another folder.

- `library.json`: game/provider/title/edition identities, achievement names,
  descriptions, IDs, points or trophy tiers, earned state, available unlock dates,
  original CSV date text when retained, measured progress, source URLs, notes and
  generated Turkish guide notes with cited snippets/URLs/model/timestamp.
- `state.json`: pinned targets, appearance settings, mapped title IDs, linked
  profile identity, target-profile identities and sync timestamps/warnings.
- `profiles/*.json`: local snapshots of previously queried public profiles and
  their games/achievements. Changing profile does not erase these histories.
- `artwork/`: validated cached game art and achievement icons, including user files;
  library metadata records sources and optional crop/lighting choices. Cached
  filenames do not prove a redistribution licence.
- `settings.json`: supported operator settings described below. Library JSON, notes,
  history, artwork, migration backups and update files are not encrypted by DPAPI.
- Migration backups (including `migration-v014-library.json` / `migration-v014-state.json`)
  preserve original files before normalization. They contain the original personal
  records and have the same retention considerations as the library.
- `updates/`: downloaded installers, manifests, provenance bundles, plans, update
  logs and backups of installed application files. These can consume disk space.

The Classic UI uses local JSON preferences. Optional Ultimate V5 cosmetic preferences
(mode, view, selected game/art adjustments) use a separate `localStorage` key,
`achievement-atlas-ultimate-v5`; it contains no OAuth/session/API keys. Storage depends
on the WebView/browser origin and session and is not the source of achievement truth.

## Providers and exactly what is sent

| Provider / feature | Information sent or requested | Storage / limits |
| --- | --- | --- |
| Microsoft OAuth and Xbox Live through OpenXbox | Microsoft authorization flow in your browser; OAuth code exchange, token refresh and XSTS requests; service account XUID; requested Gamertag/XUID, title IDs, achievement history/catalog/progress requests | The app does not ask for your Microsoft password. OpenXbox OAuth/refresh tokens are in its user-local JSON token file (or an operator-selected file), separate from the library. That token file is **not** covered by the app's settings DPAPI wrapper. The installed SDK can also read its own configured token path. |
| Public Xbox profile lookup | Target Gamertag resolved to a target XUID; target title history and achievements, using the operator's authorized service session | The target user does not supply a password; public visibility and service permissions/rate limits still apply. Service identity and target identity may differ. |
| Sony/PlayStation via PSNAWP | Operator NPSSO session used for PSN authentication; target Online ID/account ID; trophy title/communication IDs and trophy-group/progress queries | NPSSO is a sensitive service credential. Only data exposed to that session is available; a public profile does not remove authentication requirements. No target password is requested. |
| Brave Search (Turkish guides) | Search text containing game name, achievement/trophy name, device and edition plus the search API key in its authorization header | Queries are sent to `api.search.brave.com`. Returned titles, URLs and snippets are used as evidence; the app does not mirror a full guide site. |
| OpenAI (Turkish guides) | Configured model, game name, platform/device/edition, game title ID, achievement name, its description/condition, and Brave source titles/URLs/snippets; API key in authorization header | Sent to `api.openai.com`. The request builder does not intentionally include Gamertag, XUID, NPSSO, OAuth tokens, the full CSV/library, personal notes or unlock history. A name/description you supplied could itself contain personal information. |
| SteamGridDB | API key in authorization header; game-name search and selected SteamGridDB ID for cover/hero/logo choices; image requests | Key is held in process memory for that session, not persisted by the app's settings endpoint. Selection requires user confirmation of the matching game/edition. |
| Other artwork hosts | Image URL/path from an allowed provider, IP address and normal HTTP headers | Xbox/Microsoft, PlayStation, SteamGridDB and allowed community artwork hosts can be contacted. Images may be downloaded after sync or displayed remotely. Server downloads have host/redirect and size checks; browser-rendered images also disclose a normal request to the host. |
| GitHub update checks/downloads | Standard HTTPS request metadata, application User-Agent/version, fixed repository/channel URLs and requested assets | Startup checks `api.github.com`; installer, manifest and provenance assets use GitHub release/CDN hosts. No library, profile export or service keys are uploaded by the updater. Provenance validation uses a bundled Sigstore trust root offline; it does not upload your library to Sigstore. |
| External guide/source links | Opening a link sends a browser request to that site under its own policies | User action; the application does not control that site's cookies, logs or retention. |

Provider retention, billing and account controls are governed by the providers'
policies and your agreements with them. This project does not promise that a
third-party provider retains no queries or images. The PC provider interface currently
implements Steam Web API, requiring an operator's `ATLAS_STEAM_API_KEY`. SteamID64 or
vanity name, AppIDs and the service key are sent over HTTPS to `api.steampowered.com`
for ResolveVanityURL, GetOwnedGames, GetSchemaForGame and GetPlayerAchievements.
The key is stored using the same Windows DPAPI settings protection and is excluded
from library exports and browser status. Game names, achievement descriptions,
unlock timestamps and icon URLs returned by Steam enter the local JSON archive.
AppID-bound image candidates may contact Steam CDN hosts (`steamstatic.com` and
listed Akamai CDN hosts). These images are not redistributed with the application.
No user credentials were available for live Steam verification during this audit;
mock integration coverage does not establish real-account access.

## Automatic guides, explicit consent and cost

In this audit's corrected code, `ATLAS_AUTO_GUIDES` defaults to off. Merely saving
Brave and OpenAI keys does not authorize automatic paid calls. Enabling the visible
checkbox and saving settings (or explicitly setting environment variable
`ATLAS_AUTO_GUIDES=1`) enables missing-guide generation after successful profile sync.
Environment settings take precedence over stored values; remove an environment
override to let the UI control it. Manual guide buttons can generate guides even
when automatic generation is off; both service keys are still required.

These services may charge per request. A large library can produce many calls;
there is no hard monetary budget/cost estimator in this version. Stop All/Stop Guides
lets an active request complete, prevents the next provider request (including an
OpenAI request after a stopped Brave request), and retains completed guide notes.
Already incurred provider charges cannot be undone by cancelling locally. Generated
steps are model summaries of supplied snippets, not independently verified gameplay
instructions; source inclusion is not proof that every claim is correct.

The previously published v0.14 source started automatic guides whenever both keys
were available. Until a binary containing this fix is installed, users who do not
want that behavior should not configure those guide keys for that binary.

## Settings and credential protection

Windows stored settings use DPAPI scoped to the current Windows user: Xbox token
**file path**, NPSSO, Brave/OpenAI keys and guide preferences/model. On non-Windows
systems settings are a plaintext JSON file created with restrictive user permissions.
Environment variables are another supported source and are not written back by the
app. UI status returns presence flags rather than secret values. This is not a
credential vault against an attacker already running as you.

OpenXbox token-file contents, migration snapshots and library JSON are separate
from DPAPI settings. Never attach them to a public issue, commit them, or paste
NPSSO/API keys into chat. Clearing app settings does not remove environment variables,
SDK token files, provider-side authorizations, archives or already saved guides.

## Retention, deletion and revocation

There is no automatic cloud publication or profile sharing by the app. Local records
remain until replaced or deleted. Profile changes preserve local historical snapshots.
Stopping a transfer retains completed validated image files; cancelled incomplete
public-profile snapshots do not replace the current library. History, caches and
updater backups currently have no automatic retention/size policy.

To delete local data: close the app, back up anything you wish to keep, then remove
the chosen `AchievementAtlas` data directory (including profiles, backups, artwork
and updates). Uninstalling the per-user program may leave that directory. Separately
remove the OpenXbox token file at its SDK/operator location; delete environment
variables you configured; clear browser/WebView site data for cosmetic localStorage.
Removing local files does not revoke Microsoft/Sony sessions or API keys: use each
provider's account controls to revoke authorization, rotate keys and request any
provider-side deletion. Deleting files is not a forensic secure-erase guarantee.

## Signing, security and contact

[Code signing policy](CODE_SIGNING_POLICY.md) and [SECURITY.md](SECURITY.md) describe
the current development distribution. A GitHub/Sigstore origin attestation is not
Windows Authenticode publisher signing, a malware scan or SignPath approval.
This audit does not publish a new Release or change signing approval.

Questions: [repository issues](https://github.com/Gh0sTRX/achievment-thropy-tracker/issues)
or maintainer [@Gh0sTRX](https://github.com/Gh0sTRX). Do not put sensitive data in public
issues; follow SECURITY.md for sensitive concerns. Achievement Atlas is independent
of Microsoft, Sony, OpenAI, Brave, SteamGridDB, TrueAchievements and SignPath Foundation.

## Pending-update recovery (0.15.1 development channel)

Before replacing installed files, the new update helper persists a local file/hash
inventory and pending state next to the update plan and previous-version backup.
It registers a per-user Windows RunOnce value named
`!AchievementAtlasRecovery-<plan hash>` to attempt recovery after the next sign-in.
The command contains only the local helper path and recovery option, not account
credentials. Completed or restored updates remove their value; the new uninstaller
removes only Atlas recovery entries while preserving unrelated RunOnce values.
Backups/logs remain in the selected local data directory. No remote service is added.
Uninstall before deleting pending-update recovery files, or preserve them until
recovery finishes. Windows policy/timing can prevent this one-shot attempt; it is
not a guarantee of physical power-loss recovery. See
[recovery implementation and limits](docs/UPDATE_CRASH_RECOVERY_TR.md).
