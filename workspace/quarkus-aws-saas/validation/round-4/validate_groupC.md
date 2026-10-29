# P6 round 4 VALIDATE, group C (independent pass)

Spec: `.claude/skills/skill-best-practices-validator/SKILL.md`. Rubric per skill: 100 - 6 per HIGH - 2.5 per MEDIUM - 0.5 per LOW.
Read-only. Nothing executed. All five skills read in full (SKILL.md, every blueprint, asset, script, README). Line numbers were counted from the files as read.

## Score table

| Skill | HIGH | MED | LOW | Score |
|---|---|---|---|---|
| structuring-quarkus-lambda-projects | 1 | 2 | 3 | 87.5 |
| refactoring-quarkus-java | 1 | 1 | 2 | 90.5 |
| deploying-aws-lambda | 2 | 3 | 3 | 79.0 |
| debugging-aws-lambda | 0 | 2 | 4 | 93.0 |
| validating-aws-observability | 1 | 4 | 3 | 82.5 |

Mechanical checks, all passed: frontmatter has only `name` + `description`, quoted, name equals folder, "Use when" present, description about 250-285 chars (<300). SKILL.md lengths 128-151 lines. Every blueprint is at most 160 lines and those over 100 lines start with Contents. Every skill has a register with `Version-lifetime risk` and `Source Bibliography`, plus 6 scenarios with a canonical, an edge, a rejection and a trap case. Every intra-skill and sibling link/anchor I followed resolves. No absolute paths. No file named `report*` (only "deploy report" as prose). Quick Navigation links a Verification Loop in 4 of 5 skills (see structuring M1).

---

## 1. structuring-quarkus-lambda-projects (87.5)

**HIGH-1. Team-convention claims sit in Always Do and Never Do (evidence rule, tier rules; family rule 9).**
- SKILL.md:62 Always Do: "Keep the Lambda handler class or REST resource at the package root and delegate to flows in `handler/`".
- SKILL.md:89 Never Do: "| Put the Lambda handler class inside `handler/`, `web/` or another sub-package | Package root; `handler/` holds use-case flows |".
- Both contradict SKILL.md:54 "It is a team convention, not a Quarkus requirement" and the register M1 (medium). The same applies to bullet 5 on test placement (SKILL.md:64).
- Fix hint: move the convention rows to Ask First or Quick Reference tagged `(medium confidence, M1)`. Keep in Never Do only the High rows (HTTP framework, SAM, removed test artifact, lock file, bean index, `quarkus.lambda.handler` rename).

**MEDIUM-1. Rule 12: Quick Navigation does not link a Verification Loop.**
- SKILL.md:27-38 has no Verification Loop entry. The verification commands are a trailing sentence in Quick Reference (SKILL.md:132).
- Fix hint: add a `## Verification Loop` section and link it.

**MEDIUM-2. `(unverified)` tag without a register row.**
- always-do-patterns.md:32 "`java25` (unverified; see developing-quarkus-amazon-lambda-v3-40 Ask First C2)" and project-structure.yml:90 "java25: unverified".
- The register has only U1-U3, and the tag mapping (unverified-and-risks.md:45-54) has no row for it. SKILL.md:9 promises that each tag "maps to a line of the register".
- Fix hint: add U4 (java25 runtime) and a mapping row, or drop `java25`.

**LOW-1.** SKILL.md:61 states the handler `QuarkusStreamHandler::handleRequest` for every build. Register U3 says the native handler is not stated by the guide. Add "JVM build" to the bullet.
**LOW-2.** never-do-patterns.md:76 and :78 say the same thing twice (ignore entries, medium M3). Remove one.
**LOW-3.** SKILL.md:88 "family fact 27" and always-do-patterns.md:32,70,83 "family fact 23/19" point to `workspace/.../_family_facts` (SKILL.md:142 says "not shipped with the skill"). Inline the dated source URL instead.

---

## 2. refactoring-quarkus-java (90.5)

