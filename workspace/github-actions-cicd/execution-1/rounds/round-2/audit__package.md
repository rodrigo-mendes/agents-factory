# Audit: package github-actions-cicd, architecture consensus (P6 round 2, lean, architecture-auditor, 2026-10-30)

Spec: `audit-cc-architecture-consensus` adapted per brief; Scope (G0-G4, XCC), Flow (FCC) and Engine (ECC) lenses applied in one context, no lens agents spawned, no plan mode. Source only (`packages/github-actions-cicd/`). Approval relayed from G1 (2026-10-30); not a new approval.

## Score

**9.7 / 10 (100 - 0 HIGH - 1 x 2.5 MEDIUM - 2 x 0.5 LOW = 96.5). PASS.**

## Round-1 findings

| ID | Status | Evidence |
|---|---|---|
| AUD-1 review path split | FIXED | `agents/cicd-pipeline-engineer.agent.md:4-7,23-25` write/fix only, review-only returns NEEDS-INPUT pointing to `cicd-pipeline-reviewer`; `skills/building-cicd-pipelines/SKILL.md:3,17-18,68` same; review example replaced by a fix example (`SKILL.md:65`); `README.md:7,45,70`. Residual wording, see NEW-3. |
| AUD-2 CLAUDE.md | DEFERRED (P8, D-006) | not re-reported |
| AUD-3 undeclared related skills | FIXED | `cicd-pipeline-engineer.agent.md:122-127` one rule, owning package named, "not installed -> open question"; `SKILL.md:55-58`; `README.md:52` |
| AUD-4 engineer ignores rules | FIXED | step 2 loads the four rules (`:73-77`, with source fallback); Precedence 2 ranks rules (`:36-37`); rule Ask First is a question only when unsettled (`:81-84`, `:145-146`) |
| AUD-5 `.yaml` / composites under-match | FIXED | `instructions/*-pr-ci:4`, `*-merge-cd:4`, `*-building-blocks:4` use `{yml,yaml}`; `*-security:4` adds `**/.github/actions/**` |
| AUD-6 openspec naming false positive | FIXED | `agents/cicd-pipeline-reviewer.agent.md:75-77` exempts `openspec-*.yml` |
| AUD-7 Bash text-only safety | FIXED | `README.md:72-74` recommended `permissions.deny` entries |

## New findings

**NEW-1 (MEDIUM) Composing catalog out of sync with the owners it claims to copy.** Lenses: B (FCC.7 contract), C (ECC.14). Family rule 17: "block inputs exactly as the owning skill defines them (composing's catalog copies them, never invents)".
- `skills/composing-github-actions-pipelines/blueprints/catalog-reference.md:27` `_image-publish.yml` lists input `aws-role-arn`, which the owner does not define (`publishing-container-images-github-actions/blueprints/workflow-image-publish.md:25-35`; the ECR job reads `vars.ECR_PUSH_ROLE_ARN`, `workflow-image-publish-ecr-ocir.md:30,66`). A caller wired from the catalog fails with an undefined-input error. The same row omits `artifact-name` (owner `:35`, used by `building-nextjs-github-actions-v16-4/blueprints/standalone-container.md:56`).
- `catalog-reference.md:31` `_security-scan.yml` omits the `environment` input (owner `securing-supply-chain-github-actions/blueprints/workflow-security-scan.md:32,42`).
- `_code-security.yml` (owner `securing-supply-chain-github-actions/blueprints/workflow-licensed-jobs.md:20-25`, input `targets`; called from `workflow-callers.md:28` behind `vars.CODE_SECURITY_ENABLED`) is absent from the catalog.
- PASS: `role-duration-seconds` of `cloud/login-aws` is listed (`catalog-reference.md:41`) and matches the owner (`federating-github-actions-aws-oidc/blueprints/login-composite-action.md:30,42`).
- Mitigation: the catalog says the owner stays the authority (`:17`) and the engineer reads owner blueprints, so impact is limited to callers wired from the catalog alone.
- Fix: in `catalog-reference.md:27` drop `aws-role-arn`, add `artifact-name` and a note "ECR role read from `vars.ECR_PUSH_ROLE_ARN` of the `environment`"; in `:31` add `environment`; add a `_code-security.yml` row (input `targets`; caller-side `if: vars.CODE_SECURITY_ENABLED == 'true'`; only that caller job gets `security-events: write`, `pull-requests: write`; owner `securing-supply-chain-github-actions`).

**NEW-2 (LOW) Third AWS role (`ECR_PUSH_ROLE_ARN` in `<env>-publish`) is not in the canonical names.** Lenses: A (XCC consistency), C.
- Verdict: an **acceptable third role**, not a design defect. A push-only role in its own environment is least privilege, keeps `id-token: write` on the ECR job only (rule 18) and never binds on PR (`workflow-image-publish-ecr-ocir.md:66`; `registry-credentials.md:21-22,26`).
- Gap: rule 17 (`_family_rules.md:21`) lists only `<env>`/`<env>-pr` and `AWS_PR_ROLE_ARN`/`AWS_DEPLOY_ROLE_ARN`. Only the images skill refers to it (`registry-credentials.md:21`, `workflow-callers.md:81,94`, `evaluation-scenarios.md:23`); `federating-github-actions-aws-oidc` (owner of the trust format, cited by `registry-credentials.md:21`), `limiting-blast-radius-github-actions-deploys`, `github-workflows-merge-cd` and the catalog do not mention `<env>-publish`, so a CD that publishes to ECR needs a third environment and trust policy that only one skill tells the user about.
- Fix: add to rule 17 "publish stage: environment `<env>-publish`, variable `ECR_PUSH_ROLE_ARN` (images only)"; one line in the aws-oidc trust table and in the catalog `_image-publish` row; the engineer's user-must-add list then covers it.

**NEW-3 (LOW) Leftover "review" in engineer step 5.** Lens: B. `cicd-pipeline-engineer.agent.md:88` "**Write or review** following each skill's rows" contradicts `:4-7,23-25`. Fix: "Write or fix".

## Verification note (not a finding)

The `applyTo` values now combine brace sets with a comma-separated list (`instructions/github-workflows-building-blocks.instructions.md:4`). At the P7 install, confirm the deployed `paths:` keeps `_*.{yml,yaml}` intact and is not split on the comma inside the braces (precedent: `camel-quarkus-integrator-project-config.instructions.md:4` uses braces with commas). Not checked here: the brief forbids reading `.claude/`.

## Consensus matrix

| Finding | A | B | C | Priority |
|---|---|---|---|---|
| NEW-1 catalog drift | | X | X | should fix |
| NEW-2 `<env>-publish` not canonical | X | | X | consider |
| NEW-3 step 5 wording | | X | | consider |

## Validation (objective)

- `grep -n "_code-security" catalog-reference.md`: 0 hits; `grep -rn "aws-role-arn"` in skills: only `catalog-reference.md:27`.
- `grep -rn "ECR_PUSH_ROLE_ARN\|<env>-publish"`: hits only under `publishing-container-images-github-actions/`.
- Package file set unchanged: 2 agents, 4 instructions, 10 skills (9 knowledge + 1 command), README, apm.yml (dependencies `factory-core`, `github-core`).
