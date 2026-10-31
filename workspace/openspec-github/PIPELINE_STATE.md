# Pipeline state — openspec-github

```yaml
slug: openspec-github
mode: new
current_phase: G3
reconstructed: false
rounds: 3
```

## Version gate (P1, fetched 2026-10-29)

| Item | Target | Evidence | Source |
|---|---|---|---|
| GitHub CLI | 2.103.3 (Latest, 2026-10-26); local install 2.93.0 (2026-05-27) | releases page | https://github.com/cli/cli/releases |
| Projects v2 from Actions | GITHUB_TOKEN "is scoped to the repository level and cannot access projects"; GitHub App "recommended for organization projects", PAT "recommended for user projects"; App needs read/write **organization** projects ("repository projects will not be sufficient") | docs page, no date shown | https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions |
| actions/create-github-app-token | v3.3.0 (Latest, 2026-10-12), docs use `@v3` | releases page | https://github.com/actions/create-github-app-token/releases |
| Sub-issues | up to 100 per parent, 8 nesting levels; CLI `gh issue create --parent`, `gh issue edit --add-sub-issue`; GA status (unverified); API not on this page | docs page | https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues |

Impact on the plan: the GitHub App credential works only for **organization-owned** projects; a user-owned project needs a PAT (decision at G1).

## Approvals

| Gate | Date | Scope approved | User words |
|---|---|---|---|
| plan | 2026-10-29 | plan file poderia-me-ajudar-aqui-curious-sunbeam.md | ExitPlanMode approved; decisions quoted in PACKAGE_BRIEF.md |
| G1 | 2026-10-29 | U1-U7, names, gh 2.103.x, credential App+PAT | "Suportar os dois"; "2.103.x, eu atualizo o gh (Recomendado)"; "Aprovo, seguir com U1 + piloto U2" |
| G2 | 2026-10-29 | pilot U2 accepted; full P4-P6, rounds=3; user-owned projects kept with classic PAT + risk warning | "Aprovo, seguir com P4–P6 completo (Recomendado)"; "Manter, com aviso de risco (Recomendado)" |
| P6-F1 | 2026-10-29 | audit F1 remediation + deny-rule snippet | "Login local ≠ approver (Recomendado)"; "Sim, documentar snippet (Recomendado)" |
| G3 | 2026-10-29 | 6 local commits; fix L1-L3 first; keep command name, naming-rule follow-up | "Approve the 6 commits (Recommended)"; "L3: pin the commit across jobs, L2: document the residual npm risk, L1: comment on GITHUB_ACTIONS"; "Keep it, follow-up on the rule (Recommended)" |

## Units
| Unit | Source item | Skill / artifact | Research file | State | Score | Tokens |
|---|---|---|---|---|---|---|
| U1 | split OpenSpec | openspec-core (move specifying-changes-with-openspec-v1-15) | n/a | VALIDATED | | |
| U2 | gh + Projects v2 | github-core: managing-github-projects-gh-v2-103 (proposed) | research_GitHub_Projects_gh_v2.103.md | VALIDATED | 88.5 -> ~96 (M fixed) | research 172k / 8.5 min; author 141k / 5 min; validate 126k / 5 min; fix ~20k / 2.5 min |
| U3 | Actions automation | github-core: automating-github-repos-with-actions | research_GitHub_Actions_repo_automation_2026-10.md | VERIFIED | | research 159k / 7.6 min; author 146k / 4 min |
| U4 | bridge | openspec-github: syncing-openspec-with-github-projects + scripts + 4 workflows | DESIGN_U4.md + U2/U3 + family facts | VERIFIED | | |
| U5 | bridge exec | agent openspec-github-syncer, command /syncing-openspec-to-github, rule | n/a | VERIFIED | | |
| U6 | protocol | handoff-core: tracker: block + validation + test | n/a | VERIFIED | | |
| U7 | consumer | quarkus-aws-saas: preflight, E1, E8, E9, profile | n/a | VERIFIED | | |

## Quality loop
| Round | Validate | Test | Audit | HIGH | Decision |
|---|---|---|---|---|---|
| P3 pilot r1 (U2) | 88.5 (0H/3M/8L) | - | - | 0 | M-1..M-3 + L-1/5/6/7 fixed; L-2/3/8 left; verify_skill exit 0 |
| P6 r1 | A: 99.0/90.5/99.0/99.0/97.0 (0H/4M); B: 98.0/100/99.5/100 (0H/0M/5L) | 21/21 scenarios pass | CONDITIONAL 8.0/6.8/6.5, 2 HIGH (F1, F2) | 2 | code: verify step moved before token mint (4 workflows), bot_login/approvers clash checked always; docs fix briefs sent to both authors |

