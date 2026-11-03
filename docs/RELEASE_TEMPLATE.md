# Achievement Atlas vX.Y.Z — Windows Release

> **Replace `vX.Y.Z` in this template with the real release version before publishing.**
> This template is for GitHub Release **description text**, not a source-code update announcement.

## About the application

Achievement Atlas is a free, MIT-licensed, local-first achievement and game-library companion for Windows. It supports importing earned/locked TrueAchievements CSV exports, tracking progress and pinned completion goals, and optional experimental Xbox account connectivity and artwork caching. No compulsory cloud account is required for its offline library.

## Download & installation

1. Download the attached `AchievementAtlas-vX.Y.Z-Windows.exe` (replace with the **actual uploaded file name**).
2. Run the file on Windows. Review Windows security warnings before proceeding; never bypass warnings without verifying the file.
3. See the [README](https://github.com/Gh0sTRX/achievment-thropy-tracker#readme) for setup instructions and current limitations.

## Signature status

**UNSIGNED — SignPath Foundation application pending.**

This release has **not** been signed by SignPath Foundation. Its source and release file are provided on an as-is, pre-release basis. GitHub upload alone does not imply code signing or verified CI provenance.

**Code signing policy:** https://github.com/Gh0sTRX/achievment-thropy-tracker/blob/main/CODE_SIGNING_POLICY.md  
**Privacy Policy:** https://github.com/Gh0sTRX/achievment-thropy-tracker/blob/main/PRIVACY.md

**Planned service upon approval:** Free code signing provided by SignPath.io, certificate by [SignPath Foundation](https://signpath.org/).

When signing is actually enabled, update this section using the verified publisher/signature and corresponding GitHub Actions source-build details. Do not call a release signed until checked.

## Verify the file

**File:** `AchievementAtlas-vX.Y.Z-Windows.exe` (replace with actual name)  
**SHA-256:** `REPLACE_WITH_ACTUAL_SHA256`

On Windows PowerShell, run:

```powershell
Get-FileHash -Algorithm SHA256 ".\AchievementAtlas-vX.Y.Z-Windows.exe"
```

Compare its output with the published SHA-256 value. Do not publish the placeholder as a checksum.

## Current limitations

- The Microsoft/Xbox login and Xbox Live sync are experimental and may be unavailable.
- PlayStation integration is not implemented in the current source release.
- Game artwork providers may require user API keys or network access.
- No official association with Microsoft, Sony, TrueAchievements, SteamGridDB or SignPath Foundation is claimed.

## Source code and support

- [Source code / GitHub repository](https://github.com/Gh0sTRX/achievment-thropy-tracker)
- [MIT License](https://github.com/Gh0sTRX/achievment-thropy-tracker/blob/main/LICENSE)
- [Report bugs](https://github.com/Gh0sTRX/achievment-thropy-tracker/issues)