**HIGH-1. Unverified general method (register U1) and tagged-medium content sit in Always Do and Never Do (evidence rule: Always Do = one High claim with an inline URL; Never Do = High rows only; family rule 9).**
- SKILL.md:44 "Bullets 1 to 5 are the general refactoring method taken from `refactoring-oci-java` (no Quarkus claim; register U1)". Bullets 48-52 carry no URL or tag.
- SKILL.md:81 "(method from `refactoring-oci-java`, register U1)", and rows 82-84 are the same kind. register U1 = `(unverified)`.
- never-do-patterns.md:32 puts the `(medium confidence, L1)` `@InjectMock`/`convertScopes` claim inside the Never Do pattern "Scope change".
- never-do-patterns.md:80 puts `(unverified, U2)` inside the Never Do example for dropped markers.
- always-do-patterns.md:26,32,33 puts L1 medium claims inside Always Do patterns.
- Fix hint: keep the method rules in a separate "Method (team practice, unverified U1)" block outside the three tiers. Strip the L1 and U2 claims from Never Do and Always Do bodies (leave them in Ask First).

**MEDIUM-1. Rule 13: the same claim carries a different tag in the same skill.**
- SKILL.md:66 "`@Singleton` has no proxy and is not mockable by default" has no tag.
- SKILL.md:72, :103 and never-do-patterns.md:32 say the same mockability claim is `(medium confidence, L1)`.
- Fix hint: tag row 66 `(medium confidence, L1)` or cite its own verbatim source.

**LOW-1.** SKILL.md:66 "`@ApplicationScoped` is the CDI guide default" vs always-do-patterns.md:43 "recommends `@ApplicationScoped` by default". Family rule 11 reserves "default" for a config key's documented default. Say "recommended".
**LOW-2.** unverified-and-risks.md:93 lists `workspace/...` files read. These are provenance only and are not shipped. Mark them "not shipped".

---

## 3. deploying-aws-lambda (79.0)

**HIGH-1. Wrong source for the apply gate: the OCI rule, not the AWS one (evidence rule; family rule 8).**
- SKILL.md:20 "`.claude/rules/terraform-standards.md` (repo rule, not an AWS fact)". The same path appears at SKILL.md:67, SKILL.md:98, always-do-patterns.md:20, never-do-patterns.md:18, preflight-and-plan.md:60,68, unverified-and-risks.md:156 and in scenario 2.
- That file is the OCI Terraform standards rule ("Terraform Code Quality specialist for OCI", from package `oci-terraform`).
- `packages/aws-lambda/apm.yml` depends on `aws-terraform`, not `oci-terraform`.
- `packages/aws-lambda/.apm/instructions/aws-lambda-deployment-preflight.instructions.md:22` says "Do not confuse them with the OCI rule `terraform-standards`". The AWS counterparts are `aws-terraform-code-standards` and `aws-terraform-project-config`.
- Also, `terraform-cicd.md` (the source of `-input=false`, always-do-patterns.md:20) is the Azure DevOps/OCI pipeline rule.
- Fix hint: cite `aws-terraform-code-standards` (plan with `-out`, never `-auto-approve`) and `aws-lambda-deployment-preflight` instead. Keep `-input=false` as an internal convention.

**HIGH-2. Rule 13: waiter budgets and CLI behaviour come from partly read pages, are stated flat, and have no verbatim quote or tag.**
- apply-waiters-publish-alias.md:28-35 table "Poll 1 s / 5 s; gives up 300 / 60 / 312 failed checks, rc 255".
- smoke-test-and-verification.md:49-50 "rc 255 after 300 failed checks" and "rc 255 after 312". SKILL.md:115 repeats the waiter list.
- apply-waiters-publish-alias.md:26 itself says "read through a targeted extraction, not end-to-end (coverage limit L1)". The research marks S21-S29 "extract = partly read" and records no verbatim quote for the budgets.
- The register has L1 but no `(medium confidence, L1)` tag mapping, unlike the sibling `refactoring-quarkus-java`.
- Fix hint: tag the budget numbers `(medium confidence, L1)` and map them in the register. Cite exact `Always Do` waiter names only from the full page (`wait/index`) or a recorded quote.