## Log
- 2026-10-29  P0  preflight ok (5 workers, researching-technical-frameworks, skill-creator, agent-creator); workspace created
- 2026-10-29  P1  version gate fetched (4 sources); waiting G1
- 2026-10-29  G1  approved: credential App (org) + PAT (user) via tracker.owner_type; gh pinned 2.103.x
- 2026-10-29  U1  moved skill to packages/openspec-core; handoff-core depends on it; apm lock+install: .claude unchanged byte-for-byte, lock = ownership move + new entry; handoff tests 35 ok / 5 known git-init sandbox errors
- 2026-10-29  P3  U2 research launched (framework-researcher)
- 2026-10-29  P3  U2 RESEARCHED (568 lines); F5 resolved, F6 added, rules 5/7 fixed after orchestrator re-verification
- 2026-10-29  P3  U2 AUTHORED (11 files, SKILL.md 111 lines); verify_skill.py exit 0 -> VERIFIED
- 2026-10-29  P3  U2 VALIDATED; M-1 resolved by orchestrator fetch of v2.99.0 tag page; waiting G2
- 2026-10-29  G2  approved full P4-P6; classic PAT for user projects kept with risk warning
- 2026-10-29  P4  U3 research launched; U6 done by orchestrator: validate_tracker() + 5 tests (45 run, 40 ok, 5 known git-init sandbox errors); profile-format.md#tracker
- 2026-10-29  P4  U3 RESEARCHED; F7-F10 added (SHAs re-verified via git ls-remote), rules 8/11/12; cross-package links in handoff-core converted to name references (verify_skill OK)
- 2026-10-29  P4  U3 author launched; DESIGN_U4.md written; U4 scripts/tests/workflows implementer launched (general-purpose, Bash)
- 2026-10-29  P4  U3 AUTHORED (10 files, SKILL.md 122 lines, 7 scenarios); verify_skill exit 0 -> VERIFIED
- 2026-10-29  P5  U4 scripts/tests/workflows done (369k tok / 41 min); orchestrator re-ran 77 tests OK (1 skip actionlint), injection/pin/permissions checks clean; F11 added (updatedAt in schema)
- 2026-10-29  P5  U7 done (125k / 2 min): SKILL.md 183 lines, new blueprint tracker-github-projects.md; verify_skill OK x2; profile loads with tracker kind none; apm.yml dep + README by orchestrator. LOW: scenarios 10/11 placed before 9
- 2026-10-29  P5  U4 docs + U5 authored (207k / 6 min); verify_skill x2 + verify_package OK
- 2026-10-29  P5  orchestrator fixes from author triage: trusted_author fails closed; bot_login required for github-projects (handoff-core validate_tracker); install_workflows checks all conflicts before writing; +3 regression tests -> bridge 80 OK (1 skip), handoff-core 45 (5 known git-init errors)
- 2026-10-29  P8a apm lock+install (33 deps). Found: APM skipped 3 handoff-core files flagged 'modified since deployment' (U1 link fixups) and deleted coordinating-quarkus-aws-handoffs/SKILL.md once; fixed by deleting stale deployed copies + reinstall; byte-compare 1653 source files vs .claude: 0 problems; installed bridge tests 80 OK without env var
- 2026-10-29  P6  r1 validate A+B and test done (0 HIGH); orchestrator code fixes; fix briefs sent; audit next (foreground, alone)
- 2026-10-29  P6  r1 audit: CONDITIONAL, F1/F2 HIGH re-checked in files (confirmed); user decided F1 = local gh login must not be an approver when approval_source != chat; deny-rule snippet documented
- 2026-10-29  P8b audit F3 fixed by orchestrator: CLAUDE.md (counts 226/67/159/41/50/32, OpenSpec+GitHub paragraph, package tree, how-to-run), README.md + docs/ counts from check_counts.py
- 2026-10-29  P6  code fix brief (F1,F2,F5,F6,F7,F12,F4-code) sent to implementer
- 2026-10-29  user asked if --ignore-scripts was verified: orchestrator read npm registry manifest (no install scripts, pure-JS deps); R17 unverified -> medium confidence
- 2026-10-29  P6  r2 validate: 25/25 round-1 closed, N1/N2 MEDIUM fixed (docs + check-patch + 3-job archive), 107 tests OK (4 skips)
- 2026-10-29  P6  r3 audit PASS 8.9/8.7/8.6, all HIGH/MEDIUM closed; LOW L1-L3 left for G3
- 2026-10-29  P8  apm install (33 deps), byte-compare 1562 skill files 0 problems, verify_package x5 OK; commit-plan.json dry-run clean (6 groups); waiting G3
- 2026-10-29  G3  L1 comment, L2 docs, L3 ref pin applied; README follow-ups; 107 tests OK; reinstall + byte-compare clean
