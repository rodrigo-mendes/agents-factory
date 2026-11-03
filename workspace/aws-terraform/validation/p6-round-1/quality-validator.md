# P6 round 1 - Quality validation, agent layer of aws-terraform

Date: 2026-10-23. Scope: terraform-engineer agent, provision-aws-terraform router, 3 instruction files, README, 2 apm.yml.
Method: full read of every artifact, cross-check against _family_facts_v6.md (F1-F19), agent-frontmatter rule, camel-quarkus-integrator and stripe-integrator models. Glob confirmed 26 skill directories, names match the routing tables.

## Totals

HIGH 3, MEDIUM 5, LOW 8. Grade: PASS-WITH-FIXES (safety and eval format must be fixed before the agent layer ships).

## HIGH

H1. SAFETY: `terraform test` with `command = plan` can hit real AWS; `command = apply` is not excluded.
- Agent L50: "`terraform test` (only with `mock_provider` or `command = plan` runs)". The "or" admits a `command = plan` run with the REAL provider, which refreshes and reads real AWS with ambient credentials. That is a plan against real credentials, contradicting Never Do L107-108. A `run` with `command = apply` and a real provider creates real infra; the agent never says it must check for that, nor that test files already in the repo may contain it.
- Same wording is repeated: router SKILL.md L62-63 and L66-67; README L61-62 (README says "with mocks", acceptable); evaluation Scenario 1.
- Fix: require EVERY provider in the test to be mocked (`mock_provider "aws"`), no `command = apply` against an unmocked provider; before running, Grep `tests/**/*.tftest.hcl` for `command = apply` and for runs without `mock_provider`; if found, do not run, return a question. Run test with AWS_* / AWS_PROFILE unset. Remove "or command = plan" or restate as "command = plan only together with mock_provider".

