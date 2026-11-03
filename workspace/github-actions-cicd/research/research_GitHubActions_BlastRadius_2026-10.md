# Research: Limiting blast radius of GitHub Actions deployments (GitHub Team / Pro / Free, private repos) for Lambda, containers, S3+CloudFront, Vercel and Terraform

> Unit: `limiting-blast-radius-github-actions-deploys`. Source item: "user: blast radius". Spec:
> `researching-technical-frameworks` (default depth = exhaustive, MAX_ITERATIONS = 5). Brief:
> `workspace/github-actions-cicd/execution-1/briefs/P4-research-limiting-blast-radius-github-actions-deploys.md`.
> Every page was read on 2026-10-30. Family facts (F1-F24) and family rules (1-16) from
> `workspace/github-actions-cicd/_family_facts.md` / `_family_rules.md` are applied as given.
> No agents or investigators were spawned and plan mode was not entered; scope approval is the
> relayed G1/G2 approval recorded in `state/gates/G1.md` and `state/gates/G2.md` (a relay, not a
> new approval).
>
> Section-order note: the brief requires the file to END with `## Source Bibliography`, so that
> section moves from its template position to the end, after `## Pages read`. All 15 template
> sections are present.
>
> Version note: docs.github.com, docs.aws.amazon.com and developer.hashicorp.com pages carry no
> version number or publish date; they are the current GitHub.com and AWS pages and the read date
> (2026-10-30) is the date recorded. Vercel pages carry `last_updated` front matter, recorded per
> page. The REST pages show `X-GitHub-Api-Version: 2026-03-10`. Several docs.github.com
> "who can use this feature" boxes are not rendered by the fetcher; for those, the plan statement
> was read from the docs source repository (`github/docs`, `data/reusables/gated-features/*.md`),
> which is GitHub's own source for the same box (official, flagged per row).
>
> Neighbour units (not repeated here, referenced by name only, family rule 12):
> `automating-terraform-github-actions-v1-17` (plan/apply mechanics), `federating-github-actions-aws-oidc`
> and `federating-github-actions-oci` (login), `publishing-container-images-github-actions`
> (build/push), `deploying-aws-lambda` (Lambda release steps), `vercel-cli-with-tokens`.

## Metadata

```yaml
Full_Name: Blast-radius control for GitHub Actions deployments (environments, branch rules, artifact promotion, progressive delivery, rollback)
Target_Version: GitHub.com (GitHub Free / Pro / Team, PRIVATE repositories) as documented on 2026-10-30; REST API version 2026-03-10; actions pinned per _family_facts.md (F3, F10, F23, F24)
Release_Date: n/a (SaaS docs, undated); read date 2026-10-30
Support_Status: Current GitHub.com docs; AWS current docs; Vercel docs last_updated 2026-03-17..2026-09-08
Primary_Docs:
  - https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
  - https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
  - https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments
  - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
  - https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html
  - https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentConfiguration.html
  - https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html
  - https://vercel.com/docs/deployments/promoting-a-deployment
Integration_Partners: AWS Lambda (alias routing, optional CodeDeploy), Amazon ECS (ROLLING/BLUE_GREEN/LINEAR/CANARY), Amazon ECR, S3 + CloudFront (continuous deployment, origin path), Vercel CLI (promote/rollback/prebuilt), Terraform (small state components)
Target_Plan: GitHub Team / Pro / Free with PRIVATE repositories (family rule 16, G2 DEC-011)
Research_Date: 2026-10-30
Domain_Complexity: Complex
Research_Depth: exhaustive (default)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 4 of 5
Triangulated_Count: 6
Unverified_Count: 9
Irresolvable_Count: 0
Research_Quality_Score: 87%   # ~70 claims, 9 unverified
```

## Executive Summary

Blast radius in a GitHub Actions delivery pipeline is the set of cloud resources and users a single
bad change, compromised branch, or mistaken run can reach. On GitHub.com it is limited by four
layers: (1) which code is allowed to run with deploy credentials (branch rules plus environment
deployment branch policies); (2) which credentials that code receives (environment-scoped secrets
and one cloud role per environment); (3) how much traffic a new release reaches before it is
verified (progressive delivery and smoke tests); (4) how fast it can be undone (rollback to an
immutable, already-verified artifact). Concurrency groups and timeouts keep two runs from racing on
the same environment.

What changes for the target plan (the central finding): on GitHub Free, Pro and Team, the
environment features most tutorials rely on for human approval are public-repository only.
docs.github.com states: "If you are on a GitHub Free, GitHub Pro, or GitHub Team plan, required
reviewers are only available for public repositories", and the same for wait timers, custom
deployment protection rules and "Allowing administrators to bypass protection rules". For PRIVATE
repositories, "Organizations with GitHub Team and users with GitHub Pro can configure environments",
with environment secrets, environment variables and deployment branches and tags; "Users with GitHub
Free plans can only configure environments for public repositories". Protected branches and
rulesets are available on private repositories only with Pro, Team or Enterprise Cloud (docs source
reusables). Therefore the default human approval for Pro/Team is the pull-request review of the
rendered plan/diff before merge to `main`, enforced by a ruleset (or branch protection), combined
with an environment whose deployment branch policy admits only `main` and an AWS role whose trust
pins `sub = repo:ORG/REPO:environment:<env>`. GitHub Free private repositories cannot express any
of these server-side controls; the Free variant is explicitly weaker (every collaborator with write
access can deploy) and only cloud-side trust narrowing remains. Required reviewers are the upgrade
path (public repository or GitHub Enterprise), never the default (family rule 16).

The three critical patterns: (1) build once and promote the same immutable artifact (zip SHA-256,
image digest, Vercel prebuilt output, Terraform saved plan) dev -> stage -> prod; never rebuild for
prod (family rule 8). (2) One GitHub environment, one cloud role and one state/target per
environment, with environment-scoped secrets and a `main`-only deployment branch policy for every
deployable environment; PR jobs use a separate `<env>-pr` read role (family rules 10 and 13). (3)
Release to a fraction first where the target supports it natively (Lambda weighted alias, ECS
`CANARY`/`LINEAR`/`BLUE_GREEN` with alarms, CloudFront staging distribution, Vercel staged
production build + `vercel promote`), smoke-test, and roll back by repointing (alias, task set,
origin path, `vercel rollback`) instead of rebuilding. Tier = Complex: security-critical,
plan-dependent, five deployment targets.

