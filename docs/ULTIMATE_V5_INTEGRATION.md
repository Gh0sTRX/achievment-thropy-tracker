# Atlas Ultimate v5 — Cinematic UI integration (feature preview)

This is an **opt-in UI layer** on top of the existing Achievement Atlas local-first application. It does not replace the working HTML/JS application and does **not** add any PlayStation or PC account provider.

## Open the experience

Launch the existing app normally. Click **✦ ATLAS ULTIMATE** in the upper-right header. Select a platform, one of the four skins (Cinematic, 360 Blades-inspired, 360 NXE-inspired or PS3 XMB-inspired), and explore the seven screens:

- Atlas Hub — featured game, local achievement counts, recommendations, in-progress games.
- Game Library — search across *your own* imported titles and open a game.
- Game Universe — game art and recorded achievements, with the existing pin API.
- Quest Board — existing recommendation engine output.
- Hall of Fame — earned games and **100% of currently recorded achievements only**, explicitly not a claim of all official DLC/achievements.
- Unlock Timeline — uses only **unambiguously parseable ISO timestamps**; missing or ambiguous dates yield an honest empty state.
- Artwork Lighting — non-destructive brightness/blur/focus overrides saved only in the browser's local UI preferences. Actual image selection returns to the original Artwork Studio.

**Console Mode:** choose games with arrow keys or a compatible Gamepad API controller (D-pad or left stick); Enter/A opens the game's detail, Esc/B closes. Alt+C toggles Console Mode.

## Real artwork — no generated images

The production UI calls the existing `artStyle()` function; it displays only user-selected cached images or HTTPS artwork from hosts already allow-listed by the application. It does not download new assets, bundle copyrighted game art, generate fake art, scrape websites or bypass rate limits.

Without selected artwork, the screen falls back to decorative CSS gradients (not AI-generated illustrations).

## Trust boundaries and existing features

- Xbox CSV import and existing optional Microsoft/Xbox sync continue to work in the classic interface.
- Local HTTP remains on `127.0.0.1` and new static assets are served by an exact allowlist.
- The UI layer uses existing read-only `DATA`, `RECS`, `games()`, `progress()` helpers and the existing `/api/pin` POST action.
- It never fabricates PSN platinum trophies, PC unlock data, progression percentages or unlock timestamps.
- It never alters the user library or the OAuth token storage. UI-only preferences use `localStorage` key `achievement-atlas-ultimate-v5` on the local application origin. Clearing browser site data resets these cosmetic preferences.
- It is an **early integration preview**, not a final signed Windows release.

## Files

- `atlas/web/ui/ultimate.css` — namespace-scoped UI components and responsive/legacy themes.
- `atlas/web/ui/ultimate.js` — user-library presentation and event handlers.
- `atlas/web/index.html` — loads the optional CSS/JS after the existing app files.
- `atlas/server.py` — exact static asset routes and platform-neutral window title.
- `tests/test_ultimate_assets.py` — allowlist and availability regression checks.

## Verification

Before merging:

```bash
python -m unittest discover -s tests -v
node --check atlas/web/app.js
node --check atlas/web/ui/ultimate.js
```

Review in browser with real CSV imports, no images, some cached images, and several games. Verify the Xbox OAuth flow on a consenting test account separately (network authentication is not simulated by unit tests). Check keyboard navigation, 1440×900 and 390×844 viewports, animation reduction, and screen reader focus behavior.

**Known limitations:** timeline only handles ISO-style dates; sources such as TrueAchievements may use non-ISO dates and should be normalized explicitly by an improved tested importer. The UI does not yet provide true PSN/PC provider integration, per-device gamepad hardware certification, rigorous performance measurements with large libraries, or a professional accessibility audit.

This UI feature is independent of SignPath Foundation application and signing status.

## v5.1 — Date accuracy and performance (November 3, 2026)

- `atlas/dates.py` validates and normalizes imported unlock dates before saving. ISO-8601 dates with explicit timezone are preserved; month-name dates and unambiguous numeric dates are supported. Ambiguous strings (such as `03/04/2026`) are **not guessed**.
- `atlas/core.py` now writes normalized `unlock_time` and retains the original string in `unlock_time_raw`. This does **not** remove or rewrite existing local user libraries. Re-importing an earned CSV normalizes the new records; the Ultimate UI can also interpret common unambiguous historical strings in older libraries.
- Ultimate's game/achievement counts are indexed once per data reload rather than filtering all achievements for every game card. This prevents O(games × achievements) rendering work.
- The Library search is debounced by 100 ms. Changing focus games crossfades the **existing real artwork**, with an explicit reduced-motion bypass; no art is fabricated or shipped.
- The timeline uses local calendar-day buckets. Dates without a reliable day/month order are excluded, and no missing timestamps are estimated. The window excludes future unlocks.

**Performance check:** in a separate local Chromium fixture with 1,200 synthetic games and 36,000 synthetic achievements, the Hub rendered in approximately 179 ms and the Library view in approximately 58 ms. These are illustrative measurements on one test environment, not guaranteed performance metrics for real-world devices.

**Validation:** `tests/test_unlock_dates.py`, existing unit suite, JavaScript syntax checks, and local Playwright smoke tests. Real imported files and physical gamepad behavior still need manual validation. No SignPath signing changes were made.
