# Architecture Audit, Round 2: aws-terraform-engineer / provision-aws-terraform / aws-terraform

Single lens, no fan-out. Date: 2026-10-23.

## Round 1 items

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Safety: terraform test with real creds, apply/destroy/import/state | RESOLVED | agent.md:69-84 (allow-list, mock grep gate, `env -u` creds), :148-163 Never Do |
| 2 | Skill-vs-agent precedence | RESOLVED | agent.md:26-32 |
| 3 | Closed-requirement checklist missing backend | RESOLVED | agent.md:47; SKILL.md:200-201 |
| 4 | `~> 1.16` wording | RESOLVED | agent.md:126-132; README.md:14 (>= 1.16, < 2.0, 1.17+ unverified, so Ask First) |
| 5 | Instructions applyTo too broad | PARTIAL | project-config is now scoped to config files. code-standards and skills-management still match every `**/*.tf` (see M1) |
| 6 | Router duplicating routing table | RESOLVED | SKILL.md:206-210 lists only names and points to the agent |

## Structural checks (verified)

- Agent frontmatter: `name` matches the filename, `tools` has no Agent, `model: sonnet`. Valid.
- Router: `context: fork`, `agent: aws-terraform-engineer` matches, `disable-model-invocation: true`. blueprints/evaluation-scenarios.md exists.
- Dependencies: terraform 1.2.0 -> aws-terraform 1.0.0 -> factory-core 1.0.0. The root apm.yml lists only `./packages/terraform`, with aws-terraform resolved transitively, so there is no ambiguous resolved_by.
- README counts: Glob finds 26 `provisioning-aws-*-v6/SKILL.md` and 3 instruction files, which match the README. The 26 service names in the router, the agent table and the README match.

## Findings

### HIGH
- **H1: `.claude/` is not regenerated.** `.claude/agents/` has no `aws-terraform-engineer`, and the new files are untracked. Failure scenario: `/provision-aws-terraform` is missing in a clone. If someone commits only `packages/`, the CI `apm install --frozen && git diff --exit-code` check fails, and apm.lock.yaml does not include aws-terraform. Fix: run `apm install --target claude`, then commit `packages/`, `.claude/` and the lock file together.

### MEDIUM
- **M1: Two instruction files still inject on every Terraform file.** aws-terraform-code-standards.instructions.md:4 (`**/*.tf,**/*.tf.json,**/*.tfvars,**/*.tftest.hcl`) and aws-terraform-skills-management.instructions.md:4 (`**/*.tf`) match any Terraform file. This repo also ships oci-terraform. Failure scenario: someone edits OCI HCL and gets AWS 6.x rules (per-resource region, `use_lockfile`) loaded as context, which conflicts with the OCI standards. Fix: scope the globs to AWS layouts (for example `**/aws/**/*.tf`), or document that the package must not be co-installed with oci-terraform in one project. Also consider dropping `*.tfvars`.
- **M2: Gate (a) checks the wrong thing.** agent.md:75-76 says to grep for "`run` blocks without a `mock_provider`". In Terraform test, `mock_provider` is a file-level block, not a per-run block. Failure scenario: the agent reads a file-level mock as covering the whole file and misses a `run` that overrides `providers = { aws = aws.real }`, or it rejects valid files. Fix: require every provider block or alias in the module to have a matching file-level `mock_provider`, and forbid `providers =` overrides that point to an unmocked provider.

### LOW
- **L1: Two versions of the test command.** agent.md:74 has `terraform test -no-color`, but the command run at :79 omits `-no-color` and adds `env -u ... AWS_EC2_METADATA_DISABLED=true`. Use one exact command line.
- **L2: The test gate does not neutralise all credential sources.** `env -u` (agent.md:79) does not unset `AWS_CONFIG_FILE`, `AWS_SHARED_CREDENTIALS_FILE`, `AWS_WEB_IDENTITY_TOKEN_FILE` or `AWS_ROLE_ARN`, and the default `~/.aws/credentials` is still read. Mocks make this mostly moot, but unset these too, or set `AWS_SHARED_CREDENTIALS_FILE=/dev/null` and `AWS_CONFIG_FILE=/dev/null`.
- **L3: Safety relies on the prompt only.** README.md:70-101 says this honestly. Optionally add a PreToolUse hook later.
- **L4: The aws-terraform apm.yml has no `version` on its dependency**, which matches how the other packages declare theirs. That is fine. The terraform package moved to 1.2.0 for a non-breaking addition, which is consistent.

## Score
Round 1 resolved 5/6 (1 partial). New: 1 HIGH (packaging and CI drift, not prompt design), 2 MEDIUM, 4 LOW. The design is close to the camel-quarkus-integrator reference. Fixing H1 and M1 would make it shippable.