## Architectural Guardrails

> Confidence legend: High = official page read in full or for the cited section, Triangulated
> where 2+ official sources agree | (medium confidence) = one source, partly read, or inferred from
> two sources | (unverified) = no official confirmation found.

### Plan availability matrix (private repositories, GitHub.com, read 2026-10-30)

| Feature | Free (private) | Pro (private) | Team (private) | Source |
|---|---|---|---|---|
| Create environments | No ("can only configure environments for public repositories") | Yes | Yes | manage-environments; gated-features/environments.md |
| Environment secrets | No ("environment secrets are only available in public repositories") | Yes | Yes | deployments-and-environments |
| Environment variables | No (follows from "no environments"; not stated separately) | Yes | Yes | deployments-and-environments |
| Deployment branches and tags policy | No | Yes ("also available for private repositories") | Yes | deployments-and-environments |
| Required reviewers | No | No ("only available for public repositories") | No | deployments-and-environments; gated-features/environments.md |
| Wait timer | No | No | No | same |
| Custom deployment protection rules | No | No | No | deployments-and-environments |
| Allow/disallow admin bypass of environment rules | No | No (public only) | No (public only) | deployments-and-environments |
| Protected branches | No (public only) | Yes | Yes | gated-features/protected-branches.md; githubs-plans |
| Rulesets (branch/tag) | No (public only) | Yes | Yes | gated-features/repo-rules.md |
| Push rulesets | No | No (unverified for Pro) | Yes | gated-features/repo-rules.md |
| Ruleset `evaluate` enforcement | No | No | No ("only available with GitHub Enterprise") | REST repos/rules |
| Bypass lists on branch protection | n/a | No (user-owned) | Yes ("only when the repository belongs to an organization") | about-protected-branches |
| Required reviewers (teams) in ruleset PR rule | No | No ("not available on user-owned repositories") | Yes | available-rules-for-rulesets |
| "Required pull request reviewers", "Code owners" | No | Yes | Yes | githubs-plans |

Consequence: on Pro/Team private, an environment can scope secrets and restrict which branch may
deploy, but cannot pause a run for a human. The human gate must sit before `main` (PR review).

### ✅ Mandatory Patterns

**A1. Default human approval on Pro/Team = PR review before merge to `main`, enforced by a ruleset**
> Confidence: High | [✓✓ Triangulated | available-rules-for-rulesets (2026-10-30) + REST repos/rules (2026-10-30) + gated-features/repo-rules.md (2026-10-30)]
- Why: required reviewers are unavailable on Pro/Team private repositories (matrix), while rulesets are available there. The ruleset rule "Require a pull request before merging" with "Required approvals", "Dismiss stale approvals", "Require approval of the most recent reviewable push" ("an approval from someone other than the last person to push") and "Require status checks to pass before merging" makes the reviewed plan the approval. The status check is the plan/diff job of the PR workflow (`ci-<app>.yml`), whose rendered plan the reviewer reads.
- Code:
  ```bash
  # Representative — adapt to your environment (REST API version 2026-03-10)
  gh api -X POST repos/ORG/REPO/rulesets \
    -H "X-GitHub-Api-Version: 2026-03-10" --input - <<'JSON'
  {
    "name": "main-reviewed-deploys",
    "target": "branch",
    "enforcement": "active",
    "bypass_actors": [],
    "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
    "rules": [
      { "type": "deletion" },
      { "type": "non_fast_forward" },
      { "type": "pull_request", "parameters": {
          "required_approving_review_count": 1,
          "dismiss_stale_reviews_on_push": true,
          "require_code_owner_review": false,
          "require_last_push_approval": true,
          "required_review_thread_resolution": true,
          "allowed_merge_methods": ["squash"] } },
      { "type": "required_status_checks", "parameters": {
          "strict_required_status_checks_policy": true,
          "required_status_checks": [ { "context": "plan" } ] } }
    ]
  }
  JSON
  # Expected: HTTP 201 with the ruleset JSON (id, enforcement "active")
  ```
- Note: `bypass_actors: []` keeps admins from merging around the review. `evaluate` is Enterprise-only, so use `active`.
- Source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets (2026-10-30); https://docs.github.com/en/rest/repos/rules (2026-10-30); https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/repo-rules.md (2026-10-30)

