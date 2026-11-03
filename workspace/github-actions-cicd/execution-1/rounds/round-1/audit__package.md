# Audit: package github-actions-cicd, architecture consensus (P6 round 1, architecture-auditor, 2026-10-30)

Spec: `audit-cc-architecture-consensus`, adapted per brief (no lens agents spawned, no plan mode). The three lenses were applied one after another in one context: Scope = `audit-cc-architecture-scope` (G0-G4, XCC), Flow = `audit-cc-architecture-flow` (FCC.1-20), Engine = `audit-cc-architecture-engine` (ECC.1-18).
Target: `packages/github-actions-cicd/` source, read as deployed (agents -> `.claude/agents/`, instructions -> `.claude/rules/` with `applyTo` -> `paths:`, skills -> `.claude/skills/`). The deployed copies of `github-workflows-building-blocks` and `github-workflows-security` were spot-checked: `applyTo` comma lists became `paths:` arrays correctly.
Deduplication: all 20 files in `rounds/round-1/` were read. Findings already reported there (validator H1 write scope, M1 smoke/rollback drift, M2 Free-private carve-out, L1-L6; evaluator T-1 terraform required-reviewers model, R-1..R-3; tracked F-010, F-012) are NOT re-reported.

## Score

**7.8 / 10 (78 / 100). Verdict: PASS (overall >= 7.0, no lens below 5.0). 0 HIGH, 4 MEDIUM, 3 LOW.**

| Lens | Score | Basis |
|---|---|---|
| A Scope (G0-G4, XCC) | 8.0 | Clean router -> executor -> knowledge layering, no leakage of domain facts into agents or command; G0 not updated; review role split across two agents |
| B Flow (FCC) | 7.5 | Command chain complete and acyclic, NEEDS-INPUT and no-skill fallbacks defined; review path ambiguous; out-of-package skill dead ends; engineer ignores rules |
| C Engine (ECC) | 8.0 | Frontmatter, names, models, tool fields all valid; auto-listing cost low; rules depend on path injection that may not fire for new files; `.yaml` under-match |

## Dependency graph (as deployed)

```
G0     CLAUDE.md                                   (no entry for this package)
G3     building-cicd-pipelines  context: fork -> cicd-pipeline-engineer, disable-model-invocation: true
G1     cicd-pipeline-engineer   tools Read, Grep, Glob, Edit, Write, Bash; model sonnet
G1     cicd-pipeline-reviewer   tools Read, Grep, Glob; model sonnet; no /command (Agent tool or auto-delegation)
G2     github-workflows-security        paths **/.github/workflows/**
G2     github-workflows-pr-ci           paths **/.github/workflows/ci-*.yml
G2     github-workflows-merge-cd        paths **/.github/workflows/cd-*.yml
G2     github-workflows-building-blocks paths **/.github/workflows/_*.yml, **/.github/actions/**/action.yml
G2     (other pkg) openspec-github-state paths **/workflows/openspec-*.yml   overlap with security rule, intentional (DEC-001)
G4 x9  composing-github-actions-pipelines, automating-terraform-github-actions-v1-17, federating-github-actions-aws-oidc,
       federating-github-actions-oci, building-java-github-actions, publishing-container-images-github-actions,
       building-nextjs-github-actions-v16-4, limiting-blast-radius-github-actions-deploys, securing-supply-chain-github-actions
G4 ext automating-github-repos-with-actions (github-core, declared dependency)
G4 ext managing-terraform-cicd, provisioning-aws-iam-v6, deploying-aws-lambda, vercel-cli-with-tokens (NOT declared dependencies)
Orphans: none. Cycles: none (engineer has no Agent tool; reviewer does not redirect to the command).
```

Reachability: all 9 knowledge skills appear in the engineer routing table (`cicd-pipeline-engineer.agent.md:91-101`) with needs that match their descriptions, and in the reviewer evidence table (`cicd-pipeline-reviewer.agent.md:46-55`, composing loaded first at :41). Each is also reachable by description match (FCC.16 pass).

## Findings

### MEDIUM

**AUD-1 (MEDIUM) Review responsibility split across two agents; the command routes reviews to the wrong one.** Lenses: A (XCC.1, XCC.8, G1.7), B (FCC.4, FCC.8), C (auto-delegation by description).
- `skills/building-cicd-pipelines/SKILL.md:3` "must be written or reviewed"; `:58` usage example `/building-cicd-pipelines "review the existing .github/workflows against the blast-radius and supply-chain guardrails ..."` forks a pure review to the engineer.
- `agents/cicd-pipeline-engineer.agent.md:4,12` "writes or reviews"; step 5 (`:70`) "Write or review", but the engineer has no review procedure: no H1-H9 checks, and its report (`:149-155`) is built around "Files changed" and checks run, not findings with severity.
- `agents/cicd-pipeline-reviewer.agent.md:14-15` "Use when reviewing or auditing an existing pipeline" owns the mandatory HIGH checks (`:81-91`) and the findings format (`:131-148`).
- `README.md:58,83` says the reviewer is spawned through the Agent tool; the engineer never mentions the reviewer.
- Effect: a review request goes to whichever agent the router or the main session picks; via the command it always lands on the engineer and skips H1-H9. Both descriptions match "review our workflows", so auto-delegation is non-deterministic.
- Fix hint: narrow the engineer and the command to "write, or fix after review"; drop the review example at `SKILL.md:58` (or replace it with a write example); in the engineer add "for a review-only request return: use `cicd-pipeline-reviewer` (Agent tool)"; optionally add a review command (for example `/reviewing-cicd-pipelines`, `agent: cicd-pipeline-reviewer`) so the reviewer has an entry point.