H2. ROUTER eval file is not in the pilot JSON format.
- blueprints/evaluation-scenarios.md L1-28: 4 scenarios in prose (`**Input:**`/`**Expected:**`), no ```json blocks, no `skills`, `query`, `success_criteria: {must_pass, must_not}`. Reference format: provisioning-aws-cost-management-v6/blueprints/evaluation-scenarios.md L10-31.
- Fix: rewrite each scenario as a JSON block with must_pass/must_not. Add scenarios (see M5).

H3. `required_version = "~> 1.16"` ALLOWS Terraform 1.17+, but the text says 1.16.x only / 1.17 forbidden.
- `~> 1.16` means >= 1.16, < 2.0, so 1.17.0 (stable) satisfies it. Pinning to the 1.16 line needs `~> 1.16.0`.
- Contradicting statements: agent L105 ("Terraform outside 1.16.x" is Ask First); project-config L11-12 and rule 8 L39 ("Never target ... Terraform 1.17"); README L12 ("1.17.0 is NOT the target"); code-standards rule 1 L14.
- F1 fixes the constraint at `~> 1.16` (user decision G1b), so the facts are consistent but the shipped rules are not testable as written. Fix options (needs orchestrator/user decision): (a) change to `~> 1.16.0` everywhere; or (b) keep `~> 1.16` and reword to "the skills are verified on 1.16.x; 1.17+ is permitted by the constraint but unverified (medium confidence)", and drop "Never target 1.17". Also rule 8 cites no source for the 1.17 prohibition (only the v7 part has one).

## MEDIUM

M1. Never Do is a deny-list, not an allow-list (agent L106-115). Bash is unrestricted. Not covered: `terraform console`, `refresh`, `taint/untaint`, `force-unlock`, `workspace`, `providers lock`, `get -update`, `init` with a configured backend (only step 6 uses -backend=false), `aws ...` read or write CLI calls (e.g. `aws sts get-caller-identity` still uses real credentials). Add: "Run no command outside the step 6 list; no `aws`/`oci`/cloud CLI at all; do not pass `-backend=true`/`-reconfigure`". Optional LOW addition: `data "external"` and `local-exec` execute local programs on plan/test; flag them instead of running.

M2. No precedence between agent ladder and skill rows. Skills tell the reader to run `plan -detailed-exitcode -input=false -out=tfplan` as CI (s3 SKILL L131, iam L118, cloudwatch L122, vpc L119, blueprints always-do-testing / always-do-security / always-do-replication-satellites) and use `terraform import ...` or `terraform apply` as remedies (sam SKILL L146, api-gateway L94/L147, cost-management L107). Agent L44-45 says "never contradict a skill row". Add one line: skill commands are text to write into CI files or guidance for the user; the agent executes only step 6, and the Never Do list wins on any conflict.

M3. Closed-requirement checklist omits the state backend. Agent L33-35 and router L20-26 do not ask whether a backend is wanted (bucket, key, region, or none), yet Always Do L97-98 says use `use_lockfile = true`. Risk: agent invents bucket/key names. Add "backend: S3 settings or none" to both lists and to Ask First.

M4. Invalid / over-matching Verify greps.
- project-config L49: `dynamodb_table` is a substring of `aws_dynamodb_table`, so every DynamoDB table resource is flagged as a violation. Use `^\s*dynamodb_table\s*=` inside `backend "s3"`. `6.57.0` has unescaped dots and matches `16.57.0`; use `6\.57\.0`.
- code-standards L59: `data.aws_region.*\.name` has unescaped dots and a greedy `.*` (matches `data.aws_region.x.region ... var.y.name` on one line). Use `data\.aws_region\.[A-Za-z0-9_-]+\.name\b`. The "region on the global resources of rule 8" check is prose, not a command.

M5. Eval coverage gap on the safety contract: no scenario for (a) a pre-existing test with `command = apply` or unmocked provider, (b) `(unverified)`/`(medium confidence)` item surfaced in report item 6, (c) provider 5.x/7.x or Terraform 1.17 request, (d) requirement missing target path/backend. Scenario 4 ("pin 6.57.0 and dynamodb_table") is good; keep.

## LOW

L1. Rules not strictly one testable statement: code-standards rule 2 L17 ("may set region"), rule 7 L30 (process: "check the guide"), rule 6 L26 bundles 5 facts, rule 8 L35-43 bundles a long list; project-config rule 4 L25-26 bundles two facts (init order and plan exit codes); skills-management L14-17 and L21 are process/untestable and cite no fact.
L2. project-config "Not rules" L45 lists a volatility note, not a medium/unverified item (the section should list only those). Code-standards "Not rules" (WAFv2 us-east-1 alias vs region) correctly matches F16 medium.
L3. applyTo: project-config `**/.terraform.lock.hcl` is redundant with `**/*.hcl`; `*.tf.json` not covered. Globs otherwise valid; `.tftest.hcl` is covered by `**/*.hcl`.
L4. Skill path claim (agent L37-38): `.claude/skills/provisioning-aws-<service>-v6/SKILL.md` is correct for a consumer after `apm install --target claude` (same as camel-quarkus-integrator agent L28-45; stripe-integrator instead uses non-installable `packages/...` paths, so camel is the better model). In THIS repo it does not resolve yet: Glob found no `provisioning-aws-*` and no `terraform-engineer*` under `.claude/`. Run `apm install --target claude` and commit both, otherwise the CI drift check (`git diff --exit-code`) fails.
L5. Version facts duplicated in 6+ places (agent L97-98, router L3, 3 instructions, README); acceptable per F-table "Used by: all", but agent L21-24 says it states no facts of its own and "no second mapping". Consider pointing to the skills instead of repeating numbers.
L6. Agent may Read `terraform.tfstate`/`*.tfvars` during step 4 inspection; add "do not print state or tfvars contents in the report".
L7. Skills cross-reference siblings (e.g. dynamodb -> kms, lambda -> iam); agent L38-39 "do not load unrelated skills" gives no rule for a referenced sibling not in the requirement; state: ask first (already implied by Ask First L103).
L8. CLAUDE.md counts (agents 21, skills 79, terraform "3 skills") will be stale after install; terraform/apm.yml description counts only "2 skills" research; update docs at install time.

## Passed checks

- Agent frontmatter: name = filename stem (`.agent.md` convention as in other packages), description "Use when" and "Not for" present, 700 chars (< 1536), `tools: Read, Grep, Glob, Edit, Write, Bash`, `model: sonnet`, no `Agent` tool.
- Non-interactive contract: L17-19, L33-36, L40-41, L112 return questions, never assume. Out-of-coverage handled L89-91.
- Verification ladder order correct (`fmt -check -recursive`, `init -backend=false`, `validate`, `test`); "never claim success without running" L53-54, L114.
- Never Do covers apply/destroy/import/state mutation/plan with real credentials/mutating CLI/secrets.
- `(unverified)`/`(medium confidence)` treated as non-facts: L22-24, L99, L113, report item 6.
- 6-point report format present (L116-123).
- Routing table: exactly 26 rows, identical in agent L60-87, router L30-57 and README L20-47; every name exists as a directory in packages/aws-terraform/.apm/skills.
- Router frontmatter: `context: fork`, `agent: terraform-engineer`, `disable-model-invocation: true`, `argument-hint`, quoted description about 245 chars with "Use when".
- Instructions: no F#/M#/U#/workspace ids or process wording (Grep clean). Values match facts: `~> 1.16`, `~> 6.69`, 1.16.7 (2026-10-22), 1.17.0 (2026-10-21), 6.70.0 (2026-10-21), `use_lockfile`, 6.57.0 withdrawn, global list and carve-outs (`aws_route53_resolver_*`, `aws_wafv2_*`), `.region`, `bucket_region`, identity import >= 1.12.0, v7 planned with the `s3_us_east_1_regional_endpoint` quote. Medium item (WAFv2 alias vs region) only in "Not rules".
- Packaging: aws-terraform/apm.yml depends only on factory-core; terraform/apm.yml 1.2.0 adds `../aws-terraform`; no circular dependency (full grep of `path: ../` across packages). aws-terraform is not listed in root apm.yml, correct (transitive). README lists only existing skills.

## HIGH list (for caller)

1. H1 agent L50 (+router L62-67): `terraform test` "or command = plan" allows real-provider plans; no exclusion of `command = apply`/unmocked tests.
2. H2 evaluation-scenarios.md: not pilot JSON, no success_criteria must_pass/must_not.
3. H3 `~> 1.16` permits 1.17+, contradicting "1.16.x only"/"never 1.17" in agent L105, project-config L11/L39, README L12.
