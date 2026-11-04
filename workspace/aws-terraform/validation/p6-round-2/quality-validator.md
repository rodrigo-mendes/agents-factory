# Quality validation, round 2: aws-terraform-engineer agent layer

Read-only review. Verified with Glob and Grep, not from claimed counts.

## Round 1 fix verification

| Round 1 item | Status | Evidence |
|---|---|---|
| terraform test with real credentials | Fixed, with residual gaps (M1, M2, L1) | aws-terraform-engineer.agent.md:74-80. Pre-check (a) and an env-scrubbed run (b). |
| Scenario format | Fixed | evaluation-scenarios.md uses JSON with `success_criteria.must_pass` / `must_not`. 28 files under `.claude` use the same shape. All 8 blocks are valid JSON: escapes are correct and there are no trailing commas. |
| `~> 1.16` wording | Fixed | Agent:126-132, project-config rule:11-13, README:14 and Scenario 7 all say ">= 1.16 and < 2.0, admits 1.17+". |
| Precedence vs skills | Fixed | Agent:26-32. Safety rules override skills, and skill `plan`/`import`/`apply` commands are reported as "skill suggests X; not run". |
| Closed-requirement checklist | Fixed | Agent:42-48 covers backend, naming/tags, scope, test wanted and module type. |

## Routing table: exact match, verified

- Glob of `packages/aws-terraform/.apm/skills/*/SKILL.md` returns 26 skills.
- The agent table (lines 93-118) has 26 rows.
- The sets are identical, with no missing and no extra entries, and the names match. The README table also has 26 rows. The apm.yml description says 26.
- The agent has no `Agent` tool (line 13: `Read, Grep, Glob, Edit, Write, Bash`).
- The agent frontmatter is valid and mirrors the model agent, camel-quarkus-integrator. `name` matches the file name, the description is under 1536 characters and has "Use when", and `model: sonnet` is a valid value.
- The skill frontmatter has all four coupled fields: `context: fork`, `agent: aws-terraform-engineer`, `disable-model-invocation: true` and `argument-hint`.
- The links resolve. SKILL.md links to `./blueprints/evaluation-scenarios.md`, which exists.
- The apm.yml files are consistent. terraform depends on `../aws-terraform` and aws-terraform depends on `../factory-core`. There is no cycle.
- No process wording or leaked ids were found in the agent, the router skill, the scenarios, the instructions, README or apm.yml. Grep for `[FUM]\d+`, "round N", "P6", "finding" and "fixed in" returned nothing in those files. The skills under `skills/` do leak ids (L3).

## Findings

### HIGH

None.

### MEDIUM

**M1. The `mock_provider` pre-check can misfire, and `command = apply` matching is fragile.**
- Location: agent:75-76, and Scenario 6 in evaluation-scenarios.md.
- "Grep ... `run` blocks without a `mock_provider`" does not match how Terraform works. A `mock_provider` is normally declared at file level and covers every run block in the file. A literal per-run grep would reject safe files.
- A plain grep for `command = apply` misses `command=apply` (no spaces) and tab-separated forms.
- A `providers = { aws = aws.real }` mapping inside a run block, or a real `provider "aws"` block in the test file, would also pass the pre-check.
- Failure scenario: the file has `command=apply` plus an unmocked provider. The grep returns nothing and the check passes. Step (b) is then the only barrier, and it covers only the environment variables listed in L1.
- Fix: wording such as "grep case/space-tolerant (`command\s*=\s*apply`); every `provider` used by the test must be covered by a file-level or run-level `mock_provider`, and no `providers =` mapping in a run block may reference an unmocked alias."

