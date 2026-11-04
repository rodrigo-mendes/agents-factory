# Scoreboard - round-1 (2026-10-30)

Rubric per skill: 100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW. Baseline: pilot round-0 (terraform only, 91).
Exit criteria (triage-and-stop-rules): no HIGH, every skill >= 90, package >= 8/10, audit >= 8/10, 100% scenarios pass.

| Target | Validate | Test (scenarios) | HIGH | Baseline | Meets exit? |
|---|---|---|---|---|---|
| composing-github-actions-pipelines | 90.0 | 5/5 | 1 (F-013) | - | no |
| automating-terraform-github-actions-v1-17 | 86.0 | 5/5 (stale criteria) | 1 (F-014) | 91 | no (regressed by G2 plan change) |
| federating-github-actions-aws-oidc | 90.0 | 5/5 | 1 (F-015) | - | no |
| federating-github-actions-oci | 90.0 | 5/5 | 1 (F-016) | - | no |
| building-java-github-actions | 92.5 | 4/4 | 0 | - | MEDIUM only |
| publishing-container-images-github-actions | 90.0 | 5/5 | 1 (F-017) | - | no |
| building-nextjs-github-actions-v16-4 | 90.5 | 5/5 | 0 | - | MEDIUM only |
| limiting-blast-radius-github-actions-deploys | 88.5 | 5/5 | 0 | - | no (< 90) |
| securing-supply-chain-github-actions | 93.0 | 5/5 | 0 | - | MEDIUM only |
| package (agents, rules, command, README) | 86.0 | command 2/3 (PARTIAL) | 1 (F-018) | - | no |
| audit (architecture) | 7.8/10 | - | 0 | - | no (< 8) |

Terraform score drop vs round-0 is explained (not a fix regression): the G2 answer (private Team/Pro/Free) invalidated the pilot's required-reviewers approval model (F-011 -> F-014).
Open findings after round-1: HIGH F-013..F-018; MEDIUM F-019..F-028 and audit AUD-1/3/4; LOW batch.