**MEDIUM-1. Approval-line vocabulary is incomplete against approval-lines.md.**
- Only `approval: smoke ...` is written out (SKILL.md:56, smoke-test-and-verification.md:13).
- Apply and rollback are described as "approval relayed by the orchestrator" only. The `approval: apply plan=<planfile> sha256=<hash> ...` line, the rule that a regenerated plan voids it, the sha256 re-verification and the `approval: rollback alias=<alias> to=<PREV> ...` line are missing.
- SKILL.md:74 Always Do 8 ("Roll back by repointing...") is unconditional. The approval requirement appears only in rollback-and-cleanup.md:3 and :50.
- Fix hint: add the two lines to the Procedure table (steps 3 and 7) and to always-do 1, with `relayed-by=<orchestrator>`.

**MEDIUM-2. Mutating CLI shapes with no approval kind or gate.**
- apply-waiters-publish-alias.md:57-63 `aws lambda publish-version ...` ("for a pipeline that publishes outside Terraform") has no approval note. The Procedure table (SKILL.md:51-59) has no publish step.
- rollback-and-cleanup.md:58-61 / SKILL.md:59 step 8 `delete-function --qualifier` is "a later, separately approved step", but the contract has no approval kind for it and no line is named.
- Fix hint: state that publish and cleanup are M steps under the apply or an explicit user line. Ask the orchestrator for a `cleanup` approval kind or route it through `apply`.

**MEDIUM-3. Claim beyond the research (a skill must state no fact absent from the research).**
- SKILL.md:101 and never-do-patterns.md:57: "`--revision-id` is only a concurrency guard (update only if the revision is unchanged), it does not carry values", cited to the env-vars page. The research (line 345) only says "pass `--revision-id` ... to avoid lost updates [S10]". The `update-function-configuration` CLI page is in no bibliography.
- Fix hint: reword to the research text or fetch and record the CLI page.

**LOW-1.** SKILL.md:37-38 lists "Smoke test and Verification Loop" and "Verification Loop" as two entries for the same file.
**LOW-2.** SKILL.md:72 puts a caveat pointer "(M5)" inside an Always Do bullet (evidence rule: no caveats inside the bullet).
**LOW-3.** SKILL.md:21 puts a source URL in the Source column that the skill itself says returned an empty body. Mark it "not used".

---

## 4. debugging-aws-lambda (93.0)

**MEDIUM-1. Handoff and approval vocabulary not tied to the contract (rules 14, 15; approval-lines.md).**
- verdict-and-handoff.md:12-26 defines "Verdict: <one cause, or "not determined" ...>" and a work-order. It never maps these to the protocol outcome vocabulary (`success | partial | failed | needs-input` for diagnosis records, `pass | fail` for verify). It names no record (`diagnosis-NN.md`, `verify-E7.md`) and has nothing on `e7-gaps` / pillars "not verified" / `## Gaps`.
- ask-first-decisions.md:62,65 allow a real invoke "approved by the user (deploy smoke rules, In3)" / "approval must come from the user through the orchestrator". The contract routes `approval: smoke` only to `aws-lambda-deployer`, and no line kind covers a debugger invoke. The skill cannot name one.
- Fix hint: add "outcome" mapping (not determined -> `partial` or `needs-input`; E7 pillars unverified -> `fail` unless an `e7-gaps` line) and drop the debugger real invoke or route it to the deployer.