**M2. Credential scrubbing is incomplete (the original round 1 hole is only partly closed).**
- Location: agent:79.
- The command unsets 4 variables. Other credential sources remain: `AWS_SHARED_CREDENTIALS_FILE`, `AWS_CONFIG_FILE`, `AWS_WEB_IDENTITY_TOKEN_FILE`, `AWS_ROLE_ARN`, `AWS_CONTAINER_CREDENTIALS_FULL_URI` / `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI`, and `~/.aws/credentials` default-profile lookup. `AWS_EC2_METADATA_DISABLED=true` only covers IMDS.
- Failure scenario: the agent runs on a developer machine with `~/.aws/credentials` (default profile) or in a CI job that uses IRSA or ECS task credentials. A test with an unmocked provider that slips past M1 would then talk to real AWS.
- Fix: add `AWS_SHARED_CREDENTIALS_FILE=/dev/null AWS_CONFIG_FILE=/dev/null` and `-u AWS_WEB_IDENTITY_TOKEN_FILE -u AWS_ROLE_ARN -u AWS_CONTAINER_CREDENTIALS_FULL_URI -u AWS_CONTAINER_CREDENTIALS_RELATIVE_URI`. Alternatively, state that mocking is the control and the env scrubbing is best effort.
- Related: the README says Bash is limited by the prompt only. Its recommended allow list uses `Bash(terraform test:*)`, which does not constrain the `env -u ...` prefix. The README's allow patterns would not match `env ... terraform ...` or `TF_IN_AUTOMATION=1 terraform ...` commands, so the recommended permissions block the agent's own commands. README:80-83 conflicts with agent:69-79.

**M3. The agent writes a constraint that admits versions it calls unverified, and does not tell the user.**
- Location: agent:126-132 versus the Always Do rule at agent:138, and code-standards rule 1 (line 14).
- The agent must write `required_version = "~> 1.16"`, which admits 1.17+. It only raises Ask First if the requirement targets 1.17+.
- Failure scenario: the user does not mention the version. The agent writes `~> 1.16`, the user runs 1.17.0 (stable since 2026-10-21, per the file) and nothing in the report flags the risk.
- Fix: add one line to the report's open-questions section, "constraint admits 1.17+, unverified", whenever the agent writes `required_version`. Or have the rule mention the caveat next to rule 1.
- The 1.17.0 and 1.16.7 dates could not be verified here, because the agent has no web access. They are tagged to sources only.

**M4. The agent has two different `terraform test` command forms.**
- Location: agent:74 (`terraform test -no-color`) versus agent:79 (`... terraform test -input=false`).
- Scenario 1 says only "runs it with AWS_* credentials unset and TF_IN_AUTOMATION=1". An executor can reasonably run the unscrubbed form from line 74.
- Fix: keep one canonical command, line 79 plus `-no-color`.

### LOW

**L1.** agent:71 says "every command ... carries `-input=false` where the subcommand accepts it". `fmt` and `validate` do not take it, but this is consistent with "where accepted". `terraform init -backend=false -input=false` is correct. The rules' Verify section (code-standards:64) lists `init -backend=false` without `-input=false`. Harmless, but not uniform.

**L2.** The `env -u` syntax (agent:79) is POSIX. On native Windows PowerShell it fails with no clear message. The agent then reports "not run", which is acceptable. State the shell assumption (Bash/Git Bash).

**L3.** Leaked ids in the skills, outside the formal targets but inside the package.
- Examples: `provisioning-aws-s3-v6/SKILL.md:28` has "(F4)" and `blueprints/never-do-provider-migration.md:70,99` has "(F7)", "(F4)".
- Many `unverified-and-risks.md` tables have F#/U# rows. A grep for `[FUM]\d+` matches 541 occurrences across 45 files.
- Row labels like U2 in the unverified tables may be intended. Inline "(F4)" references are research-provenance ids that mean nothing to a consumer. Recommend stripping them from SKILL.md and blueprint prose.

**L4.** evaluation-scenarios.md Scenario 7 bundles two independent requests (provider 7.x or Terraform 1.17, plus a second request) in one JSON `query` with a `skills: []` field. This makes LLM-as-judge scoring ambiguous. Split it into separate scenarios, keeping the 4 base types. Also, the header says "Eight scenarios (canonical, edge, ...)", which is accurate (8 verified).

**L5.** The routing skill SKILL.md:33-37 repeats the 26-service list as a flat list while stating "mapping is maintained in the agent". There are now three copies (agent, README, skill). Drift risk is low today (all three verified equal), but a lighter reference is preferable.

**L6.** The agent's description is long (about 800 characters). It is within the limit (<1536) and has a trigger. No action needed.

## Summary

- Frontmatter, tools list, routing table (26 of 26), links, JSON validity and the version wording are all clean.
- There are no HIGH findings.
- The residual risk is the offline-test safety (M1, M2, M4) and the permission-example mismatch (M2).
