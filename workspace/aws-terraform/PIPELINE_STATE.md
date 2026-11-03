# Pipeline state — aws-terraform

```yaml
slug: aws-terraform
mode: new
current_phase: P3
reconstructed: false
rounds: 3
```

## Approvals

| Gate | Date | Scope approved | User words |
|---|---|---|---|
| G1 | 2026-10-14 | New aws-terraform package + terraform-engineer; 26 skills one per service; pilot networking (→ VPC) | "AWS: novo pacote aws-terraform + engineer" / "26 skills, uma por serviço" / "networking (VPC/Route53/CloudFront/ACM)" |
| G1b (version) | 2026-10-14 | Terraform target changed 1.15.x → 1.16.x; provider ~> 6.69 | "Mirar 1.16.x (Recomendado)" |
| G2 | 2026-10-14 | Full fan-out of 25 units, 7 batches ≤4; suffix `-v6` kept | "Aprovar fan-out completo (Recomendado)" / "Manter `-v6` (Recomendado)" |
| G3-A (family decisions) | 2026-10-23 | A1 keep High for `main` provider pages + document convention; A2 keep 'medium severity' in body; A3 unify read dates of B1–B4 skills to 2026-10-23 in P7 (A4 already decided 2026-10-22: keep ~> 1.16) | "Manter alta e registrar a convenção (Recomendado)" / "Manter 'medium severity' (Recomendado)" / "Unificar para 23/10 no P7 (Recomendado)" |
| G3-B (P6 audit decisions) | 2026-10-23 | S1 keep terraform-engineer in packages/terraform (user's Frente 1 decision); E1 shorten the 26 skill descriptions (~160–200 chars, no repeated version text); S4 rename agent to `aws-terraform-engineer` (command `provision-aws-terraform` unchanged) | "Manter em packages/terraform (sua decisão)" / "Encurtar as descrições (Recomendado)" / "Renomear aws-terraform-engineer" |
| G3 (commit plan) | | | |

## Version gate (P1)
- hashicorp/aws: research 6.47.0 → current ~6.65.0 (Sep 2026), no v7 seen.
- Terraform: research 1.7/1.9 (EOL) → current 1.15.x.

## Log
- 2026-10-14  P0  brief + state created
- 2026-10-14  P1  version gate: provider still 6.x; Terraform core in old research is EOL
- 2026-10-14  G1  approved (see above)
- 2026-10-14  P3  pilot research launched: vpc
- 2026-10-14  P3  researcher handed back INCOMPLETE (no file written); confirmed aws 6.69.0 latest (2026-10-14), no v7; 4 nested section-investigators still running (core, security, endpoints/flowlogs/IPAM, TF 1.15 testing) — wait, then synthesize
- 2026-10-14  P3  investigator core (a214038fa16a35a3c) DONE — 14 official sources; regional NAT (`availability_mode`) CONFIRMED; gaps: eip `domain` default, main_route_table_association import
- 2026-10-14  P3  investigator endpoints/flowlogs/IPAM (aeee5ebc69ad3d237) DONE — 15 official sources; flow_log `log_group_name` absent (use log_destination); gateway endpoints only S3/DynamoDB, free; NOTE: injected `system-reminder` block found in docs.aws.amazon.com flow-logs-basics page fetch — disregarded
- 2026-10-14  P3  investigator security (a0200b42483ff63bb) DONE — 15 official sources; aws_security_group_rule = discouraged (NOT deprecated); per-direction rule resources = "current best practice"; Security Hub EC2.2/6/13/14/19/53/54
- 2026-10-14  P3  investigator TF testing (ab3ab278f1e87da70) DONE — tftest/mocking/validate/plan exit codes; S3 `dynamodb_table` DEPRECATED, use `use_lockfile`
- 2026-10-14  P1  VERSION GATE REOPENED: orchestrator WebFetch releases.hashicorp.com/terraform → newest stable **1.16.6 (2026-10-14)**; 1.16.0 = 2026-08-26; 1.17.0-rc2 exists. Brief's "1.15.x" is NOT current → ask user before synthesis
- 2026-10-14  G1b user chose Terraform 1.16.x
- 2026-10-14  P3  vpc RESEARCHED — research_AWS_VPC_tf-aws-v6.md synthesized by orchestrator (60 sources; inspect_workspace: COMPLETE); research cost ≈ 85k + 146k investigators ≈ 231k tokens
- 2026-10-14  P3  artifact-author launched for provisioning-aws-vpc-v6
- 2026-10-14  P3  vpc AUTHORED (~160k author tokens incl. 1 fix pass: description 377→287, blueprints split by topic ≤160 lines, always-do/never-do kept as index hubs); verify_skill OK, verify_package OK → VERIFIED
- 2026-10-14  P3  round-1 validation launched: quality-validator + skill-evaluator → validation/round-1/
- 2026-10-14  P3  round-1: evaluator 4/4 scenarios (24/24 must_pass, 0 must_not); validator 0 HIGH / 2 MED / 2 LOW, 30/30 facts confirmed. Fixed F-M2, F-L1, F-L2 (orchestrator); F-M1 (-v6 vs -vMAJOR-MINOR) → G2 decision. verify_skill OK → VALIDATED
- 2026-10-14  P3  pilot cost ≈ 491k subagent tokens (research 231k incl. nested investigators, author 160k, validation 101k)
- 2026-10-14  G2  approved full fan-out + `-v6` suffix
- 2026-10-14  P2  _family_facts_v6.md seeded (F1–F13, verified in pilot); shared briefs in briefs/{research,author}-brief.md (flat: no sub-agents)
- 2026-10-14  P4  batch plan: B1 iam,kms,s3,cloudwatch · B2 route53,acm,cloudfront,waf · B3 shield,cloudtrail,organizations,secrets-manager · B4 parameter-store,dynamodb,sqs,sns · B5 lambda,api-gateway,eventbridge,step-functions · B6 cognito,ses,xray,cost-management · B7 sam
- 2026-10-14  P4  B1 research launched (4 researchers)
- 2026-10-14  P7  FACT CHANGE: F5 narrowed (global services don't accept `region`); F14 (global services list) + F15 (`data.aws_region.name` → `.region`; S3 `bucket_region`) added — orchestrator WebFetch of enhanced-region-support + version-6-upgrade guides. Sweep: vpc unaffected (grep); s3 author notified mid-run; iam author briefed. Future B2/B3/B6 (cloudfront, route53, organizations, shield, cost-management, waf) must apply F14.

- 2026-10-14  P4  B1 lesson: authors state ungrounded claims as facts despite the brief (S3: 2 HIGH, ~6 unsupported claims) and misreport line counts → for B2+ the author brief must say "every sentence of a ✅/🚫 bullet must be in the research; remove, don't paraphrase from memory", and I run verify_skill immediately on delivery. Quality-validator now runs on EVERY unit, not a sample, if the B1 rate repeats (decision pending after S3 re-validation).
- 2026-10-14  P4  user asked to wait for S3 to close before B2 (explicit choice "Esperar o S3 fechar primeiro")

- 2026-10-22  P1  VERSION RECHECK before B2: Terraform 1.17.0 stable (2026-10-21, no breaking changes); aws provider 6.70.0 (6.69.1 also). User chose "Manter `~> 1.16` (Recomendado)" → F1/F2/F3 updated, briefs re-dated 2026-10-22, author brief gained a grounding rule. 1.17.0 = version-lifetime risk in every skill; one light review pass of Version Context after fan-out.
- 2026-10-22  P4  B1 CLOSED (iam, kms, s3, cloudwatch validated); user approved B2 ("Sim, iniciar o lote 2 (Recomendado)" → quality-validator on every unit)
- 2026-10-22  P4  B2 research launched: route53, acm, cloudfront, waf
- 2026-10-22  P7  FACT CHANGE: F16 added (carve-outs to F14, verified by orchestrator on resource pages): `aws_route53_resolver_*` and all `aws_wafv2_*` accept `region` (regional). Sweep: no B1 skill depends on it. B2 authors briefed. B2 research done (~420k tokens); 4 authors launched

- 2026-10-22  P4  B2: all 4 units authored+fixed, verify_skill OK on 9/9 skills, verify_package OK. User instruction (mid-turn): ask permission BEFORE starting the next block → B3 NOT launched until the user confirms.
- 2026-10-22  P4  B2 CLOSED: route53/acm/cloudfront/waf validated; 9/9 skills verify_skill OK; verify_package OK. Waiting for user permission to start B3 (shield, cloudtrail, organizations, secrets-manager).

- 2026-10-23  P4  B3 approved by user ("Sim, iniciar o lote 3 (Recomendado)"); versions rechecked (aws 6.70.0, Terraform 1.17.0 stable, no change); briefs re-dated 2026-10-23; B3 research launched: shield, cloudtrail, organizations, secrets-manager
- 2026-10-23  P4  B3 research done (~375k tokens; no fact change; F14 confirmed for shield/organizations — no carve-outs). Briefs for authors forbid F#/M# ids in shipped text (lesson from route53 round 1). 4 authors launched.
- 2026-10-23  P4  B3 lesson (3rd occurrence: s3 round-1, organizations, secrets-manager): authors turn research "legacy claim wrong/unsupported" items into 🚫 rows built on absence of evidence. author-brief.md now has an explicit Never-Do rule (High + sourced only, 1:1 with blueprint entries), Always-Do-high-only rule and example/URL rules for B4+.
- 2026-10-23  P4  B3 CLOSED: shield, cloudtrail, organizations, secrets-manager validated; 13/13 skills verify_skill OK, verify_package OK. Waiting for user permission to start B4 (parameter-store, dynamodb, sqs, sns).
- 2026-10-23  P4  B4 approved by user ("Sim, iniciar o lote 4 (Recomendado)"); B4 research launched: parameter-store, dynamodb, sqs, sns (versions unchanged since morning recheck)
- 2026-10-23  P4  B4 research done (~400k tokens); 4 authors launched with the hardened author brief. Notable: SQS/SNS 'do not mix inline policy' = inference → Ask First; DynamoDB research found alias/aws/dynamodb is the AWS MANAGED key (legacy said owned).
- 2026-10-23  P4  B4 CLOSED: parameter-store, dynamodb, sqs, sns validated; 17/17 skills verify_skill OK, verify_package OK. Waiting for user permission to start B5 (lambda, api-gateway, eventbridge, step-functions).
- 2026-10-23  P4  B5 approved by user ("Sim, iniciar o lote 5 (Recomendado)"); B5 research launched: lambda, api-gateway (REST v1 + HTTP/WebSocket v2 separated), eventbridge, step-functions
- 2026-10-23  P4  B5 research done (~456k tokens); 4 authors running. Notable: sfn_state_machine_version does not exist (404); API Gateway research found real 6.0 removals (reset_on_delete; deployment stage_name etc.).
- 2026-10-23  P4  B5 finding (G3, family-level): authors stamp one blanket read date on every source; facts-file sources (F1/F5/F6/F7/F11 read 2026-10-14, F3 2026-10-22) need per-source dates. Authors told to date each row; consider refreshing the facts file reads before the final commit.
- 2026-10-23  P4  B5 CLOSED: lambda, api-gateway, eventbridge, step-functions validated; 21/21 skills verify_skill OK, verify_package OK. Facts file: F17-F19 added, F1 updated (1.16.7), shared-fact sources re-read 2026-10-23. Waiting for user permission to start B6 (cognito, ses, xray, cost-management).
- 2026-10-23  P4  B6 approved by user ("Sim, iniciar o lote 6 (Recomendado)"); B6 research launched: cognito, ses (v2 primary), xray, cost-management (global per F14 — verify per page).
- 2026-10-23  P4  B6 research done (~450k tokens); 4 authors running with the lessons text (Never=High only etc.). Notable: aws_sesv2_account_vdm_options does not exist (vdm_attributes); X-Ray SDK/Daemon maintenance mode 2026-02-25; Cost Mgmt savings plan resource is aws_savingsplans_savings_plan.
- 2026-10-23  P4  B6 CLOSED: cognito, ses, xray, cost-management validated; 25/25 skills verify_skill OK, verify_package OK. Waiting for user permission to start B7 (sam) — scope decision needed first (SAM is not an aws provider resource).
- 2026-10-23  P4  B7 scope decided by user ("SAM com Terraform") and B7 start approved ("Sim, iniciar o lote 7 (Recomendado)"); SAM research launched.
- 2026-10-23  P4  FAN-OUT COMPLETE: 26/26 skills authored and validated (B1–B7). Next: P5 (terraform-engineer agent in packages/terraform + aws-terraform rules/README/apm.yml), P6 quality loop on the agent, P7 fact sweep, P8 apm install + counts, then G3 commit plan. Waiting for user permission before P5.
- 2026-10-23  P5  approved by user ("Sim, iniciar o P5 (Recomendado)"); artifact-author launched: terraform-engineer agent + provision-aws-terraform router (packages/terraform), aws-terraform instructions + README + apm.yml (both packages).
- 2026-10-23  P5  DONE (author report): terraform-engineer agent (123 l), provision-aws-terraform router (81 l + evaluation-scenarios 28 l), aws-terraform instructions x3 (61/50/23 l), README (70 l), apm.yml x2 (terraform 1.2.0 + dep ../aws-terraform). verify_package aws-terraform OK (26 skills, 3 rules); packages/terraform verify_package: only pre-existing cross-package links (resolve at apm install); action skill is not a verify_skill target (and verify_skill crashes printing emoji on cp1252). Next: P6 quality loop on agent+instructions+router (waiting for user permission).
- 2026-10-23  G3  reviewed with the user (G3_DECISIONS.md): A1–A3 decided; P6 approved ("Sim, iniciar o P6 (Recomendado)"). Commit plan (2 commits) still to be approved after P6–P8.
- 2026-10-23  P6  round 1 done: quality-validator 3 HIGH / 5 MED / 8 LOW (terraform test + real provider safety hole; eval-scenarios not in JSON format; `~> 1.16` admits 1.17+ so 'never 1.17' wording is wrong → reword, constraint unchanged per user), skill-evaluator 12/15 (S1 scenario bug, safety gaps: state/lock file deletion, -lock=false, migrate-state), architecture-auditor 7.5/10 (2 HIGH: S1 dependency direction → user kept; E1 26 auto-invoke descriptions → shorten). Two authors launched: (A) agent/router/instructions/README/apm.yml fixes + rename; (B) 26 skill descriptions.

## Units
| Unit | State |
|---|---|
| vpc | VALIDATED |
| kms | VALIDATED (evaluator 4/4, 22/22 must_pass, 0 must_not violated) |
| cloudwatch | VALIDATED (evaluator 4/4, 24/24); fixed undefined `security_alerts` topic + reworded S3-class criterion; skipped create_before_destroy recipe (ungrounded) |
| s3 | VALIDATED round 2: 0 HIGH, 6 MED fixed by orchestrator (N-M1..N-M6; N-M4 was actually inverted — SSE-S3 FAILS S3.17), 14 new LOW left for G3 list; verify_skill OK |
| iam | VALIDATED (evaluator 4/4, 28/28 must_pass, 0/19 must_not); reworded 2 region criteria (backend region allowed); left scen.3/4 hardening as optional |
| route53 | VALIDATED round 2 (0 HIGH; N-1 fixed — Resolver `region` scoped to the 3 checked resources + (medium confidence) M1; N-2/L-2/L-4/L-6/L-7 + 6 LOW → G3 list) |
| acm | VALIDATED (0 HIGH; 6 MED + most LOW fixed; verify_skill OK) |
| cloudfront | VALIDATED (0 HIGH; 7 MED fixed, U9 logging-v2 args left unverified, U10/U11 added; verify_skill OK) |
| waf | VALIDATED (0 HIGH; HCL shapes verified on 4 raw pages; 6 MED fixed; verify_skill OK) |
| shield | VALIDATED (0 HIGH; 3 MED + 6 LOW fixed; verify_skill OK) |
| cloudtrail | VALIDATED (0 HIGH; 3 MED fixed, LOW mostly fixed; verify_skill OK; skipped: dated URLs on sibling-grounded HCL) |
| organizations | VALIDATED round 2 (0 HIGH; N-1 Never rows 9=9 fixed, loose mapping row removed, blank line added; N-2/L-8 main-branch confidence cap = family-level decision for G3; N-3/N-5 LOW left; verify_skill OK) |
| secrets-manager | VALIDATED round 2 (0 HIGH; N1–N4 MED fixed by orchestrator; LOW incl. L-1 example markers, register counts, ephemeral→write-only HCL left for G3; verify_skill OK) |
| parameter-store | VALIDATED round 2 (0 HIGH; R2-M1..M4 fixed by orchestrator; LOW: region cite, identity-import source mismatch, hubs unlinked, bullets with 2 facts → G3; verify_skill OK) |
| dynamodb | VALIDATED (0 HIGH; 8 MED + most LOW fixed; U6 resolved from provider page, U1 write-metric stays unverified; verify_skill OK; no round 2 needed) |
| sqs | VALIDATED round 2 (0 HIGH; M6/M8 citation fixes by orchestrator; M5 orphan U2/U4 'registered only' = accepted family convention; LOW → G3; verify_skill OK) |
| sns | VALIDATED round 2 (0 HIGH; N1 unsourced clause removed; LOW L1/L2/L3/L5/L9 partly open → G3; verify_skill OK) |
| lambda | VALIDATED round 2 (0 HIGH; M7/N1/N2/N3/N4/N6/N8/L7 fixed; M11 + judgement LOWs → G3; verify_skill OK) |
| eventbridge | VALIDATED round 2 (0 HIGH; M-A/B/C + LOW fixed incl. exact upgrade-guide wording and v7 quote; verify_skill OK) |
| step-functions | VALIDATED round 2 (0 real HIGH: date issue resolved at source via facts re-read; M1–M3 + most LOW fixed; verify_skill OK) |
| api-gateway | VALIDATED round 2 (0 wrong facts; N-H1 date chain + N-M1/M2 + LOW fixed; L-9 APIGateway.11 names abbreviated → G3; verify_skill OK) |
| cognito | VALIDATED round 2 (0 HIGH, 0 MED, 4 LOW → G3: Always bullet 1 two claims, mapping column header, 'legacy checklist'/'was not read' wording; verify_skill OK) |
| ses | VALIDATED round 2 (0 HIGH; N1 SES.3 mapping split + tagged M6, N2/N5/L6 fixed; N3/N4/N6 LOW → G3; verify_skill OK) |
| xray | VALIDATED (0 HIGH; 7 MED + 9 LOW fixed; S3 criterion reworded; verify_skill OK) |
| cost-management | VALIDATED (0 HIGH; 13 MED + 4 LOW fixed; L-8 F17 elements, L-3/5/6/7/9/10 → G3; verify_skill OK; no round 2 needed) |
| sam | VALIDATED round 2 (0 HIGH, 0 MED, 3 LOW → G3: tag mismatch U1/U2 vs absence tag, hub mentions CAPABILITY_AUTO_EXPAND, bullet 4 cites terraform-support page for --hook-name; verify_skill OK) |

## 2026-10-23 — P6 round-1 fix pass applied
- Agent renamed to aws-terraform-engineer; old terraform-engineer.agent.md deleted.
- 26 descriptions shortened (max 201 chars); verify_skill OK on all 26; verify_package aws-terraform OK; terraform package shows only the known cross-package links.
- Leaked wording to clean in P7: "family facts F1–F3/F6/F7/F16" mentions in bibliographies of unverified-and-risks.md (e.g. acm lines 30, 74, 75).
- Next: ask user before P6 round 2.

## 2026-10-23 — P6 round 2
- Reports: validation/p6-round-2/{quality-validator,skill-evaluator,architecture-auditor}.md. No HIGH content findings; auditor H1 (.claude/ not regenerated) is P8.
- Applied: agent test pre-check (file-level mock_provider, `command\s*=\s*apply`, providers overrides), single scrubbed `terraform test` command, required_version/refusals reported as open questions; README allow rules for env/TF_IN_AUTOMATION prefixes; scenarios: namespace added (1,4,8), 7 split into 7a/7b (9 scenarios, JSON valid).
- Open: M1 applyTo of code-standards/skills-management (user decision); P7: strip inline "(F4)/(F7)" ids and "family facts Fn" (44 hits, 22 files) + unify dates.
- M1 decided by user 2026-10-23: restrict globs to AWS paths (applied).

## 2026-10-26 — P7 done
- Stripped F# ids and workspace/_family_facts refs from shipped skills; shared-source read dates (releases, backend/s3, version-constraints, 6.0 guide, region guide, CHANGELOG) unified to 2026-10-23 per line; unit-own source dates left as fetched.
- verify_skill OK on 26; verify_package aws-terraform OK.
- Next: P8 (apm install, counts, CLAUDE.md), then G3.

## 2026-10-26 — P8 done (apm 0.35.0, user decision: update everything to latest)
- apm 0.35.0 = latest release. Install needed `--force` (0.33 lock had no deploy baseline) and GIT_CONFIG env core.autocrlf=false (microsoft/apm clone failed on Windows autocrlf).
- Post-install: restore-rule-metadata (11 patched), fix-cross-package-links extended for 0.35 hash-nested apm_modules paths (scripts/fix-cross-package-links.py); artifact-author lock hash refreshed manually.
- Real counts: .claude skills 107 (53 commands + 54 knowledge), agents 23, rules 11; packages 22 (14 in lock).
- Updated: CI pin apm-cli==0.35.0, building-agent-packages version row (source+generated), CLAUDE.md counts/packages/executors.
- Side effects: new untracked root .gitignore (apm_modules/), .claude/skills/pr-description-skill/evals/.gitignore; apm.lock.yaml +3.7k lines (0.35 format).
- Next: G3 commit plan.
- G3 commit plan approved by user 2026-10-26 ("Aprovar e commitar"): 3 commits, no push.
- 2026-10-26: root apm.yml now lists aws-architect, oci-functions-java/terraform/observability/architecture, stripe-java (stripe apm.yml fixed to structured deps). Install OK (30 deps). .claude: 207 skills/64 commands/33 agents/40 rules. Fixer extended (instructions->rules, posix links). NOT committed; awaiting G3.
- 2026-10-26: frozen check clean (hash before==after); user approved commit conditional on it.
