# Atlas Ultimate V5 — 0.14 integration

PR #2 / `feature/atlas-ultimate-v5-live-ui` integrates the uploaded V5 mission and
preview into the current 0.13 application. The V4 ZIP is a design reference;
its example game images, download scripts and demo scores are not bundled or run.
Main is not merged automatically. SignPath configuration is unchanged.

## User experience

Choose **Atlas Ultimate** in the header for the V5 experience. Classic remains
available. Cinematic, Blades, NXE and XMB are cosmetic skins, not data providers.
All/Xbox/PSN/PC filters use provider-scoped game IDs; the optional view no longer
inherits a narrower classic filter or matches different editions by game name.

Click a trophy to expand its detail **below its row/card**. Both views share this
behavior; clicking does not open a new window or a side drawer. Secret details
require explicit reveal. Pins use the existing authenticated endpoint. Artwork
selection returns to the correct game's classic Artwork Studio.

The transfer dock is visible over either view. Stop Profile, Stop Images or Stop
All requests cooperative cancellation. A cancelled profile snapshot is discarded
and the previous library remains. Already validated image files and completed
guides remain. Active synchronous PSN/image requests may need to finish (media
requests have the existing 12-second timeout). No thread is forcibly terminated.
The `Tam yenile` option bypasses incremental trophy reuse.

## Faster synchronization

- Xbox: at most three game requests in flight. Pagination remains sequential
  within a game. 401/403/429 stop processing; no access-control bypass or retry storm.
- Xbox and PSN: same target identity + exact provider summary + complete cached
  record count + matching API/catalog generation can reuse a snapshot for at most
  ten minutes after its last full fetch. Missing summaries and changed totals
  cause full refresh. Reuse does not renew its own TTL. Partial in-achievement
  progress may remain cached during this interval; `Tam yenile` fetches it again.
- Media: at most four icon downloads; work is submitted in small chunks, cache
  hits skip network and completed changes are saved in batches of sixteen.
- `/api/status` is a small, read-only polling endpoint. Unchanged libraries are
  no longer repeatedly transferred and rescored by the UI. A revision change
  fetches `/api/data`; old clients keep the existing full endpoint contract.

This reduces requests and disk writes. Live Gh0sTRX55 latency was not measured;
no percentage speedup or complete live-account verification is claimed.

## Dates, metrics and migration

CSV normalization accepts explicit ISO dates/timestamps, an English month with
four-digit year, and bounded Windows Excel 1900-system serials. Numeric locale
formats such as 03/11/2026 are deliberately omitted. The original date text is
retained when normalizing existing records. IDs, editions and pins are preserved.
Missing legacy achievement platform fields derive only from their exact game ID.

Local calendar boundaries are used for date-only timeline events; explicit
ISO timezone offsets keep their instant. Invalid dates are rejected. Timeline
30/90/365-day views include zero bins and an accessible table. Hall of Fame labels
%100 as local recorded scope, never a guarantee of the official full catalogue.
Xbox G is not shown as PSN/Steam points; actual PSN platinum records are supported.
PC/Steam remains planned; the existing PSN adapter requires operator service access.

## Console Mode and accessibility

Alt+C launches Console Mode; arrows/D-pad/analog stick select games, Enter/A opens,
Escape/B closes. Only one animation-frame polling loop runs while open. Directional
hold repeat is separate from edge-triggered A/B. Disconnect keeps keyboard access.
The native HTML dialog traps focus; the underlying UI is inert and body scrolling
is locked while Ultimate is open. Focus returns on close. Reduced motion is honored.

The optional V5 namespace retains only cosmetic preferences in its own localStorage
key; tokens, CSV records and guides are never stored there. Classic appearance and
artwork preferences remain in local state.json. V5 localStorage persistence depends
on webview origin/session; it is not used as a source of achievement truth.

## Windows branding

Original Atlas SVG/PNG/ICO marks are in assets. The ICO contains 16–256-pixel sizes
and is used for EXE, installer and shortcuts. The native window explicitly receives
the icon and the shared `AchievementAtlas.Desktop` AppUserModelID. No game/publisher
art or generated game imagery is used. Windows may retain an older pinned shortcut
icon until the shortcut cache is refreshed by recreating that pin.

## Validation

- 95 Python tests pass, including cancellation, target isolation/TTL/force refresh,
  batched writes, bounded media concurrency, existing imports/SDK adapters, and guards.
- Node projection test: 15,000 records, edition/platform isolation, date rejection,
  zero measured progress and honest completion/score metrics.
- Chromium 1440×900 / 1280×720 / 768×1024 / 390×844: all seven V5 screens,
  classic-to-V5 transitions, inline trophy expansion and Console Mode pass.
- Simulated Gamepad API input: D-pad, analog axis, A/B, disconnect, focus trap and
  keyboard fallback pass. Physical controller certification is not claimed.
- XSS-sensitive strings are HTML-escaped; artwork styles use the existing safe
  pipeline. New static paths are exact allowlists; Host/Origin/token protections
  remain. Stop operations use the same authenticated POST guard.
- Windows workflow additionally tests the packaged native window/icon and Setup
  install/uninstall, then verifies GitHub/Sigstore provenance before publishing.

Temporary browser fixtures/screenshots live only under work/v5 and /tmp. They are
explicit test data and are not part of the distributed library or installer.

## Concurrent V5.1 changes preserved

Upstream PR #2 commits through 981e3d9 were merged without rewriting the remote
branch. Their explicit numeric/month-name/AM-PM date parser, date regression tests,
real cached-art crossfade and debounced search are retained. The index uses stable
raw library/array references rather than filtered arrays, so it rebuilds once per
reload; game statistics are cached alongside per-game achievement lists.
