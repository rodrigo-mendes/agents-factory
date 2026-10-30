# CC Architecture Multi-Model Report - aws-saas-serverless-quarkus-react-nextjs

Date: 2026-10-30. Target: `C:\agents\agents-factory\packages\aws-saas-serverless-quarkus-react-nextjs` + 21 flow agents (`packages\*\.apm\agents\*.agent.md`) + rules `nextjs-static-export`, `openspec-project-layout`. Read-only audit; the three lens agents ran in parallel with model sonnet (fan-out depth 1). The P3 plan-mode confirmation was skipped: the caller fixed the output path in the task and the plan-mode tools were not available to this run.

Path shorthand (all under `C:\agents\agents-factory\packages\`):
- SKILL-B = `aws-saas-serverless-quarkus-react-nextjs\.apm\skills\building-aws-saas-serverless-quarkus-react-nextjs\SKILL.md`
- PROFILE = `aws-saas-serverless-quarkus-react-nextjs\.apm\skills\coordinating-quarkus-aws-handoffs\assets\handoff-profile.yaml`
- OBS = `aws-observability\.apm\agents\aws-observability.agent.md`

## 1. Executive Summary

Consensus Verdict: PASS (no 3/3 finding, no HIGH, all models >= 7.0), with 8 MED findings to fix.

| Model | Overall | Unique (1/3) findings |
|---|---|---|
| A Scope | 7.2 (G0 9, G1 7.0, G2 6.5, G3 n/a, G4 7.5) | 15 raised, 12 stay single after merging |
| B Flow | 8.4 | 6 |
| C Engine | 8.3 | 3 groups (budget, doc counts, Windows) |

Model A Overall 7.2 / Model B Overall 8.4 / Model C Overall 8.3.

Verified counts (ls/grep/wc by lenses, spot-checked here): 21 flow agents, all with a source `.agent.md`; 3 skills (219 / 229 / 118 lines, all < 500); profile `roles:` = 20; `model: opus` only in solution-architect and aws-infrastructure-architect, the other 19 `sonnet`; no flow agent has the Agent tool (only architecture-auditor, book-orchestrator, skill-evaluator, framework-researcher do, none in this flow); `applying-aws-well-architected` occurs 0 times in the package skills (grep -rn, verified).

Findings: 3/3 = 0, 2/3 = 5 (2 MED, 3 LOW), 1/3 = 20 (6 MED, 14 LOW). Totals: HIGH 0, MED 8, LOW 17 (25).

Author != reviewer matrix (SKILL-B 127-142 vs PROFILE `next` rules vs agent descriptions): consistent for all deliverables (E1, E2a, E2b, E2c, E3, E3b, E4, E5, code, Stripe, AI, front, infra, observability, cicd, deploy, E8), each with a distinct reviewer, a reachable chain and no dead end. The gaps are ordering (S1) and enforcement (U1).

## 2. Consensus Findings (3/3) - MUST FIX

None. No issue was independently reported by all three lenses.

## 3. Two-Model Findings (2/3) - SHOULD FIX

**S1 MED - final-gate can fire before static-site-verifier runs (B FCC.7/10 + C engine simulation).**
- PROFILE:132-133: `verify role: debug pass, all_tasks: done` -> `final-gate`; the comment at 134-135 admits the site verify runs after the debugger.
- `building-aws-saas-serverless-quarkus-react-nextjs\blueprints\e7-deploy-and-observability.md:63` says to set `wo-*-site-verify` to `done` BEFORE board.py runs on the verify, so `all_tasks` is already done. C simulated it: debug pass + all_done gives `final-gate`.
- Dissent: A did not examine rule routing order (outside the scope lens).
- Fix: create `wo-*-site-verify` as `pending` until its verify exists (edit e7:63), or add a profile rule before line 132 routing the debug pass to `site-verify` while a pending site-verify wo exists.

**S2 MED - aws-observability: four modes, overlap with aws-terraform-engineer, no independent verdict on E2c section 8 (A G1.1/XCC.8 + B FCC.7).**
- OBS:43/62/72/83 (Modes A-D) with `tools: Read, Grep, Glob, Edit, Write, Bash` (OBS:10): read-only modes get Write/Edit; the profile needs 3 role values (PROFILE:118-126).
- `terraform\.apm\agents\aws-terraform-engineer.agent.md:97,118` routes CloudWatch/X-Ray to the same skills as OBS:64; the partition is stated only one way (OBS:131, roles-and-skills.md:76-77).
- `aws-architect\.apm\agents\aws-infrastructure-architect.agent.md:61` writes E2c section 8 (observability) but `aws-architect-reviewer.agent.md:44-48` has no observability criterion; Mode A yields a report with no pass/fail (PROFILE:118-124; OBS:22 "never verify").
- Fix: add an observability/CI-CD criterion to aws-architect-reviewer step 3; add "observability resources are not yours" to `assets\wo-infra.template.md`; optionally split Modes A/C into a read-only validator.

**S3 LOW - nextjs-static-export rule duplicates agent Never-Do and its glob is broad (A XCC.8 + C ECC.2).**
- `nextjs-frontend\.apm\instructions\nextjs-static-export.instructions.md:4` (`**/frontend/**,**/next.config.*`) fires on any Next project, including SSR ones; Never-Do at 34-43 duplicates `nextjs-frontend-integrator.agent.md:107-111`.
- Fix: state the `output: 'export'` precondition in the rule's first line; the agent links to the rule.

**S4 LOW - "read-only" Bash enforced only by prose (A G1.2 + C ECC.16).**
- `handoff-core\.apm\agents\spec-synchronizer.agent.md:31` ("the Bash tool itself is not restricted"), `aws-lambda-debugger.agent.md:15`, `static-site-verifier.agent.md:12`; settings.json has no matching permission rules.
- Fix: ship a recommended `permissions.allow/deny` snippet in the package README.

**S5 LOW - orchestrator is an inline skill without `argument-hint` and auto-invocable (A G3 + C ECC.5; B: fork criteria N/A by design).**
- SKILL-B:2-4, 98. Intentional per factory convention (`skill-frontmatter.md` forbids the unpaired flag); a vague request could still auto-start an E1-E9 run.
- Fix: add `argument-hint`; tighten the "Use when" wording.

## 4. Single-Model Findings - CONSIDER

| ID | Model | Sev | Criterion | Location | Issue / Likely real? / why others missed |
|---|---|---|---|---|---|
| U1 | B | MED | FCC.20 | SKILL-B:155 vs `handoff-core\.apm\skills\coordinating-agent-handoffs\scripts\check_records.py:79-83` | Claim "verify.from / review.from must differ ... check_records.py enforces it" holds for `kind == verify` only. Review records ref a wo-review authored by the orchestrator, so code/Stripe/AI/front/infra/cicd review independence is procedural. REAL (both files read here). A and C do not check script semantics against prose claims. Fix: reword the claim, or compare review.from with the author of the result-* of the same task. |
| U2 | A | MED | XCC.4/8 | `openspec-core\.apm\instructions\openspec-project-layout.instructions.md:41-52,59-60` | Rule names solution-architect, ui-ux-designer, reviewers and a manager procedure, while openspec-core is "reusable without handoff". REAL. Fix: keep layout + ADR format; move the table to the orchestrator. |
| U3 | A | MED | XCC.3/8 | `aws-architect-reviewer.agent.md:41,44`; knowledge-map.md:74 | The reviewer's main skill `applying-aws-well-architected` is in no knowledge-map/roles list (grep = 0), so the six-pillar review is unreachable by the selection rule. REAL (verified). |
| U4 | A | MED | XCC.8 | `agent-alignment.md:19`; coordinating SKILL.md:94 vs `ui-design\.apm\agents\ui-ux-designer.agent.md:8,23-24,69` | Profile docs say the designer writes `result-NN-designer.md`; the agent has no Write (orchestrator saves). REAL doc contradiction. |
| U5 | A | MED | XCC.2 | agent-alignment.md:40,43 | Protocol translation (DONE/PARTIAL -> outcomes; native verdict -> approved/changes-requested) lives in manager briefs because generic agents are not handoff-aware. Accepted trade-off; record it in unverified-and-risks.md. |
| U6 | C | MED | ECC.4/13 | `.claude\skills` project-wide | 256 skills, 188 auto-invocable, ~53k chars of descriptions per session; this package adds 3 plus 20 Vercel skills, including OUT skills (knowledge-map.md:53). Project-wide, not package-specific. |
| U7 | B | LOW | FCC.7 | PROFILE:35 | One `reviewer` role for six agents; NEXT lists all six; choice relies on the wo-review variants table (`wo-review.template.md:21-29`) not restated in SKILL-B. |
| U8 | B | LOW | FCC.10 | PROFILE:72-77 | Design-author fix loops have no counter; "escalate after two failed verifies" exists only as a YAML comment. |
| U9 | B | LOW | FCC.7 | `github-actions-cicd\.apm\agents\cicd-pipeline-engineer.agent.md:24-25` | "(spawned via the Agent tool)" wording; no Agent tool, depth 1 holds. Reword to "the caller launches". |
| U10 | B | LOW | FCC.7 | stripe-integrator, aws-terraform-engineer, cicd-pipeline-engineer | No explicit no-spawn line (worker-briefs.md:18 forbids it). Hygiene only. |
| U11 | B | LOW | FCC.20 | worker-briefs.md:116; e7:63 | No profile templates for verifier/sync/site-verify work-orders; the `task:` field can be omitted. |
| U12 | A | LOW | XCC.8 | OBS:28-31 + 5 other copies | Approval-line format duplicated in 6 places; link to approval-lines.md. |
| U13 | A | LOW | XCC.8 | OBS:91-110; aws-architect-reviewer.agent.md:37-58 | Record templates inlined in agents. |
| U14 | A | LOW | G1.1 | aws-lambda-debugger.agent.md:62,70; spec-synchronizer.agent.md:45,59 | Two modes each; "Mode B" means four different things across agents. |
| U15 | A | LOW | XCC.3/4 | spec-synchronizer.agent.md:7-8; static-site-verifier.agent.md:25-27 | Generic agent hard-codes this flow; static-site-verifier names skills outside its package deps. |
| U16 | A | LOW | XCC.1/7 | aws-architect.agent.md:3-12; package apm.yml:15; SKILL-B:189 | Three confusable aws-architect* names; `../aws-lambda` pulls the deployer and preflight rule although deploy "left the flow". Consider renaming the reviewer to aws-infrastructure-reviewer. |
| U17 | A | LOW | XCC.2 | SKILL-B:129,170 | Orchestrator authors E1/E3/E5 and work-orders; accepted by the plan; spec-synchronizer reviews. No change. |
| U18 | A | LOW | XCC.4 | SKILL-B:88-94; agent-alignment.md:5-6 | Preflight does not check the rule files; stale "authored separately" sentence; knowledge-map.md:89 says "Modes A/B/C" but the agent has Mode D. |
| U19 | C | LOW | ECC.14 | `C:\agents\agents-factory\CLAUDE.md` | C reports 246/41/50 vs actual 256/54/56; A read a CLAUDE.md that already lists the package. Lenses conflict; recount with ls before editing. |
| U20 | C | LOW | Windows | OBS:76-78 (`python3`); spec-synchronizer.agent.md:36 (`python`); aws-lambda-debugger.agent.md:106 and static-site-verifier.agent.md:56,77 (`date -u`, `sha256sum`); nextjs-frontend-integrator.agent.md:71 (sha256 of `out/` undefined); aws-terraform-engineer.agent.md:73,80 (`env -u`, `/dev/null`); e4-e5-design-and-tasks.md:95 | Windows portability group, engine-only. Fix: use `python`, copy the python fallback of OBS:108, define one sha256 manifest method shared by integrator and verifier. |

## 5. Per-Model Detailed Results

5.1 Model A: G0 9 / G1 7.0 / G2 6.5 / G3 n/a (7.5 imputed) / G4 7.5 -> 7.2. Pair design author -> independent reviewer is clean; weak spots S2, U2, U4.
5.2 Model B: Commands 9 / Delegation hub 8.5 / Rules 8 (partial evidence) / Skills 8.5 -> 8.4. Not read in full: blueprints e1-e9 (partly), the two rules, detect_drift.py.
5.3 Model C: paths 8 / Budget 7 / Fork-disclosure 9 / Conflicts 9 / Frontmatter 9 -> 8.3. Profile parses via _mini_yaml; 38 simulated states all routed; 17 templates parse; agent sources byte-identical to generated `.claude\agents`.

## 6. Unified Remediation Roadmap

| Priority | Issue | Consensus | Action | File | Effort |
|---|---|---|---|---|---|
| 1 | S1 premature final-gate | 2/3 | Keep site-verify wo `pending` until its verify exists, or add routing rule | e7-deploy-and-observability.md:63; PROFILE:132 | S |
| 2 | S2 observability overlap / no verdict | 2/3 | Reviewer observability criterion; partition line in wo-infra | aws-architect-reviewer.agent.md:44; wo-infra.template.md | M |
| 3 | U1 review independence unenforced | 1/3 real | Reword claim or extend check_records.py | SKILL-B:155; check_records.py:79 | S/M |
| 4 | U3 missing well-architected skill | 1/3 real | Add to knowledge-map Wave 6 and roles-and-skills | knowledge-map.md:74 | S |
| 5 | U4 designer Write contradiction | 1/3 real | Fix 2 doc rows | agent-alignment.md:19; coordinating SKILL.md:94 | S |
| 6 | U2 rule leak in openspec-project-layout | 1/3 real | Trim rule, link the orchestrator | openspec-project-layout.instructions.md:41-60 | S |
| 7 | S3 / S4 / S5 | 2/3 | Rule precondition; permissions snippet; argument-hint | see section 3 | S |
| 8 | U20 Windows portability | 1/3 | Interpreter and hash methods | see U20 | M |
| 9 | LOW doc/hygiene U7-U19 | 1/3 | Batch edit | see section 4 | S |

## 7. Model Effectiveness Analysis

- Unique findings: A 15 raised (most real doc/ownership issues), B 6 (U1 and S1 the most actionable), C 3 groups (S1 corroboration, Windows).
- False positives: none identified; U5, U17, U6 are accepted trade-offs rather than defects; U19 conflicts between lenses and needs a recount.
- Most actionable: S1 (breaks the E7 -> E9 order) and U1 (independence claim not enforced by the script).
- Re-audit recommended: Flow lens after fixing S1, reading blueprints e1-e9 and detect_drift.py in full.

## 8. Conclusion

The family is structurally sound: depth 1 holds, the model split matches the plan, the profile parses and routes every simulated state, the author/reviewer matrix agrees across SKILL, profile and agents, and frontmatter is valid. No lens found a 3/3 defect. The recurring theme is gates described in prose that the scripts do not enforce (S1, U1). Expected scores after priorities 1-6: A about 7.8, B about 9.0, C about 8.6.