**A2. Every deployable environment has a deployment branch policy that admits only `main` (Pro/Team)**
> Confidence: High | [✓✓ Triangulated | deployments-and-environments (2026-10-30) + REST environments + branch-policies (2026-10-30)]
- Why: "For users on GitHub Pro or GitHub Team plans, deployment branches and tags are also available for private repositories." "Selected branches and tags: Only branches and tags that match your specified name patterns can deploy to the environment." Combined with A1, only reviewed code reaches the environment's secrets. "All deployment protection rules must pass before a job referencing the environment is sent to a runner." Prefer "Selected branches" = `main` over "Protected branches only", because the latter admits any protected branch.
- Code:
  ```bash
  # Representative — adapt to your environment (REST API version 2026-03-10)
  gh api -X PUT repos/ORG/REPO/environments/prod -H "X-GitHub-Api-Version: 2026-03-10" \
    --input - <<'JSON'
  { "deployment_branch_policy": { "protected_branches": false, "custom_branch_policies": true } }
  JSON
  gh api -X POST repos/ORG/REPO/environments/prod/deployment-branch-policies \
    -H "X-GitHub-Api-Version: 2026-03-10" -f name=main -f type=branch
  # Expected: 200 then 200/201 with {"name":"main","type":"branch",...}
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30); https://docs.github.com/en/rest/deployments/environments (2026-10-30); https://docs.github.com/en/rest/deployments/branch-policies (2026-10-30)

**A3. One environment = one cloud role = one state/target; secrets that can deploy are environment-scoped**
> Confidence: High (GitHub side) | (medium confidence) for the role-per-environment inference
- Why: environment secrets are available to a job only after it is sent to a runner, which happens only after the environment's rules pass ("The job can access the environment's secrets only after the job is sent to a runner"). Family rule 10 makes this mandatory. The AWS side (trust `sub = repo:ORG/REPO:environment:<env>`) is owned by `federating-github-actions-aws-oidc`; this unit only requires that each environment maps to its own role, its own Terraform state key and its own target (account/project), so a compromised `dev` credential cannot touch `prod`. Terraform guidance: "Any operation on a resource can potentially affect other resources managed in the same state file".
- Matrix (representative):

  | GitHub environment | Branch policy | Cloud identity | State / target | Created on |
  |---|---|---|---|---|
  | `dev-pr` | all branches (read-only role) | `<app>-dev-pr-read` | read-only on dev state | Pro/Team |
  | `dev` | `main` | `<app>-dev-deploy` | `dev/<component>.tfstate`, dev account | Pro/Team |
  | `stage` | `main` | `<app>-stage-deploy` | `stage/<component>.tfstate`, stage account | Pro/Team |
  | `prod` | `main` | `<app>-prod-deploy` | `prod/<component>.tfstate`, prod account | Pro/Team |
- Source: https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments (2026-10-30); https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects (2026-10-30)

**A4. Build once; promote the same immutable artifact by hash or digest; verify before each deploy**
> Confidence: High | [✓✓ Triangulated | Lambda versions (2026-10-30) + ECR tag immutability (2026-10-30) + Vercel prebuilt (2026-09-08)]
- Why: family rule 8. Lambda: "After you publish a function version, its code, runtime, architecture, memory, layers, and most other configuration settings are immutable"; "Lambda never reuses version numbers". ECR: with tag immutability "the `ImageTagAlreadyExistsException` error is returned if you push an image with a tag that is already in the repository". Vercel: `vercel build` then `vercel deploy --prebuilt` uploads build output "without a remote build of your source code". The build job records `sha256` of the zip (or the image digest) as a job output; every deploy job downloads the artifact (F24), recomputes the hash and fails on mismatch.
- Code:
  ```yaml
  # Representative — adapt to your environment (actions per _family_facts.md F23/F24)
  - name: Verify artifact hash before deploy
    run: |
      echo "${EXPECTED_SHA256}  dist/function.zip" | sha256sum -c -
    env:
      EXPECTED_SHA256: ${{ needs.build.outputs.zip_sha256 }}
  # Expected: "dist/function.zip: OK"; any other output fails the job
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html (2026-10-30); https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html (2026-10-30); https://vercel.com/docs/cli/deploying-from-cli (last_updated 2026-09-08, read 2026-10-30)

**A5. One concurrency group per app x environment; never cancel a running deploy**
> Confidence: High (semantics) | (medium confidence) for "never cancel" rationale
- Why: "there can be at most one running job or workflow in a concurrency group at any time"; by default "any existing `pending` job or workflow in the same concurrency group will be canceled" when a new run queues; `cancel-in-progress: true` also cancels the running one. Cancelling a deploy mid-flight (alias half-shifted, Terraform apply partly done) leaves the environment in an intermediate state (medium confidence, inferred). Use `cancel-in-progress: false`; choose `queue: single` (default, newest pending wins) or `queue: max` ("Up to 100 jobs or workflow runs can be `pending`") when every merge must deploy in order. `queue: max` with `cancel-in-progress: true` "is not allowed and will result in a workflow validation error".
- Code:
  ```yaml
  # Representative — adapt to your environment
  concurrency:
    group: deploy-orders-prod
    cancel-in-progress: false
  ```
- Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30)

**A6. Explicit `timeout-minutes` on every deploy job and long step**
> Confidence: High
- Why: job default is "Default: 360" minutes; a hung deploy holds the concurrency group (A5) and blocks the next release. Step `timeout-minutes`: "Maximum: 360"; "must be a positive integer". Set the job timeout to the longest expected bake/shift time plus margin.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30; characters 100000-235839 read for this section)

**A7. Record deployments: `environment: { name, url }` on the deploying job**
> Confidence: High
- Why: by default "when a workflow job references an environment, GitHub creates a deployment object"; "The URL maps to `environment_url` in the deployments API"; "the environment is displayed on the main page of the repository". Querying `GET /repos/{owner}/{repo}/deployments?environment=prod&sha=<sha>` gives the audit trail of which commit is live per environment; deployment statuses carry `environment_url`, `log_url` and `auto_inactive` ("Adds a new inactive status to all prior non-transient, non-production environment deployments").
- Code:
  ```bash
  # Representative — adapt to your environment (REST API version 2026-03-10)
  gh api "repos/ORG/REPO/deployments?environment=prod&per_page=5" \
    -H "X-GitHub-Api-Version: 2026-03-10" --jq '.[] | {id, sha, ref, created_at}'
  # Expected: JSON objects, newest first, one per prod deployment
  ```
- Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments (2026-10-30); https://docs.github.com/en/rest/deployments/deployments (2026-10-30); https://docs.github.com/en/rest/deployments/statuses (2026-10-30)

