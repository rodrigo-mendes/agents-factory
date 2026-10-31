# CC Architecture Consensus - openspec-github (round 3, final)

Date: 2026-10-29. I applied the three lenses one after another myself (no agents and no plan mode, per the brief). Approval relayed from PIPELINE_STATE.md#approvals.

## Scores
| Lens | Score |
|---|---|
| A Scope (G0-G4 + XCC) | 8.9 |
| B Flow (FCC.1-20) | 8.7 |
| C Engine (ECC.1-18 + Actions trust) | 8.6 |
| **Weighted** | **8.7 - PASS** |

## Closure of the earlier HIGH and MEDIUM findings
| ID | Status | Evidence |
|---|---|---|
| F1 HIGH: agent approves through the shared gh login | CLOSED | `scripts/gh_projects_sync.py:184-197` `check_operator` refuses an approver login, runs in `preflight` :200-205; SKILL.md:89,99 |
| F2 HIGH: write token near npm | CLOSED | `assets/workflows/openspec-archive.yml`: `authorize` has a read-only token, `prepare` has no token and runs `npm --ignore-scripts`, `publish` uses a fresh runner and mints the write token only in the last two steps (rule 15) |
| F3 MEDIUM: CLAUDE.md counts | CLOSED | `check_counts.py` reports 226/67/159/41/50/32, matching CLAUDE.md:139-141,148,157,161,166; packages described at :99-107 |
| F4 MEDIUM: canonical command call | CLOSED (round 2, no regression) | - |
| F5 MEDIUM: archive before the pull re-check | CLOSED | the `authorize` job runs `gate_command.py recheck --gate E9`; `prepare` needs it |
| F6 MEDIUM: gate noise | CLOSED (round 2, no regression) | - |
| F7 MEDIUM: trust anchors read from the working tree | CLOSED | `gh_projects_sync.py:589-601` refuses modified anchor files and prints `TRUST` |
| N1 MEDIUM: local App token refused by preflight | CLOSED | the docs now match the code: SKILL.md:89,99, approvals-and-trust.md:94-95 and bootstrap-and-credentials.md:57 all say "machine-user locally, App only in Actions" |
| N2 MEDIUM: rename bypasses the path filter | CLOSED | `_model.py:920-955` `check_patch` checks both sides of every rename/copy, refuses mode changes, symlinks, submodules and quoted paths; called in `publish` before `git apply`, followed by `--no-renames --name-only`; tests at test_model.py:409, test_gate.py:296 |

F9 (naming) is deferred to G3 and is not scored here.

## New HIGH/MEDIUM findings
None.

## New LOW findings
- L1: in `check_operator`, `GITHUB_ACTIONS=true` turns an unreadable login into a warning, and any local process can set that variable. The impact is nil, because only a token with no readable login (an App token) gets past it, and that token cannot act as an approver. Add a comment.
- L2: `prepare` runs third-party code, so it can still write any content under `openspec/` into the patch. The human PR review is the remaining control. Say so in `blueprints/workflows.md`.
- L3: `authorize` and `prepare` each check out the default branch separately, so a push between them changes the ref they work on. Pin `prepare` and `publish` to the authorize job's `github.sha` (or its HEAD output).
- L4: the round-2 LOW findings N3-N8 were not re-scored in this round.

## Verification limits
I compared packages/openspec-github with .claude and found no drift. Running the test suite with unittest did not finish within 120 s, so test results were not confirmed in this round.