**MEDIUM-2. Facts from partly read (extract) CLI pages stated flat, untagged (rule 13).**
- read-only-allowlist.md:50-52 (`logs tail` default start 10 minutes, `nextToken` expires after 24 hours, `--unmask` needs `logs:Unmask`) and logs-insights-and-fields.md:74 ("up to 50 log groups, limit up to 100,000 ... times out after 60 minutes") cite S39/S40/S41/S56, which the register (unverified-and-risks.md:77) lists under L1 "targeted extraction".
- Fix hint: tag `(medium confidence, L1)` or record the quotes.

**LOW-1.** SKILL.md:134 Quick Reference "SnapStart restore limit" cites only `API_Invoke.html`. The family fact cites `snapstart-runtime-hooks-java.html` and the Quarkus guide for the 2 s / 10 s pair. Add both URLs.
**LOW-2.** read-only-allowlist.md:81 principal list omits `lambda:InvokeFunction`, which DryRun (:76) and C5 need.
**LOW-3.** SKILL.md:77 Always Do 1 carries a caveat ("except that ... start-query ... needs approval") inside one bullet. Split it.
**LOW-4.** never-do-patterns.md:83 puts an `(unverified)` 503 note inside the Never Do pattern N5. Move it to Ask First.

Contract checks that PASS: `approval: logs-insights scope=<log-group> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>` and the `scope=xray` form match the contract (read-only-allowlist.md:27,32). Mutating verbs are refused with a work-order. The 2 s vs 10 s SnapStart pair and the 14-day SnapStart caveat match family facts 21 and 33. Register counts U9/I8/M10/L6 match the Verification Loop expectations (verdict-and-handoff.md:86-87).

---

## 5. validating-aws-observability (82.5)

**HIGH-1. Safety gate: the documented live command starts billable queries with no approval and no `--skip` (SKILL.md:62 vs :140).**
- SKILL.md:62 says "Logs Insights `start-query` ... and X-Ray `start-trace-retrieval` run only when the caller holds `approval: logs-insights scope=... window=...` ... never run `start-query` or `start-trace-retrieval` on your own authority."
- SKILL.md:140 "Live use ...: `bash scripts/validate-observability.sh --function F --region R --start-s T --alarm-prefix P --dashboard D`; exit 0 and no FAIL line means the run passed." This runs logs (`check-logs.sh:70` `start-query`) and traces (`check-traces.sh:123` `start-trace-retrieval` when the destination is CloudWatchLogs).
- evaluation-scenarios.md:25-31 (scenario 1) never requires the approval line, and `must_pass` instructs running "validate-observability.sh or the five check scripts".
- scripts/README.md:68 admits "The scripts do not check approvals; the caller does". The only gated script is `trigger-alarm-test.sh`.
- Fix hint: change SKILL.md:140 and scenario 1 to `--skip logs,traces` by default and to require the logs-insights line for the full run. Optionally add a `--i-have-logs-insights-approval` flag, symmetric with `--i-have-user-approval`, so the unapproved default is skip.

**MEDIUM-1. Approval and record vocabulary not tied to the contract (rule 15, approval-lines.md).**
- SKILL.md:64 and ask-first-decisions.md:29 describe "the orchestrator relayed the user's explicit approval for that exact alarm" but never write the line `approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=<orchestrator>`.
- Nothing about `result-NN-observability.md`, `role: observability-live`, or how `not verified` pillars feed `e7-gaps`.
- Fix hint: add the `alarm-test` line next to the logs-insights line and a pointer to the record/outcome vocabulary.

**MEDIUM-2. Exit code 0 can hide unverified pillars.**
- SKILL.md:140 "exit 0 and no FAIL line means the run passed"; cli-environment-and-exit-codes.md:89 "0 all checks passed; WARN lines are inconclusive".
- `check-logs.sh:126-128` prints WARN "INCONCLUSIVE" when no line matches yet. `validate-observability.sh:114-132` and `:140-143` give exit 0 with pillars `SKIPPED`, and `check-dashboards.sh:154` always WARNs. A caller or gate keyed on the exit code would pass while pillars are not verified.
- The contract requires such pillars to be reported as `not verified` and to fail E7 unless `e7-gaps` accepts them.
- Fix hint: add a SUMMARY field `not_verified=<pillars>` and a `--strict` exit (for example 4) when any pillar is WARN or SKIPPED, and word the SKILL line as "no FAIL and no WARN/SKIPPED for the required pillars".