**A8. Lambda: publish a version, shift a weighted alias, smoke-test, then complete or revert**
> Confidence: High | [✓✓ Triangulated | Lambda alias routing (2026-10-30) + Lambda versions (2026-10-30)]
- Why: "You can point an alias to a maximum of two Lambda function versions"; both must share the execution role and DLQ configuration and be published ("The alias cannot point to `$LATEST`"). Shift with `--routing-config AdditionalVersionWeights={"2"=0.05}`; finish with `--function-version 2 --routing-config AdditionalVersionWeights={}`; revert by setting the weights back to `{}` on the old version. Verify which version served via the `START ... Version:` log line, the `ExecutedVersion` metric dimension, or the `x-amz-executed-version` response header. "At low traffic levels, you might see a high variance between the configured and actual percentage". Release steps (waiters, publish, alias) are owned by `deploying-aws-lambda`.
- Code:
  ```bash
  # Representative — adapt to your environment (AWS CLI v2)
  aws lambda update-alias --function-name orders --name live \
    --routing-config 'AdditionalVersionWeights={"42"=0.10}'
  # smoke + alarm check, then either:
  aws lambda update-alias --function-name orders --name live --function-version 42 \
    --routing-config 'AdditionalVersionWeights={}'      # complete
  aws lambda update-alias --function-name orders --name live \
    --routing-config 'AdditionalVersionWeights={}'      # revert (alias stays on old version)
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html (2026-10-30); https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html (2026-10-30)

**A9. ECS: use a native deployment strategy with automatic failure detection**
> Confidence: High (strategy values) | (medium confidence) for alarm support per strategy
- Why: `DeploymentConfiguration.strategy` valid values are `ROLLING | BLUE_GREEN | LINEAR | CANARY`. `CANARY` "shifts a small percentage of traffic to the new service revision first, then shifts the remaining traffic all at once after a specified time period"; `LINEAR` shifts "in equal percentages over time"; `bakeTimeInMinutes` is required for `BLUE_GREEN`; `lifecycleHooks` run Lambda functions or pause hooks (resume with `ContinueServiceDeployment`). For `ROLLING`, the deployment circuit breaker and CloudWatch alarms can fail and roll back ("If you use the rollback option, when a service deployment fails, the service is rolled back to the last deployment that completed successfully"). The alarm page says alarms are "only supported for Amazon ECS services that use the rolling update (`ECS`) deployment controller"; whether this includes `BLUE_GREEN`/`LINEAR`/`CANARY` strategies on the ECS controller is not stated (unverified). Deploy by image digest (A4).
- Code:
  ```bash
  # Representative — adapt to your environment (ROLLING with alarm rollback, from AWS docs)
  aws ecs update-service --cluster prod --service orders \
    --task-definition orders:57 \
    --deployment-configuration "alarms={alarmNames=[orders-5xx],enable=true,rollback=true},deploymentCircuitBreaker={enable=true,rollback=true}"
  aws ecs wait services-stable --cluster prod --services orders
  ```
- Source: https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentConfiguration.html (2026-10-30); https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-alarm-failure.html (2026-10-30); https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-blue-green.html (2026-10-30)

**A10. Vercel: deploy a staged production build from the prebuilt artifact, smoke-test its URL, then `vercel promote`**
> Confidence: High (each command) | (medium confidence) for combining `--prebuilt` with `--skip-domain`
- Why: "Promote a staged production build ... won't trigger a rebuild"; staged = `vercel --prod --skip-domain` then `vercel promote [deployment-id or url]`; `--timeout` default `3m` and a timeout "does not affect the actual promotion". Promoting a Preview deployment instead causes "a new production deployment" (rebuild with production variables), which breaks build-once (A4). Token handling belongs to `vercel-cli-with-tokens`.
- Source: https://vercel.com/docs/deployments/promoting-a-deployment (last_updated 2026-06-26); https://vercel.com/docs/cli/deploying-from-cli (2026-09-08); https://vercel.com/docs/cli/promote (2026-07-15); all read 2026-10-30

### ⚠️ Conditional Patterns

**C1. Which approval model? (Ask First)**
- Options:
  - A) Pro/Team default: A1 ruleset PR review + A2 `main`-only environments; prod deploys automatically after merge, passing through dev and stage jobs.
  - B) Pro/Team + manual prod trigger: same as A, but `prod` runs from `ops-promote-<app>.yml` on `workflow_dispatch`. Running it needs "Write access to the repository"; the environment branch policy rejects any `--ref` other than `main`. Adds an explicit "go" without required reviewers. Weakness: any writer may press it (medium confidence that this is acceptable to the user).
  - C) Upgrade path: required reviewers + `prevent_self_review` + "Allow administrators to bypass" off. Available only for public repositories or GitHub Enterprise (tag: upgrade path). Up to "six users or teams"; "Only one of the required reviewers needs to approve".
  - D) Free variant (see C2).
- Tradeoffs: A is fastest; B adds a human click at prod; C is the only server-enforced pause of a running job.
- Source: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow (2026-10-30); https://docs.github.com/en/rest/deployments/environments (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30)

**C2. GitHub Free private repository variant (explicitly weaker)**
- Facts: no environments, no environment secrets, no deployment branch policies, no protected branches or rulesets on private repos (matrix). Every collaborator with write access can push to `main` and run any workflow on any branch.
- Weaker design: (1) keep the write collaborator list minimal; (2) no long-lived cloud secrets: AWS OIDC role trust pinned to `sub = repo:ORG/REPO:ref:refs/heads/main` (format owned by `federating-github-actions-aws-oidc`), so a run from another branch cannot assume the deploy role; (3) prod deploy only from `workflow_dispatch` with a job guard `if: github.ref == 'refs/heads/main'` (advisory only, a writer can edit it); (4) same build-once, progressive delivery, concurrency and timeouts as Pro/Team. Do not reference `environment:` in Free private workflows (behaviour unverified). Where a secret is unavoidable (OCI API key, Vercel token), it is a repository secret readable by every writer's workflow run, which breaks family rule 10; record this as an accepted risk and recommend Pro/Team.
- State the residual risk in the skill: "On Free private, any writer can deploy to prod."
- Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (2026-10-30); https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/protected-branches.md (2026-10-30); https://docs.github.com/en/get-started/learning-about-github/githubs-plans (2026-10-30)

**C3. Solo maintainer on Pro (no second reviewer)**
- A ruleset requiring 1 approval with `require_last_push_approval` cannot be satisfied by the only collaborator (approval must come from "someone other than the last person to push"). Options: add a second collaborator (preferred), or set `required_approving_review_count: 0` and keep required status checks (the plan becomes a self-review), or C1-B manual trigger. Bypass lists are not an option on user-owned repositories ("Actors may only be added to bypass lists when the repository belongs to an organization").
- Source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches (2026-10-30); https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets (2026-10-30)

**C4. Lambda: plain weighted alias vs CodeDeploy**
- A) Workflow-driven alias shift (A8): no extra service; the workflow owns smoke and revert.
- B) CodeDeploy deployment group with `CodeDeployDefault.LambdaCanary10Percent5Minutes` (or 10/15/30 min) or `LambdaLinear10PercentEvery{1,2,3,10}Minute(s)`; "You can configure a deployment group or deployment to automatically roll back when a deployment fails or when a monitoring threshold you specify is met". Rollbacks are "new deployments, with new deployment IDs".
- Choose B when rollback must happen even if the GitHub runner dies mid-shift (medium confidence, inferred).
- Source: https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html (2026-10-30); https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html (2026-10-30)

**C5. S3 + CloudFront: versioned-prefix switch vs CloudFront continuous deployment**
- A) Versioned prefix: upload to `s3://bucket/releases/<sha>/`, then change the origin's Origin path (`/releases/<sha>`); rollback = previous path. "CloudFront continues to serve objects that are already in an edge cache until the TTL on each object expires", so pair with an invalidation (invalidation API not read: medium confidence).
- B) Continuous deployment: staging distribution (`copy-distribution --staging`) + policy `SingleWeight` (`.01`-`.15`) or `SingleHeader`; promote with `update-distribution-with-staging-config`, which "copies the configuration from the staging distribution to the primary distribution" and "routes all traffic to the primary distribution". Limits: max weight 15%, 20 staging distributions per account, no HTTP/3, WAF ACL association frozen, and "CloudFront sends all requests to the primary distribution during peak traffic hours". It tests CDN configuration; pointing the staging distribution at a new origin path to canary site content is an inference (medium confidence).
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html (2026-10-30); https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/working-with-staging-distribution-continuous-deployment-policy.html (2026-10-30); https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html (2026-10-30)

