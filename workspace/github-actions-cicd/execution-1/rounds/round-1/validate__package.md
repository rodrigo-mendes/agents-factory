# Validate: package (agents, rules, command, README, apm.yml) (P6 round 1, validator B, 2026-10-30)

Score: 86.0 (1 HIGH, 2 MEDIUM, 6 LOW). Specs: agent-router-pattern-validator, instructions-best-practices-validator, skill-best-practices-validator (read only).

Base path: packages/github-actions-cicd/

## Pass
- apm.yml: valid manifest, dependencies factory-core + github-core, includes auto; counts in description (9 skills, 2 agents, 4 rules, 1 command) verified against the file tree; root apm.yml lists ./packages/github-actions-cicd (line 44).
- Router pattern: command skill `building-cicd-pipelines` has `context: fork`, `agent: cicd-pipeline-engineer` (file exists), `disable-model-invocation: true`, argument-hint; engineer carries only routing table + safety, no domain facts; reviewer is read-only (tools Read, Grep, Glob) and spawned via Agent tool, documented in README; 3 evaluation scenarios.
- Rules: `name` + `description` with "Use when", `applyTo` (APM source form, same as sibling packages), 39-46 lines each, three tiers or Always/Never with alternatives, load-the-skill pointers, overlap of security rule (`**/.github/workflows/**`) with the three scoped rules is intentional and non-contradictory.
- README versions match facts (F1, F11-F15).

## HIGH
- H1 (agent-router: responsibility/consistency): write scope contradicts itself and the skills. `.apm/agents/cicd-pipeline-engineer.agent.md:39-42` allows "a workflow-adjacent file only if a loaded skill's blueprint names it, e.g. a Dependabot config", but its Never Do (`:142`) says "Write or Edit outside `.github/workflows/**` and `.github/actions/**`", Precedence 1 (`:30`) makes Never Do win, and README:7,74 and command SKILL.md:45-46 repeat the narrow scope. The skills require files outside it: `.github/dependabot.yml` (securing `blueprints/dependabot-config.md:9`), `./scripts/switch-origin-path.sh` (nextjs `workflow-deploy-s3-cf.md:51,59`), `vercel.json` (nextjs `workflow-deploy-vercel.md:11-12`). Result: generated workflows reference scripts and configs the agent is forbidden to write. Fix hint: name the exact allowed extra paths (`.github/dependabot.yml`, `scripts/*.sh` named by a blueprint, `vercel.json`) in Input, Never Do, README and the command, or have the agent return them as NEEDS-INPUT/"user must add" items.

## MEDIUM
- M1 (rule vs skill drift): `.apm/instructions/github-workflows-merge-cd.instructions.md:19,45` require a smoke test and rollback for prod ("Deploy prod without smoke test and rollback" is a Never Do), but the shipped CD examples have none: publishing `cd-image.yml`, nextjs `cd-web-s3.yml`/`cd-web-vercel.yml`. Rule line 16 says concurrency "per environment" while blast-radius uses per app and environment. Reviewer would flag the family's own examples. Fix hint: scope the rule to targets covered by `_smoke-test`, or add smoke/rollback to the examples.
- M2 (rule 16 / rule 10 carve-out missing): `github-workflows-security.instructions.md:16,32` ("keep the key in an environment secret", "Scope secrets to environments for anything that can deploy") and `.apm/agents/cicd-pipeline-reviewer.agent.md:110` ("repository-scoped secrets for anything that can deploy" reported as MEDIUM) give no Free-private exception, although `github-workflows-merge-cd.instructions.md:15` and rule 16 define the weaker Free variant with repository secrets plus warning. On Free private there are no environments, so the instruction is unsatisfiable and the reviewer over-reports the sanctioned variant.

## LOW
- L1 (A: precision): `cicd-pipeline-engineer.agent.md:30` cites "(Never Do, step 6)"; the Never Do list is under `## Rules`, step 6 is Verify.
- L2 (B2 reasoning): rules state prohibitions without reasons in most lines (e.g. `github-workflows-pr-ci.instructions.md:14-19`, `github-workflows-building-blocks.instructions.md:13-18`); add one-clause "because".
- L3: `README.md:61` writes `refs/heads/main`; the OIDC sub fragment is `ref:refs/heads/main` (as in the skills).
- L4 (skill-structure.md): command `building-cicd-pipelines/SKILL.md` has no Quick Navigation and no three-tier section; it matches sibling command skills (`provision-aws-terraform`), so convention-level only.
- L5: `building-cicd-pipelines/blueprints/evaluation-scenarios.md:13` prompt asks for prod "required reviewers" on Pro private and expects no correction (F25: public/Enterprise only), and uses `AWS_ROLE_ARN` where aws-oidc and nextjs use `AWS_DEPLOY_ROLE_ARN`; command SKILL.md:56 "prod needs approval" is ambiguous in the same way.
- L6: `github-workflows-pr-ci.instructions.md:14` allows `pull-requests: write` only on the plan-comment job, while the supply-chain `ci-api.yml` grants it (and `security-events: write`) to the scan job.

Known/tracked, not re-reported: F-012 (catalog names out of sync: catalog still lists `_node-build` secret NPM_READ_TOKEN, `_promote` and `_security-scan` outputs "none", `_smoke-test` pass/fail via job result, composite names `node/setup`, `repo/changes`).