**MEDIUM-3. Billable calls presented as unconditional defaults outside the gate section.**
- SKILL.md:72 Always Do 3 "Logs: ... count required fields with Logs Insights" and always-do-patterns.md:38-40 A3 (the `start-query` command).
- SKILL.md:104 Never Do ✅ "`CloudWatchLogs` means `start-trace-retrieval`" and pillar-traces.md:20-21,49-51.
- ask-first-decisions.md:51 K3 "Insights (default)".
- Not stated there: the approval line, and (command-allowlist-and-iam.md:21 M4) that `start-trace-retrieval` read class is itself `(medium confidence)`. Never-do-patterns.md:3 claims "every alternative is High too".
- Fix hint: add "(needs approval: logs-insights ...)" to those bullets, and drop the High claim for the N4 alternative or tag it.

**MEDIUM-4. No scope/window guard for the approval.**
- check-logs.sh:59-64 resolves the log group at run time (`LoggingConfig.LogGroup`, else `/aws/lambda/FN`) and queries `START_S..now` without printing it first.
- The approval's `scope=` and `window=` cannot be matched by the caller beforehand.
- Fix hint: print the resolved group and window on a `PLAN` line, or add a `--dry-plan` that exits before `start-query`.

**LOW-1.** SKILL.md:3 description says "scripts that change no resource", yet the skill ships a mutating script (`trigger-alarm-test.sh`) and billable queries.
**LOW-2.** check-traces.sh:44, check-alarms.sh:39 and check-dashboards.sh:41 accept `--wait-seconds`/`--retry-seconds` via `common_opt` but ignore them. Reject them or document it.
**LOW-3.** command-allowlist-and-iam.md:24,61 allowlists `apigateway get-stage` and `apigateway:GET`, which no script uses and which is broader than needed.

Checked against the scripts and PASS: all flags in SKILL.md/README (`--fields`, `--min-events`, `--allow-no-retention`, `--min-invocations`, `--max-errors`, `--custom*`, `--api-type`, `--trace-ids`, `--max-traces`, `--expect-aws-call`, `--alarm-prefix/--alarm-names`, `--fail-on-insufficient-data`, `--dashboard*`, `--skip`, `--alarm-name`, `--i-have-user-approval`, `--allow-composite`, `--reason`) exist with the stated defaults. The exit-code contract (0/1/2/3, trap ERR to 3, validate precedence 2 > 1 > 3) matches the code. `set-alarm-state` appears only in `trigger-alarm-test.sh`, and the only `start-*` verbs are `start-query` and `start-trace-retrieval`. The guard greps in SKILL.md:136-137 and command-allowlist-and-iam.md:73-77 give the expected output.

---

## Cross-skill and family notes

- The `logs-insights` line is consistent in debugging and observability (scope, window, `scope=xray`). The `smoke` line is consistent in deploying only. `apply`, `rollback` and `alarm-test` are not named in any of the three (see deploying M1, observability M1).
- Family rules 1-8 hold in all five (Quarkus 3.40 only, no SAM/CDK, secrets in Secrets Manager, JVM/SnapStart/native as Ask First, bounded dimensions). Rule 2 (Quarkiverse 3.23.x): structuring tags the 3.40.1.1 pairing medium. Rule 10 (per-key defaults): no violation found.
- Not verified by me (no research read for these): the "tool summary with verbatim quotes" claim in observability L2 (unverified-and-risks.md:78), and the AWS numeric facts (quotas, TPS) beyond the spot checks I made against the Debug and Deploy research files (SQS, API Gateway throttle, 300 GB, SnapStart runtimes, waiter table; all matched).