**C6. Terraform component size**
- Split state by volatility, by stateful vs stateless, by team/privilege and by environment ("group resources by volatility"; "By managing stateful resources independently of stateless ones"; "split up workspaces based on team responsibilities and required privileges"). Each component gets its own job, state key and role, so a plan for `app-compute` cannot destroy `data-db`. Plan/apply mechanics: `automating-terraform-github-actions-v1-17`.
- Source: https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects (2026-10-30)

**C7. PR jobs: `deployment: false` on the `<env>-pr` environment (Pro/Team)**
- `deployment: false` lets a job "use an environment's secrets and variables without creating a deployment object", keeping PR read jobs out of deployment history. Caveat: "Custom deployment protection rules (GitHub Apps) require a deployment object"; whether deployment branch policies still apply is not stated (unverified). Effect on the OIDC `sub` claim not stated (unverified).
- Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments (2026-10-30)

### 🚫 Forbidden Patterns

**N1. Relying on required reviewers / wait timers as the approval gate on Pro/Team/Free private repos**
- Why: "required reviewers are only available for public repositories" on Free/Pro/Team; the setting is unavailable, so the pipeline would ship without the gate the authors believe exists.
- ❌ Wrong:
  ```yaml
  # assumes a human pauses this job; on Pro/Team private nothing pauses it
  deploy-prod:
    environment: prod   # "required reviewers" not configurable here
  ```
- ✅ Correct:
  ```yaml
  # approval happened at PR review (ruleset A1); env admits only main (A2)
  deploy-prod:
    if: github.ref == 'refs/heads/main'
    environment: { name: prod, url: "https://orders.example.com" }
  ```
- Impact: unreviewed code reaches prod. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30)

**N2. Rebuilding for each environment**
- ❌ Wrong: `cd-orders.yml` runs `mvn package` / `docker build` / `vercel build` again in the prod job.
- ✅ Correct: build once, upload (F23), download (F24), `sha256sum -c` (A4); images by `repo@sha256:<digest>`; Vercel `vercel deploy --prebuilt`.
- Impact: prod runs bytes nobody tested. Source: family rule 8; https://vercel.com/docs/cli/deploying-from-cli (2026-09-08)

**N3. `cancel-in-progress: true` on a deploy concurrency group**
- ❌ Wrong:
  ```yaml
  concurrency: { group: deploy-orders-prod, cancel-in-progress: true }
  ```
- ✅ Correct:
  ```yaml
  concurrency: { group: deploy-orders-prod, cancel-in-progress: false }
  ```
- Impact: a running alias shift or apply is killed mid-way (medium confidence on impact). Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (2026-10-30)

**N4. "Protected branches only" or "No restriction" deployment branch policy on prod**
- ❌ Wrong: `{"deployment_branch_policy": null}` (all branches) or `{"protected_branches": true, ...}` with several protected branches.
- ✅ Correct: `{"protected_branches": false, "custom_branch_policies": true}` + policy `main` (A2).
- Impact: any branch (or any protected branch) receives prod secrets. Source: https://docs.github.com/en/rest/deployments/environments (2026-10-30)

**N5. Ruleset with bypass actors or `enforcement: evaluate` on Pro/Team**
- ❌ Wrong: `"bypass_actors": [{"actor_type":"RepositoryRole","actor_id":5,"bypass_mode":"always"}]`, `"enforcement":"evaluate"`.
- ✅ Correct: `"bypass_actors": []`, `"enforcement": "active"` (A1).
- Impact: admins merge unreviewed; `evaluate` "is only available with GitHub Enterprise". Source: https://docs.github.com/en/rest/repos/rules (2026-10-30)

**N6. Promoting a Vercel Preview deployment to production**
- ❌ Wrong: `vercel promote https://orders-git-feature-x.vercel.app --yes` (Preview build).
- ✅ Correct: `vercel promote <staged production deployment url>` (A10).
- Impact: "will result in a new production deployment" (rebuild with production variables). Source: https://vercel.com/docs/cli/promote (2026-07-15)

**N7. Pointing a Lambda alias at `$LATEST` or a weighted alias across different roles/DLQs**
- ❌ Wrong: `aws lambda update-alias --name live --function-version '$LATEST'`
- ✅ Correct: publish a version and point the alias at its number (A8).
- Impact: "The alias cannot point to `$LATEST`"; versions must share role and DLQ config. Source: https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html (2026-10-30)

**N8. Mutable image tags for promotion**
- ❌ Wrong: `image: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/orders:latest`
- ✅ Correct: `image: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/orders@sha256:<digest>` and repository `--image-tag-mutability IMMUTABLE`.
- Impact: the tag can be overwritten between stage and prod. Source: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html (2026-10-30)

## Migration Guide

No version jump applies (SaaS). Changes found in the current docs that invalidate older tutorials:

| Change | Old assumption | Current fact | Source |
|---|---|---|---|
| Rulesets on private repos | Branch protection only | Rulesets available on Pro/Team/Enterprise Cloud private repos | gated-features/repo-rules.md |
| Environment without deployment record | Every `environment:` creates a deployment | `deployment: false` opts out; required reviewers and wait timers still apply; custom protection rules fail the job | control-deployments |
| Concurrency queue | At most one pending | `queue: max` allows up to 100 pending; incompatible with `cancel-in-progress: true` | control-workflow-concurrency |
| ECS progressive delivery | CodeDeploy needed for blue/green, canary, linear | Native `strategy` = `ROLLING | BLUE_GREEN | LINEAR | CANARY` with bake time and lifecycle hooks | API_DeploymentConfiguration |
| Vercel rollback state | Push restores normal flow | After rollback "Vercel turns off auto-assignment of production domains"; undo with `vercel promote` | instant-rollback |
| Doc example action majors | Copy from docs | Take versions only from `_family_facts.md` (lesson 1) | brief |

