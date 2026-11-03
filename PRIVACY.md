# Privacy Policy — Achievement Atlas

**Effective date:** November 3, 2026  
**Project:** [Achievement Atlas](https://github.com/Gh0sTRX/achievment-thropy-tracker)  
**Scope:** The public, open-source application described in this repository (currently the v0.5 pre-release), including its optional desktop window and browser-based local interface.

## Summary

Achievement Atlas is **local-first**. It does not operate a hosted account service for your achievement library and the published application source contains no built-in advertising, analytics tracker, or automatic upload of your library to the project's maintainer.

**The program does not transfer personal information to other networked systems unless the user chooses to initiate a network-enabled feature**, such as Microsoft/Xbox sign-in or synchronization, searching or downloading artwork, or opening an external link. Those features and providers are described below. Offline CSV import and the local library do not require internet access.

This policy describes the code published in this repository, not hypothetical future integrations or modifications made by third-party distributors.

## Information processed and stored on your device

Depending on what you use, the application may process:

- **Imported game/achievement records:** game titles, achievement names, unlock status and dates, Gamerscore, publicly linked achievement pages, completion statistics and an optional Xbox gamertag from CSV files you select.
- **Preferences and saved state:** pinned achievements, game-to-service mappings, sync timestamps, chosen artwork and relevant settings.
- **Optional Xbox profile details:** your gamertag, Xbox user ID (XUID), Gamerscore and game/achievement data retrieved after you request account connection or synchronization.
- **Locally cached artwork:** game covers, hero images and achievement icons you choose to retrieve.

The application stores its library and settings as JSON files under the local `AchievementAtlas` application-data directory:

- **Windows:** `%LOCALAPPDATA%\AchievementAtlas\` (or the operating system's configured application-data fallback).
- **Linux/other supported environments:** `$XDG_DATA_HOME/AchievementAtlas/`, or `~/.local/share/AchievementAtlas/` if `XDG_DATA_HOME` is not set.

No project-hosted central database receives these files as part of ordinary local use. The local HTTP interface listens on `127.0.0.1` (loopback), not on a public network interface. Browser-based access to this interface stays on your own computer.

## Optional network services

Network features are optional and may transfer data to third parties when you explicitly invoke them:

1. **Microsoft / Xbox Live (experimental):** If you select Microsoft sign-in or Xbox synchronization, authentication requests and Xbox API requests go to Microsoft/Xbox services. The application processes the returned account and achievement information locally. The optional open-source [OpenXbox / xbox-webapi-python](https://github.com/OpenXbox/xbox-webapi-python) dependency manages OAuth tokens in its **separate user-local storage**; those tokens are not committed to this GitHub repository. Treat the token file as a credential. [Microsoft privacy statement](https://www.microsoft.com/en-us/privacy/privacystatement).
2. **SteamGridDB artwork:** If you enter an API key and search for artwork, requests containing the game/search term and your API key are sent to SteamGridDB. The API key is held in application memory for the active session rather than saved in the Achievement Atlas library. Selected images are downloaded from permitted image hosts to your local artwork cache. See [SteamGridDB](https://www.steamgriddb.com/) and its published terms/privacy notices.
3. **Achievement image providers:** If you request caching of available achievement icons, the program fetches images from the associated allowed provider/CDN. Your device's IP address and ordinary connection metadata may be visible to that provider.
4. **External links:** If you choose to visit a TrueAchievements achievement page or other external website, your browser communicates with that site under its own privacy policy, for example [TrueAchievements' privacy policy](https://www.trueachievements.com/privacypolicy).

These third parties independently determine their data handling. Achievement Atlas does not control their services, access logs, cookies, or retention policies. The project does not intentionally transmit local CSV files or its entire saved library to these services.

## Authentication and security

- Microsoft login occurs through a browser-based authorization flow; the application is not intended to collect your Microsoft password.
- The optional OpenXbox dependency stores sign-in tokens in its own local token file outside the repository. Signing out of a website does **not necessarily delete** those locally stored tokens.
- The application uses a local HTTP server and request-origin / anti-CSRF checks. This is a pre-release project and has not received a professional security audit.
- Do not publicly expose the local server, upload your personal library or token files, or commit your API keys to Git.

For implementation details and responsible reporting, see [SECURITY.md](SECURITY.md).

## Retention, deletion and your choices

Your local library, preferences and cached artwork remain on your device until you delete or replace them. Uninstalling the application may not remove the application-data directory. To erase locally stored Achievement Atlas data, close the program and delete the relevant `AchievementAtlas` directory. **This is irreversible unless you have a backup.**

If you used Microsoft/Xbox sign-in, separately delete the optional OpenXbox token storage and revoke the app's Microsoft account authorization if desired. Removing the Achievement Atlas data directory alone does not revoke a Microsoft authorization or erase copies held by external services.

You may use the local CSV functionality without connecting an Xbox account, entering an artwork API key, or using the network features. For data held by Microsoft, SteamGridDB or other providers, use their own account/privacy controls.

## Children and future changes

Achievement Atlas is not specifically directed at children and does not provide a child-oriented account service. Future features (including any PlayStation or PC integrations, telemetry or hosted services) will require this policy to be updated **before** those behaviors are deployed. Check the repository history for revisions.

## Contact

For a privacy question about the project, contact the maintainer **[@Gh0sTRX](https://github.com/Gh0sTRX)** through the [repository issue tracker](https://github.com/Gh0sTRX/achievment-thropy-tracker/issues). **Do not post tokens, passwords, private CSV exports or other sensitive personal data in public issues.** For sensitive security concerns, follow [SECURITY.md](SECURITY.md).

Achievement Atlas is an independent community project and is not affiliated with Microsoft, Sony, SteamGridDB, TrueAchievements or SignPath Foundation.
