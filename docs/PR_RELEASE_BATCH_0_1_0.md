# PR: Batch Release v0.1.0

## Summary

This PR prepares and documents the **initial batch release** of clible. It bundles all features and fixes developed to date into a single, well-documented release (v0.1.0). No new code features are added; the goal is to align documentation, changelog, and release tooling so that everything so far is consistently released as one unit.

Includes **conventions audit**: module docstrings, English-only comments, [CONVENTIONS_AUDIT.md](CONVENTIONS_AUDIT.md).

## Purpose

- **Release everything created so far in one batch** – All prior work (verse fetching, analytics, session management, caching, Docker, etc.) is treated as a single cohesive release.
- **Establish release hygiene** – Add `CHANGELOG.md`, update `README.md`, and create this PR document so future releases can follow the same pattern.
- **Provide a clear baseline** – v0.1.0 serves as the first tagged version for semantic versioning and future bumps (e.g. via bump2version).

## Changes in This PR

### 1. README.md

- **Documentation**: Link to [CHANGELOG.md](../CHANGELOG.md) in the Documentation section.
- **License**: Replace “Add license information here” with “See [LICENSE](../LICENSE) file in the repository.”
- Version and status at bottom remain **0.1.0** and **Active Development** (unchanged).

### 2. CHANGELOG.md

- **Created and filled** using [Keep a Changelog](https://keepachangelog.com/) format.
- **\[Unreleased\]** – Placeholder for future changes.
- **\[0.1.0\] - 2026-01-24** – Initial batch release entry with:
  - **Added**: Core, API/fetching, CLI/UI, analytics, session/queries, export, DevOps (mapped to PRs/issues where applicable).
  - **Changed**: Session refactors, caching improvements, Taskfile/README updates.
  - **Fixed**: API rate limiting, session linking, range support, analytics fixes.
  - **Removed**: Reading statistics (temporary removal).
- Pointers to `docs/` PRs for detailed feature descriptions.

### 3. This PR Document

- **docs/PR_RELEASE_BATCH_0_1_0.md** – Describes the batch release PR, its scope, and the release checklist below.

### 4. Conventions Audit

- **Module docstrings**: Added to all app modules (api, db/queries, cli, export, state, status_bar, menus, validations, analytics).
- **Test comments**: Finnish comments in `test_validations`, `test_fetch_by_reference`, `test_analysis_tracker` replaced with English.
- **CONVENTIONS_AUDIT.md**: New doc summarizing naming, commenting, and docstring conventions; applied changes; file-size notes.
- **.cursorrules**: Typo fix "Constantlly" → "Constantly".
- **Cleanup**: Removed `app/menus/Untitled`; minor fixes (status_bar docstring, validation_lists Old/New Testament, redundant comments).
- **README**: Link to [Conventions audit](CONVENTIONS_AUDIT.md) in Documentation section.

Details: [CONVENTIONS_AUDIT.md](CONVENTIONS_AUDIT.md).

## Files Changed

- **README.md** – CHANGELOG link, License reference, Conventions audit link
- **CHANGELOG.md** – New file, full initial release notes
- **LICENSE** – MIT (clible contributors, 2026)
- **.cursorrules** – Typo fix
- **.gitignore** – Remove `docs/` so docs are tracked
- **.bumpversion.toml** – Version bump config
- **.github/workflows/release.yml** – Release workflow (if present)
- **docs/PR_RELEASE_BATCH_0_1_0.md** – This PR description
- **docs/CONVENTIONS_AUDIT.md** – Conventions audit summary
- **app/** – Module docstrings, minor fixes (api, cli, db, export, state, status_bar, menus, validations, analytics)
- **tests/** – English comments (test_validations, test_fetch_by_reference, test_analysis_tracker)
- **app/menus/Untitled** – Deleted

## Release Checklist (Post-Merge)

After this PR is merged:

- [ ] All tests passing (`uv run pytest`)
- [ ] Version in `pyproject.toml` is `0.1.0` (no bump in this PR)
- [ ] Create annotated tag: `git tag -a v0.1.0 -m "Release v0.1.0 – initial batch release"`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] Optional: Use bump2version for future releases (`.bumpversion.toml` already configured)
- [ ] CONVENTIONS_AUDIT and PR_RELEASE_BATCH_0_1_0 reflect merged state

## Scope of v0.1.0 (What This Release Captures)

All work up to and including:

- Core: verse fetching, SQLite storage, sessions, multi-user, AppState.
- API: book fetch, max chapter/verse, caching (API + verse data cache).
- CLI/UI: menus, item selection, status bar, Rich UI.
- Analytics: word frequency, phrase analysis, translation comparison, visualizations, analysis history and tracking.
- Export: Markdown and plain text.
- DevOps: Dockerfile, Docker Compose, CI, Taskfile.

See [CHANGELOG.md](../CHANGELOG.md) for the full breakdown and PR references.

## Breaking Changes

None. Documentation, release tooling, docstrings, and comment language changes only; no behavioural changes.

## Related Documentation

- [CHANGELOG.md](../CHANGELOG.md) – Version history.
- [README.md](../README.md) – Project overview and usage.
- [CONVENTIONS_AUDIT.md](CONVENTIONS_AUDIT.md) – Naming, commenting, docstrings.
- Other `docs/PR_*.md` files – Feature-specific PR stories (e.g. `PR_VERSE_DATA_CACHE.md`, `PR_SESSION_ANALYSIS_FIXES.md`, `PR_TRANSLATION_COMPARISON.md`).