Introduction dates for these changes were not on the pages read (unverified).

## Implementation Blueprint

Step 1 (Pro/Team): create environments `dev-pr`, `dev`, `stage`, `prod`; set A2 policies on the
three deployable ones; store deploy secrets only as environment secrets, and non-secret values
(role ARN, region, app URL) as environment variables (A3).

Step 2: create the A1 ruleset on the default branch; required status check = the plan job name of
`ci-<app>.yml`.

Step 3: caller `cd-orders.yml` (merge to `main`) — build once, then one reusable deploy per
environment. Pins per family rule 4 (F3, F10, F23, F24). The called workflow reads the role ARN from
`vars.AWS_ROLE_ARN` inside its own job that declares `environment: ${{ inputs.environment }}`, so
the caller passes no secrets (family rule 6: no `secrets: inherit`; nothing to pass by name here).
That environment-scoped values resolve inside the called job and not in the caller (which has no
environment) is (medium confidence): the reusable-workflow page was read by the Composing unit, not
re-read here.

```yaml
# Representative — adapt to your environment
# .github/workflows/cd-orders.yml  (Pro/Team private repo)
name: cd-orders
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    outputs:
      zip_sha256: ${{ steps.hash.outputs.zip_sha256 }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - run: ./build.sh            # produces dist/function.zip (owned by language unit)
      - id: hash
        run: echo "zip_sha256=$(sha256sum dist/function.zip | cut -d' ' -f1)" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: orders-zip
          path: dist/function.zip
          retention-days: 30
  deploy-dev:
    needs: build
    uses: ./.github/workflows/_lambda-release.yml
    permissions: { contents: read, id-token: write }
    with: { environment: dev, zip_sha256: "${{ needs.build.outputs.zip_sha256 }}", canary_weight: "0" }
  deploy-stage:
    needs: [build, deploy-dev]
    uses: ./.github/workflows/_lambda-release.yml
    permissions: { contents: read, id-token: write }
    with: { environment: stage, zip_sha256: "${{ needs.build.outputs.zip_sha256 }}", canary_weight: "0.10" }
  deploy-prod:
    needs: [build, deploy-stage]
    uses: ./.github/workflows/_lambda-release.yml
    permissions: { contents: read, id-token: write }
    with: { environment: prod, zip_sha256: "${{ needs.build.outputs.zip_sha256 }}", canary_weight: "0.10" }
```

```yaml
# Representative — adapt to your environment
# .github/workflows/_lambda-release.yml
name: _lambda-release
on:
  workflow_call:
    inputs:
      environment: { type: string, required: true }
      zip_sha256: { type: string, required: true }
      canary_weight: { type: string, required: true }   # "0" = all at once
    outputs:
      version: { value: "${{ jobs.release.outputs.version }}" }
permissions:
  contents: read
jobs:
  release:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment:
      name: ${{ inputs.environment }}
      url: ${{ vars.APP_URL }}
    concurrency:
      group: deploy-orders-${{ inputs.environment }}
      cancel-in-progress: false
    permissions:
      contents: read
      id-token: write          # only this job logs in (family rule 7)
    outputs:
      version: ${{ steps.publish.outputs.version }}
    steps:
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with: { name: orders-zip, path: dist }
      - run: echo "${{ inputs.zip_sha256 }}  dist/function.zip" | sha256sum -c -
      - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
      - id: publish
        run: ./.github/actions/lambda/release.sh   # update code, wait, publish (deploying-aws-lambda)
      - name: Canary, smoke, complete or revert
        run: ./.github/actions/lambda/shift.sh "${{ steps.publish.outputs.version }}" "${{ inputs.canary_weight }}"
```

Step 4 (Free variant, C2): same build job; deploy jobs drop `environment:`, run only on
`workflow_dispatch` with `if: github.ref == 'refs/heads/main'`, and rely on the AWS trust pinned to
`ref:refs/heads/main`. Document "any writer can deploy" in the README.

Step 5: per-target release scripts follow A8 (Lambda), A9 (ECS), C5 (S3/CloudFront), A10 (Vercel),
C6 (Terraform components).

Smoke test and rollback triggers (per target):

| Target | Fraction mechanism | Smoke signal | Automatic rollback | Manual rollback |
|---|---|---|---|---|
| Lambda | alias `AdditionalVersionWeights` | invoke alias, check `x-amz-executed-version`; CloudWatch alarm on `ExecutedVersion` | CodeDeploy alarms (C4-B) or script reverts weights | `update-alias` to previous version |
| ECS | `CANARY` / `LINEAR` / `BLUE_GREEN` | lifecycle hook Lambda; ALB `HTTPCode_ELB_5XX_Count` (AWS-recommended) | alarms + circuit breaker rollback (ROLLING) | redeploy previous task definition revision |
| S3+CloudFront | staging distribution weight <= 15% or prefix switch | HTTP check on header-routed staging (`SingleHeader`) | none native (unverified) | origin path back to previous prefix |
| Vercel | staged production (`--skip-domain`) | curl the deployment URL before promote | none in CLI pages read (unverified) | `vercel rollback` (Hobby: previous only) |
| Terraform | small component per job | plan shows no unexpected destroy | none (unverified) | revert commit + reviewed plan |

## Quality Control

```bash
# Representative — adapt to your environment (offline checks on a generated repo)
# 1. Every deploy job has a timeout and a concurrency group
grep -nE "timeout-minutes:|concurrency:" .github/workflows/_*-release.yml
# Expected: one of each per deploying job
# 2. No cancel-in-progress true on deploy groups
grep -nE "cancel-in-progress:\s*true" .github/workflows/cd-*.yml .github/workflows/_*.yml
# Expected: no output (exit 1)
# 3. Actions pinned by SHA from the facts file
grep -nE "uses: [^.][^@]+@[0-9a-f]{40} # v" .github/workflows/*.yml | wc -l
# Expected: equals the number of third-party uses: lines
# 4. No rebuild in deploy workflows
grep -nE "docker build|mvn (package|verify)|vercel build" .github/workflows/_*-release.yml
# Expected: no output
# 5. Environment policies (live, read-only)
gh api repos/ORG/REPO/environments/prod --jq '.deployment_branch_policy'
# Expected: {"protected_branches":false,"custom_branch_policies":true}
gh api repos/ORG/REPO/environments/prod/deployment-branch-policies --jq '.branch_policies[].name'
# Expected: main
```

