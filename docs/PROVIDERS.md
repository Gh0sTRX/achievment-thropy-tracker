# Public profile providers

Username-only target lookup is now implemented for Xbox (operator OpenXbox session) and PSN (operator PSNAWP session). Brave search + OpenAI produce cached, source-linked Turkish notes. See [setup and limitations](PUBLIC_PROFILES_TR.md). These integrations have fixture coverage; live target verification is pending.

# Platform and artwork providers

## Current (experimental)

- **CSV adapter**: user-supplied earned/locked TrueAchievements exports. No login needed. This is a snapshot, not live sync.
- **Xbox adapter**: optional `xbox-webapi` library, with Microsoft OAuth and Xbox XSTS. Read-only account, title history and achievements. Title ID mapping requires user confirmation to avoid wrong-edition matches. Access can fail due to provider restrictions; live auth is not CI-tested.
- **Artwork adapter**: user-supplied SteamGridDB API key for cover/hero search; explicit user selection; local image cache. Xbox One achievement API may supply `mediaAssets` icon URLs. Xbox 360 numeric `imageId` is not a URL and must not be guessed.

## Planned

- **PlayStation adapter**: implemented in `atlas/public_profiles.py`; requires operator authentication.
- **Recommendation plugins**: explainable rules such as near-100%, short-session options (only with trusted duration data), missable achievements, offline-only filters and cooperative targets.
- **Artwork metadata**: source, attribution, cache expiration, missing assets and optional cache refresh.

The app core must work without network access or any game platform integration. We do not bypass Cloudflare, DRM, private endpoints or access controls.