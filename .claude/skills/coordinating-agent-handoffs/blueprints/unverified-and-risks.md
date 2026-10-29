# Unverified items and risks

Back to [SKILL.md](../SKILL.md). Register: **6 unverified (U1-U6)**, **1 irresolvable
version-lifetime risk (I1)** and **2 coverage limits (L1-L2)**, 9 items in total. Tags
`(unverified)` in other files of this skill point here by id.

## Contents

- [Unverified](#unverified)
- [Version-lifetime risk](#version-lifetime-risk)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Unverified

| Id | Item | Consequence | Mitigation |
|---|---|---|---|
| U1 | Claim "Python 3.8+, stdlib only" and "Windows and Linux": written to the 3.8 feature set (no `fromisoformat` with `Z`, no walrus) and checked by reading, but the tests were only run on Python 3.14 in this build. | A 3.8-only incompatibility could remain | Run `python -m unittest discover -s scripts/tests` on the oldest Python in use before relying on it |
| U2 | Subagent write guard on file names starting with `report`: observed in this build, not found in an official, dated Anthropic page. | If the guard is narrower or removed, `result-<nn>-<role>.md` is still the factory convention | Keep `result-<nn>-<role>.md`; never probe the guard |
| U3 | Claude Code `Stop` hook exit codes: exit 2 prevents Claude from stopping, every other exit code is non-blocking. Page not recorded. | The `\|\| true` in the hook command could be unnecessary or insufficient | Re-check the current hooks reference before installing the hook ([drift hook](./drift-hook.md)) |
| U4 | `Stop` hook stdout may be visible only in the transcript view. | A warning could go unseen | Verify in the target Claude Code version after installing |
| U5 | The `{"systemMessage": "..."}` JSON field name for an always-visible hook message. | The wrapper would print an ignored line | Confirm against the current hooks reference first |
| U6 | On Windows the hook command may run in Git Bash, where `python` may be missing and `py` is needed. | The hook could fail silently (`\|\| true`) and never warn | Run the verification command of the [drift hook](./drift-hook.md) in the shell that Claude Code uses |

## Version-lifetime risk

| Id | Risk | Consequence | Mitigation |
|---|---|---|---|
| I1 | Protocol v1 is the factory's own protocol (no external source, no upstream release). It couples to the OpenSpec skill `specifying-changes-with-openspec-v1-15` (delta sections, archive order) and to Claude Code behaviour (subagent write guard U2, `Stop` hook U3). A change in any of them is invisible to this skill. | Silent drift between protocol and tools | Bump `protocol_version` on any breaking change to record fields; re-check the OpenSpec link when that skill is re-researched; re-run the scripts' tests after a Claude Code or Python upgrade |

## Coverage limits

| Id | Limit | Consequence | Mitigation |
|---|---|---|---|
| L1 | 2 git-dependent tests could not run in the build sandbox (the `TestDetectDrift` cases that need a real `git` repository); `detect_drift` was verified manually. | A regression in git handling would not be caught by the sandbox run | Run the full test suite where `git` is installed; the round-1 additions (`TestDetectDriftExact`) are git-dependent too |
| L2 | The fixtures cover two profiles only (Quarkus/AWS orchestrated, OCI user-mediated); other `spec.kind` / `scope_key` combinations are tested by reading. | A profile feature outside the fixtures may misbehave | Add a fixture when a new family profile uses a new combination |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Python 3.8+ stdlib only | SKILL.md Version Context | U1 |
| (unverified) subagent write guard on file names starting with `report` | README.md of the package, this register | U2 |
| (unverified) `Stop` hook exit-code behaviour | drift-hook | U3 |
| (unverified) hook stdout visible only in the transcript | drift-hook | U4 |
| (unverified) `systemMessage` field name | drift-hook | U5 |
| (unverified) Windows hook shell may be Git Bash, `py` instead of `python` | drift-hook | U6 |

U1 and U3-U6 are tagged in the skill text; U2 is mapped here and in the package README only (the same
`(unverified)` wording). The risk I1 and the coverage limits L1-L2 have no tag; they are stated here only.

## Source Bibliography

| Claim | Source | Date | Status |
|---|---|---|---|
| Python 3.8+ compatibility | none (design choice; see U1) | 2026-10-28 | unverified |
| OpenSpec delta/archive formats | `specifying-changes-with-openspec-v1-15` (OpenSpec 1.15, researched 2026-10-28) | 2026-10-28 | defers to that skill |
| Subagent write guard on file names starting with `report` | observed in this build; no official page | 2026-10-28 | unverified (U2) |
| `Stop` hook behaviour (U3-U6) | page not recorded | 2026-10-28 | unverified |
| Protocol v1 itself | factory-own, generalised from the skill `coordinating-oci-handoffs` (`blueprints/handoff-protocol.md`) | 2026-10-28 | no external source |
