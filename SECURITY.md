# Security & privacy

- **Local only:** Python HTTP server listens on loopback. API writes require a per-process anti-CSRF token and a local Host/Origin check. Do not put it behind a public proxy or expose the listening port.
- **Account isolation:** achievement imports and live account identity are compared before merging, and earned entries are not silently revoked.
- **Secrets:** do not commit `tokens.json`, local state, CSV exports or user artwork. The SteamGridDB key is session-only. The optional OpenXbox dependency stores OAuth tokens in its own user-local storage; protect your Windows account and never upload that folder.
- **Artwork:** remote image hosts are allow-listed, redirects are validated and payload sizes limited. Not every allowed CDN is guaranteed accessible.
- **No bypassing rate limits or Cloudflare:** 403 / 429 may be legitimate restrictions. Do not add bypass logic.
- **Threat model:** this is a pre-release tool. Windows Auth, browser-based login and third-party API responses have **not** undergone a professional security audit.

Report security problems privately to the repository maintainer instead of publishing credentials or a proof-of-concept affecting real accounts.