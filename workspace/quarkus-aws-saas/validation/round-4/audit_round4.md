# P6 round 4 AUDIT (architecture-auditor, 3 lenses sequential, read-only + board simulations, 2026-10-28)

**Verdict: CONDITIONAL** (1 Must-fix). Scope 7.8 · Flow 7.6 · Engine 7.5 (round 2: 8.0/7.3/7.4). 1 Must, 5 Should, 10 Consider.

Round-2 backlog: CLOSED O3/N1, O10/N10, N2, N3, N6, N7, N8, N9, N12, N13; OPEN N4 (template, see M1), N5 (S5), N11 (C1), N14 (C2); DEFERRED O2, O5, O11, O14 (26/49 rules, ~145 KB, all OCI/terraform, not in SaaS graph), O17 (155 auto-listed / 221). Rule `sdd-openspec-workflow` does not exist. CLAUDE.md counts stale (221/66/49/40) → P8.

## Must-fix
- M1 Mode A record role split: agent/profile/briefs say `observability-review`; wo-observability.template.md:19-20, approval-lines.md:255-258, agent-alignment.md:38 say "A/B no role". Simulated: no role at E2 → `NEXT: deploy` (rule 16).

## Should-fix
- S1 E7 gap-acceptance relaunch: debugger always writes id verify-E7; overwrite breaks append-only, another file name → duplicate id. Fix: `verify-{stage}-{nn}`, keep the fail record.
- S2 `tfplan` (no extension) and lock-file changes become drift under --include-worktree (deploy-report has no Files section) → sync shadows final-gate.
- S3 aws-observability intake needs code owner + profile (no template field / no argument) and smoke start epoch (deployer doesn't record it).
- S4 `--include-worktree` called Ask First in profile SKILL:159, orchestrator SKILL:57,:121 but mandatory in E8/E9.
- S5 `role: stripe` only on the advisor review in wo-review.template:32 and agent-alignment:51.

## Consider
C1 agent-alignment A1 stale (integrator emits spec_impact/task); "Input" vs "Intake" · C2 Guardrails order (syncing, observe, profile SKILL) · C3 debugger still allows a real invoke with "a relayed approval line" · C4 Mode A `spec_impact: divergence` at E2 → sync before E5 baseline · C5 `scope=xray` vs `scope="xray"`; "one line per scope" missing in e7/approval-lines · C6 build_attempts counts Mode C/Mode A partial reports · C7 wo-debug task comment (mode B: deploy) · C8 synchronizer git diff misses untracked files · C9 aws-architect cites `_family_rules_v2026.md` · C10 tests use the simplified fixture, not the installed profile.

Full report: subagent hand-back acaa447a7e24d2830 (session transcript).
