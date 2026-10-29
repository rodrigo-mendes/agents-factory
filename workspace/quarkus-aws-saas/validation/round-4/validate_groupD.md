# Round 4 VALIDATE — group D (quality-validator, 2026-10-28; saved by orchestrator from the inline report)

| Skill | HIGH | MED | LOW | Score |
|---|---|---|---|---|
| coordinating-agent-handoffs | 4 | 4 | 4 | 64 |
| specifying-changes-with-openspec-v1-15 | 3 | 1 | 3 | 78 |
| syncing-spec-from-code | 1 | 2 | 3 | 87.5 |
| observe-aws-workload | 0 | 2 | 4 | 93 |
| integrating-stripe-quarkus-v3-40 | 2 | 3 | 3 | 79 |

Scripts vs docs: flags, exit codes, kinds/enums, sections, matchers, counters, escalation all match. No `report*` file names.

## coordinating-agent-handoffs
- H1 rule 12: Quick Navigation lacks Verification Loop link (SKILL.md:23-40).
- H2 rule 12: protocol.md (102), profile-format.md (109), evaluation-scenarios.md (128) lack Contents.
- H3 evidence: `report*` write guard stated flat in always-do:25-26, never-do:14; SKILL.md:189 Never Do row tagged unverified U2 → keep naming as convention, guard claim only as (unverified).
- H4 structure: Blueprints & Guardrails at SKILL.md:166, after ~120 lines of long sections → move after Quick Navigation.
- M1 register notation (C1/C2→L ids, R1, "Tag mapping" heading/columns). M2 same tag written 3 ways ("(unverified: …)"). M3 drift-hook.md:21-24,50-53 unverified claims untagged, no U ids. M4 rule 14: deploy-report/diagnosis-report templates list only success|failed.
- L1 role from `to` for work-orders undocumented (SKILL.md:154). L2 "orchestrator-mediated" vs "orchestrated". L3 deploy-report.md vs id deploy-report-<nn>. L4 SKILL.md:19 cites packages/oci-core path.

## specifying-changes-with-openspec-v1-15
- H1 Always Do :54,:56,:57 and Never Do row 3 :78 rest on L1/L2 medium claims; never-do-patterns.md:3 "every alternative High" false; REMOVED/RENAMED format is a High family fact but skill hedges it medium (rule 13).
- H2 rule 13: archive-without-`--yes` claim tagged medium in always-do:126, flat in never-do:57, non-interactive:23, scenarios:112.
- H3 releases-page claims (L2) untagged: migration-notes:19-28, non-interactive:19-22,63,71-72,80, ask-first:25,62, SKILL.md:19.
- M1 absence of evidence ("no openspec diff", U4) should be (medium confidence, absence of evidence).
- L1 tag date source; L2 "(unverified, U1)" form; L3 migration-notes:46 merged list items.

## syncing-spec-from-code
- H1 flow stall: P1 "exit 0 → no drift, stop" ignores record drift (`spec_impact: divergence|ambiguity` without delta ref → board drift=true → sync again, unbounded). Fix: scan handoff records too; add scenario.
- M1 `--include-worktree` hard-wired vs Ask-First in protocol. M2 agent cannot know `spec.kind` (no --profile input).
- L1 Mode A unmentioned; L2 E5/E9 jargon; L3 no misuse scenario.

## observe-aws-workload
- M1 `nn=` missing in argument-hint/synopsis. M2 "validate (default)" vs agent requires mode.
- L1 Ask First wording (agent never asks user). L2 "read-only scripts" vs alarm test. L3 "returns a result" vs record in every mode; QUESTIONS vs needs-input. L4 names Quarkus skills not in apm.yml deps.

## integrating-stripe-quarkus-v3-40
- H1 Never Do row 2 (:73) and never-do N2/N5/N6 rest on medium/unverified (D9 L2, U1); Always Do 5 carries caveat pointer.
- H2 neighbour-skill claims not re-fetched untagged: migration-notes:7, webhook-pipeline:67, always-do:42, :95.
- M1 D9 "Default" + no D9 section. M2 absence-of-evidence tag form (SKILL.md:61, migration-notes:28, :96). M3 caveats in Always Do :49,:50.
- L1 register mapping says tags in Always Do that are absent; L2 tool-summary date; L3 two-level bibliography.
