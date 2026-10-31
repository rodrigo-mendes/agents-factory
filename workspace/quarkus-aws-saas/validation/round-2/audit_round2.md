# P6 round 2 re-audit (architecture-auditor, 3 lenses sequential, read-only, 2026-10-28)

**Verdict: PASS with 4 Should-fix.** Scope 8.0 · Flow 7.3 · Engine 7.4 (round 1: 6.8 / 5.6 / 6.6). 0 Must-fix (3/3), 4 Should-fix (2/3), 10 Consider (1/3).

## Round-1 findings

| ID | Status |
|---|---|
| C1 E7 chain, C2 drift baseline, S1–S5, O1 (profile), O4, O6, O8 (agents), O9, O12, O13, O15, orphan camel dirs | CLOSED |
| O2 no verifier for infra/observability Terraform | OPEN → decision needed |
| O3 factory paths in installed agents | OPEN → N1 |
| O7 stale text | OPEN (LOW) → N11 |
| O10 standalone use of observe-aws-workload | OPEN (LOW) → N10 |
| O5 guard hook, O11 broad Java globs, O14 26/49 rules without `paths:`, O17 description budget (155 auto-listed) | DEFERRED-TO-USER |
| O16 OCI observability record name, settings.json denies `*.tfvars` | ACCEPTED-TRADEOFF (say so in the preflight rule) |
| CLAUDE.md team + counts (measured 221 skills / 66 commands / 49 rules) | OPEN (P8) |

## New — Should-fix (2/3)

- **N1** `stripe-advisor` and `aws-architect` load skills/family rules from `packages/`/`workspace/` (absent in a SaaS project). Fix: `.claude/skills/` first, factory fallback, family rules optional.
- **N2** `logs-insights` approval: producer allows `scope="xray"`, consumers accept only a log group → traces pillar never retrievable. Add the xray scope to debugger, aws-observability, read-only allowlist, wo-observability, observe-aws-workload, profile SKILL; add `e7-gaps` to the profile SKILL list.
- **N5** worker-briefs omits `role: stripe` on reviews of Stripe tasks → changes-requested routes to `code`.
- **N6** spec-synchronizer allowlist lacks `--include-worktree`; diff uses `<sha>..HEAD` (misses uncommitted code).

## New — Consider (1/3)

N3 E7 must mark the `task: deploy` work-orders done before the board (final-gate `all_tasks`) · N4 Mode A observability review shares role `observability` with Mode B → use `observability-review` · N7 wo-observability allows `plan -out` (agent forbids real-backend plan) · N8 worker-briefs files alarm-test under the debugger; Mode A "inline" vs record · N9 deployer next-step hint skips observability · N10 observe-aws-workload examples without `wo=`, hardcoded code owner · N11 stale text (agent-alignment A4/A9, U4/U5, "(future)" markers) · N12 `__pycache__` in handoff-core scripts, not gitignored · N13 "applyTo" wording in aws-observability-skills · N14 Quick Navigation/Guardrails order in syncing-spec-from-code and observe-aws-workload.

Full report: subagent hand-back ad85d3c93c1be9413 (session transcript).