Testing approach: dry-run the reusable workflows on `dev` only; verify rollback by deliberately
failing the smoke step in `dev` and checking that the alias weights return to `{}`.

## Production Readiness

- Monitoring: alarms per target that the rollback logic reads (ECS recommended `HTTPCode_ELB_5XX_Count`, `HTTPCode_ELB_4XX_Count`, `CPUUtilization`, `MemoryUtilization`; Lambda `ExecutedVersion` dimension). ECS polls `DescribeAlarms`, which counts toward CloudWatch quotas; if throttled "the roll back might not occur". If an alarm is already in ALARM at deployment start, "Amazon ECS will not monitor alarms for the duration of that deployment".
- Error handling: a failed smoke step must run the revert step (`if: failure()`), then fail the job so later environments never run.
- Scaling: Lambda weights are probabilistic at low traffic; CloudFront may ignore the policy at service peak; ECS blue/green may "double your resource usage during deployments".
- Security: Pro/Team defaults A1-A3; Free variant residual risk documented (C2).
- Vercel: after `vercel rollback`, new pushes do not go live until `vercel promote` (instant-rollback page).

## Reference Implementations

- GitHub: environment + branch-policy REST examples (https://docs.github.com/en/rest/deployments/environments), rulesets REST (https://docs.github.com/en/rest/repos/rules).
- AWS: Lambda weighted alias CLI walkthrough and SAM `DeploymentPreference` example (https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html); ECS alarm rollback `create-service` example (https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-alarm-failure.html); CloudFront staging distribution CLI (https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/working-with-staging-distribution-continuous-deployment-policy.html).
- Vercel: staged production + prebuilt (https://vercel.com/docs/cli/deploying-from-cli).
- No community sources used.

## Research Gaps

| # | Gap | Tag | Follow-up path |
|---|---|---|---|
| G1 | Whether a workflow on a Free private repo that references `environment:` fails, is ignored, or auto-creates an environment | (unverified) | Test in a scratch Free private repo; docs pages read are silent |
| G2 | Whether a non-existent environment referenced in a workflow is auto-created (any plan) | (unverified) | workflow-syntax page read in 3 chunks; statement not found |
| G3 | Whether `deployment: false` jobs still honour deployment branch policies, and the OIDC `sub` they get | (unverified) | control-deployments silent; test |
| G4 | Whether ECS CloudWatch-alarm rollback applies to `BLUE_GREEN`/`LINEAR`/`CANARY` strategies | (unverified) | ECS canary/linear developer-guide pages rendered empty in the fetcher; re-read |
| G5 | Push rulesets on Pro private | (unverified) | gated reusable names Team only |
| G6 | Fine-grained token permission names for environments/rulesets/deployments REST (Administration write, Deployments write) | (unverified) | REST pages only list classic `repo`/`repo_deployment` scopes |
| G7 | `gh` and `aws` CLI preinstalled on `ubuntu-latest` | (medium confidence) | Read actions/runner-images Ubuntu README; requested as a fact |
| G8 | Combining `vercel deploy --prebuilt` with `--prod --skip-domain` in one command | (medium confidence) | Read https://vercel.com/docs/cli/deploy options |
| G9 | Automatic rollback mechanisms for CloudFront, Vercel (rolling releases page not read) and Terraform | (unverified) | Read vercel rolling-releases docs; none expected for CloudFront/Terraform |
| G10 | Introduction dates of `queue: max`, `deployment: false`, ECS native strategies | (unverified) | GitHub changelog / AWS What's New |
| G11 | Environment-scoped `vars`/secrets resolve in the called reusable workflow job, not the caller | (medium confidence) | Re-read reusing-workflow-configurations page (Composing unit owns it) |

## Research Iteration Changelog

| Iteration | Gap | Action | Result |
|---|---|---|---|
| 1 | Plan availability of protected branches/rulesets on private repos (boxes not rendered) | Fetched docs.github.com pages, then the `/api/article` endpoint | Not resolved |
| 2 | Same | WebSearch, then raw `github/docs` `data/reusables/gated-features/{protected-branches,repo-rules,environments}.md` | Resolved (official source repo) |
| 3 | ECS native canary/linear | developer-guide canary page empty; read API_DeploymentConfiguration | Resolved strategy values; alarm-per-strategy left as G4 |
| 4 | Environment auto-creation, `timeout-minutes` default | Read workflow-syntax at offsets 100000 and 200000 | Timeout resolved (360); auto-creation left as G2 |

## Completion Checklist

- [x] Metadata, Executive Summary, three guardrail tiers present
- [x] Every Forbidden Pattern has ❌/✅ example
- [x] Plan availability quoted from docs.github.com / github/docs for Free, Pro, Team private
- [x] Default approval designed without required reviewers; Free variant separate and marked weaker; required reviewers = upgrade path
- [x] Versions only from `_family_facts.md` (F3, F10, F23, F24); no doc-example majors used
- [x] PR jobs use `<env>-pr` read role (family rule 13)
- [x] Neighbour units referenced by name only
- [x] Pages read table and Source Bibliography at the end
- [ ] Gaps G1-G11 resolved (open, listed above)

## Agent Operation Notes

- High confidence: plan availability matrix rows quoted from docs; ruleset/env REST shapes; concurrency/timeout semantics; Lambda alias routing; ECS strategy values; CloudFront continuous deployment limits; Vercel promote/rollback behaviour.
- Medium confidence: never-cancel rationale; role-per-environment as blast-radius boundary (design inference); CloudFront staging distribution used to canary site content; `--prebuilt` + `--skip-domain` combination; environment values resolving across the reusable-workflow boundary; CLI availability on runners.
- Low / unverified: G1-G6, G9, G10.
- Ask First for the skill: C1 approval model, C3 solo maintainer, C4 CodeDeploy, C5 S3 strategy.

## Pages read

| URL | Read on | Official | Prompt-injection-like instructions found |
|---|---|---|---|
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax | 2026-10-30 (all 235839 chars, 3 chunks) | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows | 2026-10-30 (workflow_dispatch/push sections) | yes | no |
| https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets | 2026-10-30 (index only) | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches | 2026-10-30 (index only) | yes | no |
| https://docs.github.com/api/article?pathname=/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets | 2026-10-30 | yes | no |
| https://docs.github.com/api/article/meta?pathname=/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/protected-branches.md | 2026-10-30 | yes (GitHub docs source) | no |
| https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/repo-rules.md | 2026-10-30 | yes (GitHub docs source) | no |
| https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/environments.md | 2026-10-30 | yes (GitHub docs source) | no |
| https://raw.githubusercontent.com/github/docs/main/content/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets.md | 2026-10-30 | yes (GitHub docs source) | no |
| https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/repository-rules.md | 2026-10-30 (404) | yes | no |
| https://docs.github.com/en/get-started/learning-about-github/githubs-plans | 2026-10-30 | yes | no |
| https://docs.github.com/en/rest/deployments/deployments | 2026-10-30 | yes | no |
| https://docs.github.com/en/rest/deployments/statuses | 2026-10-30 | yes | no |
| https://docs.github.com/en/rest/deployments/environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/rest/deployments/branch-policies | 2026-10-30 | yes | no |
| https://docs.github.com/en/rest/repos/rules | 2026-10-30 (create-ruleset section) | yes | no |
| https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-types.html | 2026-10-30 (rendered empty, 0 chars of body) | yes | no |
| https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-blue-green.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-canary.html | 2026-10-30 (rendered empty, 0 chars of body) | yes | no |
| https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-alarm-failure.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentConfiguration.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/working-with-staging-distribution-continuous-deployment-policy.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html | 2026-10-30 | yes | no |
| https://vercel.com/docs/cli/promote | 2026-10-30 (last_updated 2026-07-15) | yes | no (page has a "For AI agents: follow these links" navigation note; informational, not an instruction to deviate) |
| https://vercel.com/docs/cli/rollback | 2026-10-30 (last_updated 2026-03-17) | yes | no (same navigation note) |
| https://vercel.com/docs/instant-rollback | 2026-10-30 (last_updated 2026-07-07) | yes | no (same navigation note) |
| https://vercel.com/docs/deployments/promoting-a-deployment | 2026-10-30 (last_updated 2026-06-26) | yes | no (same navigation note) |
| https://vercel.com/docs/cli/deploying-from-cli | 2026-10-30 (last_updated 2026-09-08) | yes | no (same navigation note) |
| https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects | 2026-10-30 | yes | no |
| https://developer.hashicorp.com/terraform/cloud-docs/workspaces/best-practices | 2026-10-30 (fetch failed: socket hang up, 0 chars) | yes | no |

## Source Bibliography

### Primary Sources (GitHub)
- [Deployments and environments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) - undated, read 2026-10-30
- [Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) - undated, read 2026-10-30
- [Control deployments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments) - undated, read 2026-10-30
- [Deployment environments (concepts)](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments) - undated, read 2026-10-30
- [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) - undated, read 2026-10-30
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) - undated, read 2026-10-30
- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) - undated, read 2026-10-30
- [Manually running a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) - undated, read 2026-10-30
- [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) - undated, read 2026-10-30
- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets) - undated, read 2026-10-30
- [Creating rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository) - undated, read 2026-10-30
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) - undated, read 2026-10-30
- [GitHub's plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans) - undated, read 2026-10-30
- [github/docs gated-features: protected-branches](https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/protected-branches.md) - main branch, read 2026-10-30
- [github/docs gated-features: repo-rules](https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/repo-rules.md) - main branch, read 2026-10-30
- [github/docs gated-features: environments](https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/environments.md) - main branch, read 2026-10-30
- [REST: deployments](https://docs.github.com/en/rest/deployments/deployments) - API version 2026-03-10, read 2026-10-30
- [REST: deployment statuses](https://docs.github.com/en/rest/deployments/statuses) - API version 2026-03-10, read 2026-10-30
- [REST: environments](https://docs.github.com/en/rest/deployments/environments) - API version 2026-03-10, read 2026-10-30
- [REST: deployment branch policies](https://docs.github.com/en/rest/deployments/branch-policies) - API version 2026-03-10, read 2026-10-30
- [REST: repository rules](https://docs.github.com/en/rest/repos/rules) - API version 2026-03-10, read 2026-10-30

### Primary Sources (AWS)
- [Lambda weighted alias](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html) - undated, read 2026-10-30
- [Lambda versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html) - undated, read 2026-10-30
- [CodeDeploy deployment configurations](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html) - undated, read 2026-10-30
- [CodeDeploy redeploy and roll back](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html) - undated, read 2026-10-30
- [ECS blue/green deployments](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-blue-green.html) - undated, read 2026-10-30
- [ECS CloudWatch alarm deployment failure](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-alarm-failure.html) - undated, read 2026-10-30
- [ECS API DeploymentConfiguration](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentConfiguration.html) - undated, read 2026-10-30
- [ECR image tag mutability](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html) - undated, read 2026-10-30
- [CloudFront continuous deployment](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html) - undated, read 2026-10-30
- [CloudFront continuous deployment quotas](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html) - undated, read 2026-10-30
- [CloudFront staging distribution and policy](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/working-with-staging-distribution-continuous-deployment-policy.html) - undated, read 2026-10-30
- [CloudFront origin settings](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html) - undated, read 2026-10-30

### Primary Sources (Vercel, HashiCorp)
- [vercel promote](https://vercel.com/docs/cli/promote) - last_updated 2026-07-15, read 2026-10-30
- [vercel rollback](https://vercel.com/docs/cli/rollback) - last_updated 2026-03-17, read 2026-10-30
- [Instant Rollback](https://vercel.com/docs/instant-rollback) - last_updated 2026-07-07, read 2026-10-30
- [Promoting deployments](https://vercel.com/docs/deployments/promoting-a-deployment) - last_updated 2026-06-26, read 2026-10-30
- [Deploying from CLI](https://vercel.com/docs/cli/deploying-from-cli) - last_updated 2026-09-08, read 2026-10-30
- [HashiCorp WAF: workspace and project best practices](https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects) - undated, read 2026-10-30

### Family inputs
- `workspace/github-actions-cicd/_family_facts.md` F3, F10, F23, F24 (action SHAs); `_family_rules.md` 1-16
