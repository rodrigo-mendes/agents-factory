# Changes from gh 2.93 to 2.103

Back to [SKILL.md](../SKILL.md). Scope: only commands this skill uses. Read 2026-10-29 from https://github.com/cli/cli/releases (partly read; see [coverage limits](./unverified-and-risks.md#coverage-limits-4)) and the tag pages v2.94.0, v2.97.0 and v2.103.3 (read in full). Release-list dates show no year; 2026 is taken from the tag pages and fact F1.

| Version (date) | Change | Impact |
|---|---|---|
| 2.93.0 (2026-05-27) | `gh auth refresh` hint on 401; TUF auth-header leak fixed (medium confidence) | none |
| 2.94.0 (2026-06-10) | Issues 2.0: issue types (`--type`), sub-issues (`--parent`, `--add-sub-issue`, `--remove-sub-issue`, `--remove-parent`), relationships (`--blocked-by`, `--blocking`) | minimum gh for sub-issue flags |
| 2.97.0 (2026-07-31) | name-based `item-edit` (`--field`, `--value`); `item-list --field` named columns; fixes for GHSA-cg6r-mpgc-h9mm (`gh auth status` printed token fragments), GHSA-4fjg-2h4q-fwg3 (unescaped URL path components) and GHSA-3m3g-3wcr-px46 (terminal escapes) | require 2.97.0 or newer; older `gh auth status` logs may hold token fragments |
| 2.98.0 (2026-08-20) | fix `project item-add` output for non-TTY (medium confidence) | parse `item-add` only with `--format json` (medium confidence) |
| 2.99.0 (2026-09-01) | repeatable `--attach` on `issue create/edit/comment` (batches limited to 50 files); "fix(view): reject `--comments` with `--json`" | never combine them |
| 2.102.0 (2026-09-30) | host versions removed from `item-list` help (medium confidence) | none |
| 2.103.0 to 2.103.3 (2026-10-21 to 2026-10-26) | refreshable and expiring tokens (`--expiring`, automatic refresh in `gh auth status`, `--no-refresh`); `gh issue artifact` group | `gh auth status` may refresh tokens unless `--no-refresh`; artifacts out of scope |

Rows for 2.93.0, 2.98.0 and 2.102.0 come from the paginated release list only (summarised) and are tagged (medium confidence), register M7. The 2.94.0, 2.97.0, 2.99.0 and 2.103.x rows were read on tag pages (https://github.com/cli/cli/releases/tag/v2.99.0 read in full on 2026-10-29).

## Upgrade steps (Windows, official WinGet package)

1. `winget upgrade --id GitHub.cli --source winget`
2. Open a new terminal window (the installer changes PATH).
3. `gh --version` and expect `gh version 2.103.x`.

Source: https://github.com/cli/cli/blob/trunk/docs/install_windows.md

## Compatibility matrix

| Dependency | Minimum | Maximum | Note |
|---|---|---|---|
| gh | 2.94.0 for sub-issue flags; 2.97.0 for name-based edit and the token-print fix | 2.103.x pinned | family pin from fact F1 |
| REST API version | 2026-03-10 | none | shown on the sub-issues and comments pages |
| GHES | 3.17 for sub-issues; 3.19 for relationships (medium confidence) | none | out of scope here |

## Migration note

If a script still runs on gh 2.93 or older, upgrade first; the sub-issue flags and name-based edit do not exist there, and the manual pages in this skill describe 2.103.x only.