**AUD-2 (MEDIUM) G0 not updated: CLAUDE.md does not list `/building-cicd-pipelines` or the two agents, and its fallback tells the main session to decline unlisted requests.** Lenses: A (G0.4, G0.5), B (FCC.9 at G0), C (stale budget counts).
- `grep -n "cicd" CLAUDE.md` returns 0 hits. `CLAUDE.md:116` "If a request does not match any `/command` listed above, respond with the closest matching command ... route or decline."
- Counts are stale after deploy: `CLAUDE.md:141,150,159,163` say 67 commands, 41 agents, 246 skills (179 knowledge), 50 rules; on disk now 43 agents, 54 rules, 256 skills, 188 without `disable-model-invocation`.
- Effect: in this repository a CI/CD request is declined or misrouted (closest listed command is `/provision-aws-terraform` or `managing-terraform-cicd`), even though the package is installed.
- Fix hint: at commit time add a GitHub Actions CI/CD paragraph next to the other package paragraphs (command, engineer, reviewer, 9 skills, 4 rules, dependencies), a `/building-cicd-pipelines` line under "How to run", and refresh the counts. CLAUDE.md is hand-authored, so this is outside `packages/` but part of shipping the package here.

**AUD-3 (MEDIUM) Engineer routes to four skills outside its declared dependencies, with no "not installed" path.** Lenses: A (G1.6, XCC.4), B (FCC.7, FCC.18).
- `apm.yml:7-10` depends only on `factory-core` and `github-core`.
- `agents/cicd-pipeline-engineer.agent.md:104-107` loads `managing-terraform-cicd`, `provisioning-aws-iam-v6`, `deploying-aws-lambda`, `vercel-cli-with-tokens` "only if the requirement touches them"; `:62-63` says "a sibling a skill merely references is an Ask-First question". The two sentences disagree on whether to load or ask, and neither covers a missing file. The command repeats the list (`SKILL.md:50-51`).
- They exist in this repo (from `oci-terraform`, `aws-terraform`, `aws-lambda`, `vercel-frontend`), not in a project that installs only this package. The flagship example ("Java Lambda CI+CD to AWS", `README.md:80`, `SKILL.md:56`) touches `deploying-aws-lambda`, so the main path reads a file that may not exist.
- Fix hint: make one rule in the engineer: "Related skills are optional. If `.claude/skills/<name>/SKILL.md` is absent, do not guess its content; list it under Open questions as 'install package X or accept unguided part'". Name the owning package for each in README and the engineer.

**AUD-4 (MEDIUM) The engineer never loads the four rules and does not say how rule Ask-First items apply to a non-interactive run.** Lenses: B (FCC.13, FCC.14), C (ECC.1, ECC.15).
- The reviewer loads rules explicitly (`cicd-pipeline-reviewer.agent.md:57-62`); the engineer has no rule step (workflow `:44-87`), and its Precedence (`:28-35`) ranks only its own Never Do and the skills.
- Path-scoped rules are injected when a matching file is read. In a repository with no `.github/workflows/` yet, step 4 (`:67-69`) finds nothing, so no rule is injected before the first Write. The rules then guard only edits of existing files.
- Rules contain user-facing asks: `github-workflows-security.instructions.md:37` Ask First "Adding a job with `id-token: write` or any write permission" (true of every CD job), `:38` `workflow_run` with secrets; `github-workflows-merge-cd.instructions.md:13` "Ask the user's GitHub plan", `:37` Free variant. Read literally by the engineer, every CD returns NEEDS-INPUT; ignored, the rule has no effect. The engineer's step 3 (`:64-66`) defines this filter for skill Ask-First tables only.
- Fix hint: add to engineer step 2 "Read the rules for the file types you will write: `.claude/rules/github-workflows-{security,pr-ci,merge-cd,building-blocks}.md`"; extend Precedence point 3 to rules; extend step 3: "a rule's Ask First item is a question only when the requirement does not already settle it (for example, 'CD to AWS via OIDC' settles `id-token: write` on the login job)".

### LOW

