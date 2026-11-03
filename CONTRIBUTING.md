# Contributing

Thanks for helping build Achievement Atlas as a reusable open-source companion.

1. Open an issue describing a bug or feature before larger changes.
2. Keep each platform integration behind its own adapter; do not put personal account IDs, API keys, passwords or exported gamer data in source code.
3. Preserve offline CSV import even when online providers fail.
4. Include tests for data parsing, account isolation, achievement mapping and status transitions; never fabricate unlock percentages, dates or artwork URLs.
5. Run `python -m unittest discover -s tests -v` and `node --check atlas/web/app.js` before opening a PR.
6. Document actual live-account checks separately from mocked/unit tests.

Respect Microsoft, Sony, artwork-provider and achievement-site terms. Do not bypass access controls or redistribute third-party artwork without permission.