**AUD-5 (LOW) Rule globs miss `.yaml` workflows and `action.yaml` composites; the security rule does not cover composites.** Lenses: C (ECC.2), B (FCC.11).
- `github-workflows-pr-ci.instructions.md:4` `ci-*.yml`, `github-workflows-merge-cd.instructions.md:4` `cd-*.yml`, `github-workflows-building-blocks.instructions.md:4` `_*.yml` and `action.yml` only. The reviewer inventories `*.yaml` (`cicd-pipeline-reviewer.agent.md:69`), so it reviews files no scoped rule fires on.
- `github-workflows-security.instructions.md:4` `**/.github/workflows/**` excludes `.github/actions/**`, although composites run `run:` steps and pin third-party actions (building-blocks rules 5 and 7 cover part of it).
- Fix hint: add `.yaml` / `action.yaml` variants to the three scoped rules, or state in composing that only `.yml` is generated and have the reviewer flag `.yaml` as a naming finding; add `**/.github/actions/**/action.y*ml` to the security rule.

**AUD-6 (LOW) Reviewer naming check will flag openspec-github's own workflows.** Lenses: B (FCC.15), C (ECC.14).
- `cicd-pipeline-reviewer.agent.md:71-73`: files outside `ci-`/`cd-`/`ops-`/`_` naming are LOW findings. `openspec-github` ships `openspec-ci.yml`, `openspec-gate.yml`, `openspec-board-sync.yml`, `openspec-archive.yml` (`packages/openspec-github/.apm/skills/syncing-openspec-with-github-projects/assets/workflows/`), installed as `.github/workflows/openspec-*.yml`, where both `github-workflows-security` and `openspec-github-state` fire (overlap intentional, DEC-001).
- The two rules agree (SHA pins, `contents: read`, event text through `env:`, no `pull_request_target`): ECC.14 overlap PASS. Only the reviewer's naming check conflicts.
- Fix hint: in reviewer P1.2 classify `openspec-*.yml` as "owned by openspec-github, naming exempt; review against `openspec-github-state`".

**AUD-7 (LOW) Engineer safety depends on text only.** Lens: C (ECC.16, G1.2).
- `cicd-pipeline-engineer.agent.md:14` grants unrestricted `Bash`; the Never Do list (`:131-145`) forbids `terraform apply`, `gh workflow run`, `aws`, `oci`, `git push`. `.claude/settings.json` denies only `.env` and `*.tfvars` reads. The same holds for sibling executors (aws-terraform-engineer), so this is a family convention, not a package defect.
- Fix hint: in README "How to use", recommend consumer `permissions.deny` entries such as `Bash(terraform apply*)`, `Bash(terraform destroy*)`, `Bash(gh workflow run*)`, `Bash(gh secret*)`, `Bash(git push*)`.

## Consensus matrix

| Finding | A Scope | B Flow | C Engine | Agreement | Priority |
|---|---|---|---|---|---|
| AUD-1 review path split | X | X | X | 3/3 | must fix |
| AUD-2 CLAUDE.md not registered | X | X | X (counts) | 3/3 | must fix (at commit) |
| AUD-3 undeclared related skills | X | X | | 2/3 | should fix |
| AUD-4 engineer ignores rules / rule Ask First | | X | X | 2/3 | should fix |
| AUD-5 `.yaml` under-match | | X | X | 2/3 | should fix |
| AUD-6 openspec naming false positive | | X | X | 2/3 | consider |
| AUD-7 Bash text-only safety | | | X | 1/3 | consider |

## Passed checks (evidence)

- G3/FCC.1-5: `building-cicd-pipelines` has `context: fork`, `agent: cicd-pipeline-engineer` (file exists), `disable-model-invocation: true`, quoted `argument-hint`, no implementation code.
- G1.1/G1.7: neither agent carries domain facts; both state Does NOT. G1.2/ECC.8: `tools:` on agents, no `allowed-tools:` swap; reviewer is read-only.
- G1.4/ECC.12: `model: sonnet` on both. ECC.10/ECC.11: all 15 names kebab-case, equal to file/folder, each unique across `.claude/agents`, `.claude/rules`, `.claude/skills` (grep count 1 each).
- FCC.9: engineer fallback for uncovered stacks and clouds (`:109-111`); NEEDS-INPUT contract (`:46-59`); reviewer question contract (`:30-31`, `:37-40`). FCC.10: no cycles.
- ECC.4/ECC.13: 9 knowledge descriptions, 2,746 characters in total including the command (command is off-budget), each under 300 characters with "Use when" and most with a "Not for" clause; distinct from github-core `automating-github-repos-with-actions` ("Not for CI build matrices, deployments"). Low auto-listing cost.
- ECC.14: security rule overlaps the three scoped rules and `openspec-github-state` without contradiction.
- G2.3/G2.4: rules carry no routing table and no full code; each points to the owning skills.

## Validation (P5, objective data)

- `find packages/github-actions-cicd -type f`: 2 agents, 4 instructions, 10 skill folders (9 knowledge + 1 command), README, apm.yml.
- `ls .claude/agents | wc -l` = 43; `ls .claude/rules | wc -l` = 54; `ls .claude/skills | wc -l` = 256; skills without `disable-model-invocation: true` = 188.
- `grep -n cicd CLAUDE.md` = 0 hits.
- Deployed `.claude/rules/github-workflows-building-blocks.md` frontmatter: `paths:` list of 2 globs (conversion correct).
