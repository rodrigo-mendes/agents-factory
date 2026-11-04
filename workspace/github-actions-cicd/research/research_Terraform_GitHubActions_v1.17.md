# Research: Terraform CLI 1.17 driven from GitHub Actions (AWS and OCI)

> Unit: `automating-terraform-github-actions-v1-17`. Source item: "CI on PR and CD on merge for
> Terraform infra deploying to AWS and OCI". Spec: `researching-technical-frameworks` (default
> depth = exhaustive, MAX_ITERATIONS = 5). Brief: `workspace/github-actions-cicd/execution-1/briefs/P3-research-terraform.md`.
> Every page was read on 2026-10-30. Family facts (F1-F22) and family rules (1-12) from
> `workspace/github-actions-cicd/_family_facts.md` / `_family_rules.md` are applied as given.
>
> Section-order note: the brief requires the file to END with `## Source Bibliography`, so that
> section is moved from its template position to the end. All 15 template sections are present.

## Metadata

```yaml
Full_Name: HashiCorp Terraform CLI, run from GitHub Actions (GitHub.com) against AWS and OCI
Target_Version: Terraform 1.17 (pin 1.17.1, family fact F1)
Release_Date: 1.17.0 on 2026-10-21; 1.17.1 on 2026-10-28 (F1; v1.17 CHANGELOG)
Support_Status: Active, current stable minor line (docs label "v1.17.x (latest)")
Primary_Docs: https://developer.hashicorp.com/terraform (v1.17.x pages)
Official_Repo: https://github.com/hashicorp/terraform
Setup_Action: hashicorp/setup-terraform v4.0.1 = dfe3c3f87815947d99a8997f908cb6525fc44e9e (F2)
Integration_Partners: GitHub Actions (environments, concurrency, artifacts), AWS S3 backend, OCI Object Storage (oci backend)
Research_Date: 2026-10-30
Domain_Complexity: Complex
Research_Depth: exhaustive (default)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 2 of 5
Triangulated_Count: 6
Unverified_Count: 9
Irresolvable_Count: 0
Research_Quality_Score: 87%   # ~70 claims, 9 unverified
```

## Executive Summary

Terraform 1.17 is a minor release in the stable 1.x series that "honors the Terraform v1.0
Compatibility Promises"; its upgrade guide lists no breaking changes, and the v1.17 CHANGELOG has
no BREAKING CHANGES or deprecation entries (https://developer.hashicorp.com/terraform/language/upgrade-guides,
https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md, both read 2026-10-30). New in 1.17.0:
variables and locals in provider requirements, a `-minimal-refresh` plan option, and Terraform
Policy (`-policies`) out of experimental. 1.17.1 (2026-10-28) is bug fixes only. For CI/CD the
facts that matter were set earlier and still hold in 1.17: the S3 backend locks with
`use_lockfile = true`, and DynamoDB locking "is deprecated" and "will be removed in a future minor
version". The native `oci` backend (Terraform v1.12.0 or later, per Oracle) stores state in OCI
Object Storage and locks through the `If-None-Match: *` header. Oracle now calls the
S3-compatible route "deprecated".

The pipeline shape this research supports: a pull-request workflow that runs `fmt -check`,
`validate`, plan-mode `terraform test`, and `plan -out`, then shows the plan on the PR. This
workflow never writes to the cloud (family rule 7). A merge workflow makes a fresh saved plan from
the merge commit, uploads it as a short-lived artifact, and applies exactly that file in a job
that references a GitHub environment with required reviewers. A concurrency group per
environment and component runs one at a time. A scheduled `ops-` workflow detects drift with
`plan -detailed-exitcode` (exit code 2 = changes), opens an issue, and never applies.

The three critical patterns are: (1) apply only a saved plan file, and treat it as a secret,
because "it will be saved in cleartext in the plan file"; (2) one state per environment and
component, locked with `use_lockfile` (S3) or the `oci` backend's built-in lock; (3) serialize
plan and apply per environment with `concurrency`, and gate the apply with environment reviewers.
Tier = Complex: it involves credentials, sensitive plan artifacts, two clouds, state locking, and
human approval gates.

## Architectural Guardrails

> Confidence legend: High = official page read in full, 2+ official sources where marked
> Triangulated | (medium confidence) = one source, partly read, or inferred | (unverified) = no
> official confirmation found.

### ✅ Mandatory Patterns

**A1. Apply only a saved plan file produced by `plan -out` in the same workflow run**
> Confidence: High | [✓✓ Triangulated | plan command page (2026-10-30) + apply command page (2026-10-30) + automate-terraform tutorial (2026-10-30)]
- Why: in saved plan mode "Terraform performs the operations in the saved plan without prompting you for confirmation", and "Terraform interprets the act of passing the plan file as the approval". The human approval is the GitHub environment review, not `-auto-approve`.
- Code:
  ```bash
  # Terraform 1.17.1
  terraform plan  -input=false -out=tfplan
  terraform apply -input=false tfplan
  ```
- Source: https://developer.hashicorp.com/terraform/cli/commands/apply (2026-10-30); https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform (2026-10-30)

**A2. Treat the plan file (and any artifact containing it) as sensitive**
> Confidence: High | [✓✓ Triangulated | plan command page + automate-terraform tutorial]
- Why: "If your plan includes any sort of sensitive data, even if obscured in Terraform's terminal output, it will be saved in cleartext in the plan file. You should therefore treat any saved plan files as potentially-sensitive artifacts." The tutorial adds: "The plan file contains a full copy of the configuration, the state that the plan applies to". Anyone with repository read access can download workflow artifacts ("Read access to the repository is required").
- Code:
  ```yaml
  - uses: actions/upload-artifact@<SHA-not-in-family-facts>  # see Research Gaps G1
    with:
      name: tfplan-${{ inputs.environment }}-${{ inputs.component }}-${{ github.sha }}
      path: ${{ inputs.working-directory }}/tfplan
      retention-days: 1
  ```
- Source: https://developer.hashicorp.com/terraform/cli/commands/plan (2026-10-30); https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts (2026-10-30)

**A3. Disable prompts and adapt output for automation (`-input=false`, `TF_IN_AUTOMATION`)**
> Confidence: High | [✓✓ Triangulated | plan command page + environment-variables page + automate-terraform tutorial]
- Why: `-input=false` "is particularly useful when running Terraform in non-interactive automation systems". `TF_INPUT=false` acts as if `-input=false` were passed. With `TF_IN_AUTOMATION` set, "Terraform adjusts its output to avoid suggesting specific commands to run next."
- Code:
  ```yaml
  env:
    TF_IN_AUTOMATION: "true"
    TF_INPUT: "false"
  ```
- Source: https://developer.hashicorp.com/terraform/cli/config/environment-variables (2026-10-30)

**A4. Pin the Terraform CLI version in `hashicorp/setup-terraform`**
> Confidence: High (single source: setup-terraform README, plus F1/F2)
- Why: if `terraform_version` is not set, the action "will default to `latest`". Family rule 11 requires the facts-file version (1.17.1, F1). The README also allows constraint strings. Use an exact version for reproducible plans.
- Code:
  ```yaml
  - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
    with:
      terraform_version: "1.17.1"
      terraform_wrapper: false
  ```
- Source: https://github.com/hashicorp/setup-terraform (2026-10-30)

**A5. Read `-detailed-exitcode` explicitly: 0 = no changes, 1 = error, 2 = changes present**
> Confidence: High (plan command page)
- Why: the plan page says: "0 = Succeeded with empty diff (no changes)", "1 = Error", "2 = Succeeded with non-empty diff (changes present)". GitHub's default Linux shell is `bash -e {0}` (or `bash --noprofile --norc -eo pipefail {0}` with `shell: bash`), so a bare exit code 2 fails the step. Capture it with `set +e`.
- Code:
  ```bash
  set +e
  terraform plan -input=false -detailed-exitcode -out=tfplan
  rc=$?
  set -e
  echo "exitcode=$rc" >> "$GITHUB_OUTPUT"
  [ "$rc" -eq 1 ] && exit 1 || exit 0
  ```
- Source: https://developer.hashicorp.com/terraform/cli/commands/plan (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30, partly read: characters 0-100000 of 235839)

**A6. S3 backend: lock with `use_lockfile = true`, enable bucket versioning, one key per environment and component**
> Confidence: High | [✓✓ Triangulated | S3 backend page (2026-10-30) + AWS S3 conditional writes page (2026-10-30)]
- Why: "This backend also supports state locking which can be enabled by setting the `use_lockfile` argument to `true`." `use_lockfile` "Defaults to `false`", so locking is off unless you set it. "DynamoDB-based locking is deprecated" and "will be removed in a future minor version". "It is highly recommended that you enable Bucket Versioning on the S3 bucket to allow for state recovery." The lock file needs `s3:GetObject`, `s3:PutObject` and `s3:DeleteObject`. On the AWS side, S3 `If-None-Match` conditional writes make "the first write operation to finish" succeed and fail later ones with `412 Precondition Failed`. (That this is how `use_lockfile` works internally is inferred, (medium confidence).)
- Code:
  ```hcl
  # Terraform 1.17 — backend.tf (partial config; bucket/key/region come from -backend-config)
  terraform {
    backend "s3" {
      use_lockfile = true
      encrypt      = true
    }
  }
  ```
  ```bash
  terraform init -input=false \
    -backend-config="bucket=acme-tfstate-prod" \
    -backend-config="key=network/prod/terraform.tfstate" \
    -backend-config="region=eu-west-1"
  ```
- Source: https://developer.hashicorp.com/terraform/language/backend/s3 (2026-10-30); https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html (2026-10-30)

**A7. OCI state: use the native `oci` backend (locking built in, bucket versioning on)**
> Confidence: High | [✓✓ Triangulated | HashiCorp oci backend page (2026-10-30) + Oracle "Using Object Storage for State Files" (2026-10-30)]
- Why: "The oci backend stores the Terraform state file in Oracle Cloud Infrastructure (OCI) Object Storage" and "supports state locking by leveraging the `If-None-Match: *` header capability of OCI Object Storage". Oracle: "we recommend using … the OCI native backend", which needs "Terraform … version v1.12.0 or greater". The S3-compatible method "is deprecated". HashiCorp: "It is highly recommended that you enable Bucket Versioning on the object storage bucket".
- Code:
  ```hcl
  # Terraform 1.17 — OCI component backend (non-default workspaces use prefix tf-state-env)
  terraform {
    backend "oci" {
      bucket    = "acme-tfstate-prod"
      namespace = "acmetenancyns"
      region    = "eu-frankfurt-1"
      key       = "functions/prod/terraform.tfstate"
      auth      = "APIKey"
    }
  }
  ```
- Source: https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm (2026-10-30)

**A8. Gate the apply job with a GitHub environment that has required reviewers**
> Confidence: High (deployments-and-environments reference + control-deployments how-to)
- Why: "When a workflow job references an environment, the job won't start until all of the environment's protection rules pass." Required reviewers: "up to six users or teams", "Only one of the required reviewers needs to approve", and "users who initiate a deployment cannot approve the deployment job" (when prevent self-review is on). With required approval, "a job cannot access environment secrets until one of the required reviewers approves it". Plan limits: on GitHub Free, Pro or Team, required reviewers only work in public repositories.
- Code:
  ```yaml
  apply:
    needs: plan
    runs-on: ubuntu-latest
    environment: prod
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30); https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments (2026-10-30)

**A9. Serialize plan+apply per environment and component with a workflow-level `concurrency` group, `cancel-in-progress: false`**
> Confidence: High for the GitHub semantics (two official pages); workflow-level (not job-level) placement is a design inference (medium confidence)
- Why: "there can be at most one running job or workflow in a concurrency group at any time". Running work is cancelled only with `cancel-in-progress: true`, and an apply must never be cancelled mid-flight. Default `queue: single` cancels an older pending run when a newer one queues. On a linear `main` the newer run includes the older commits, so that is acceptable. `queue: max` keeps up to 100 pending, but "The combination of `queue: max` and `cancel-in-progress: true` is not allowed". Workflow-level placement keeps a later run's plan from slipping in between this run's plan and apply. Otherwise that later plan would go stale (see U1).
- Code:
  ```yaml
  concurrency:
    group: terraform-${{ inputs.environment }}-${{ inputs.component }}
    cancel-in-progress: false
  ```
- Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (2026-10-30); https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments (2026-10-30)

**A10. Commit `.terraform.lock.hcl` and pre-populate hashes for the runner platform**
> Confidence: High (dependency lock file page)
- Why: "You should include this file in your version control repository". Run `terraform providers lock -platform=linux_amd64` (plus developer platforms) so that CI does not learn new `h1:` hashes later. Terraform "will always re-select that version" recorded in the lock file. That keeps the providers on the plan and apply runners identical, which the tutorial requires: "Terraform expects the provider plugins that were used to produce a plan to be available and identical".
- Code:
  ```bash
  terraform providers lock -platform=linux_amd64 -platform=darwin_arm64 -platform=windows_amd64
  ```
- Source: https://developer.hashicorp.com/terraform/language/files/dependency-lock (2026-10-30)

**A11. Drift detection is a scheduled plan that opens an issue and never applies**
> Confidence: High for each building block (plan page, events page, GITHUB_TOKEN page); the composition is a design pattern (medium confidence)
- Why: `-refresh-only` "creates a plan whose goal is only to update the Terraform state … to match changes made to remote objects outside of Terraform". Exit code 2 signals a non-empty diff. "Scheduled workflows run on the latest commit on the default branch". The shortest interval is 5 minutes, runs "can be delayed during periods of high loads", and in public repositories schedules are "automatically disabled when no repository activity has occurred in 60 days". Open the issue with `gh issue create` and `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` under `permissions: issues: write`.
- Source: https://developer.hashicorp.com/terraform/cli/commands/plan; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows; https://docs.github.com/en/actions/tutorials/authenticate-with-github_token (all 2026-10-30)

### ⚠️ Conditional Patterns

**C1. Which plan gets applied: fresh saved plan on the merge commit vs. the PR's plan artifact**
> Confidence: High for the constraints; recommendation (medium confidence)
- Options: (A) the merge workflow plans on the merge commit and applies that artifact in the same run (recommended). (B) Apply the artifact produced by the PR workflow. (C) Plan and apply in a single job after approval, with no artifact.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | "same commit" guarantee: plan reviewed in the env gate = plan applied; same runner image | reviewers see a second plan (the PR plan is only a preview) | default for this family |
  | B | reviewers approve exactly what they saw on the PR | the merge commit differs from the PR head; cross-run download needs `github-token` + `run-id`; the plan may be stale | never by default; only with merge queues that test the exact merge result (unverified) |
  | C | no artifact, so no plan file at rest | the plan is computed after approval, so the approver did not see it | non-critical stacks only |

- Constraints that drive this: plan and apply on different machines need the working directory "extract[ed] … at the same absolute path", the same OS/CPU, and "identical" plugins (automate-terraform tutorial). Cross-run downloads need a `github-token` ("required when downloading artifacts from a different repository or from a different workflow run", actions/download-artifact README).
- Agent: "Ask the user whether reviewers must approve the PR plan itself (B) or whether a fresh plan on the merge commit, reviewed in the environment gate (A), is acceptable."
- Source: https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform (2026-10-30); https://github.com/actions/download-artifact (2026-10-30)

**C2. What crosses from the plan job to the apply job**
> Confidence: (medium confidence)
- Options: (A) archive the whole working directory including `.terraform` (the official guidance: "archive the entire working directory, including the `.terraform` subdirectory"). (B) Upload only `tfplan` and re-run `terraform init` on the apply runner with the committed lock file.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | exactly what HashiCorp documents | large artifact; `.terraform` may hold `-backend-config` values ("Terraform will include these values in both the `.terraform` subdirectory and in plan files") | default |
  | B | small artifact, no provider binaries at rest | relies on the lock file + same runner label for identical plugins and paths; not documented as equivalent (unverified) | teams that accept the documented-path deviation |

- Agent: "Ask whether the artifact may contain provider binaries and backend config; default to A on a pinned `runs-on` label."
- Source: https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform; https://developer.hashicorp.com/terraform/language/backend/s3 (2026-10-30)

**C3. How the PR plan reads state without writing to the cloud (family rule 7)**
> Confidence: (medium confidence)
- Options: (A) read-only cloud role + `-lock=false` on the PR plan. (B) A role that may write only the lock object. (C) No cloud plan on PRs; run only `fmt`/`validate`/mocked `test`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | no cloud write at all | `-lock=false` "is dangerous if others might concurrently run commands against the same workspace"; a PR plan can read a state mid-apply | rule 7 strict; the PR plan is advisory only |
  | B | consistent reads | writes the lock object (`s3:PutObject`/`DeleteObject` on the `.tflock`), which strictly violates rule 7 | rule-7 exception approved by the user |
  | C | zero cloud access on PRs | no plan preview on the PR | fork-heavy or public repos |

- Note: PRs from forks get no secrets ("secrets are not passed to the runner when a workflow is triggered from a forked repository"), so A/B only work for same-repo branches.
- Agent: "Ask which option; default to A and label the PR plan comment 'preview, not the applied plan'."
- Source: https://developer.hashicorp.com/terraform/cli/commands/plan; https://developer.hashicorp.com/terraform/language/backend/s3; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-10-30)

**C4. How the plan is rendered on the PR**
> Confidence: High (setup-terraform README + workflow commands page)
- Options: (A) PR comment (`gh pr comment --body-file`, needs `pull-requests: write`). (B) Job summary via `$GITHUB_STEP_SUMMARY`. (C) Both, with the comment truncated and pointing to the summary.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | visible in the PR conversation | "a limit to the number of characters inside a GitHub comment (65535)", and an oversize comment can fail the run | small stacks |
  | B | 1 MiB per step; "Summaries automatically mask any secrets" | less visible | large plans |
  | C | both | more code | default |

- Agent: "Ask whether a PR comment is wanted; always write the summary."
- Source: https://github.com/hashicorp/setup-terraform; https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands (2026-10-30)

**C5. `terraform test` scope inside the PR workflow**
> Confidence: High (tests language page + test command page)
- Options: (A) only `command = plan` run blocks and mocks on PRs; apply-mode tests in a separate, manually dispatched workflow against a sandbox account. (B) No tests on PRs.
- Why it is conditional: "By default, each `run` block executes with `command = apply`", and "The Terraform `terraform test` command creates _real_ infrastructure". On a PR that conflicts with rule 7. Mocking exists since Terraform v1.7.0, and 1.17 adds ephemeral-resource support to `mock_provider` (CHANGELOG).
- Agent: "Ask which test files are plan/mock-only; run only those via `-filter` on PRs."
- Source: https://developer.hashicorp.com/terraform/language/tests; https://developer.hashicorp.com/terraform/cli/commands/test (2026-10-30)

**C6. Drift signal: `-refresh-only` vs. normal plan**
> Confidence: High (plan page)
- Options: (A) `plan -refresh-only -detailed-exitcode`: detects only changes made outside Terraform. (B) `plan -detailed-exitcode`: also flags merged-but-unapplied config. (C) Both, reported separately.
- Never use `-minimal-refresh` (new in 1.17) or `-refresh=false` for drift: "this option causes Terraform to ignore external changes to resources that have no planned changes".
- Agent: "Ask whether unapplied config should count as drift; default C."
- Source: https://developer.hashicorp.com/terraform/cli/commands/plan (2026-10-30)

**C7. OCI backend authentication in CI**
> Confidence: (medium confidence)
- Options: `auth = "APIKey"` with key material from environment secrets (family rule 9 default), or `SecurityToken` (token-exchange path, F20/F21, medium confidence). The page also lists `InstancePrincipal`, `ResourcePrincipal`, `InstancePrincipalWithCerts`, `OKEWorkloadIdentity`, which do not apply to GitHub-hosted runners (unverified for self-hosted OCI runners).
- HashiCorp: "We strongly recommend using environment variables to supply credentials". Variables use the `OCI_` prefix first, then no prefix. "Required attributes like `bucket` and `namespace` cannot be configured through environment variables". The full list of env var names for API-key material is not on the page (unverified). Login mechanics belong to `federating-github-actions-oci`.
- Source: https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30)

### 🚫 Forbidden Patterns

**N1. `terraform apply -auto-approve` (re-plan at apply time) in the merge workflow**
> Severity: Critical
> Confidence: High
- Why: the approver approves something that is never shown. HashiCorp: "Use automatic approval only with non-critical infrastructure."
- Impact: changes that nobody reviewed reach prod. A commit that lands between review and apply is applied silently.
- ❌ Wrong:
  ```yaml
  - run: terraform apply -auto-approve -input=false
  ```
- ✅ Correct:
  ```yaml
  - run: terraform apply -input=false tfplan   # tfplan from the plan job of this run
  ```
- Source: https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform; https://developer.hashicorp.com/terraform/cli/commands/apply (2026-10-30)

**N2. Long-lived or broadly shared plan artifacts**
> Severity: High
> Confidence: High
- Why: plan files hold sensitive values in cleartext. Artifacts default to 90 days, and anyone with read access can download them.
- Impact: secrets and state leak to every reader of the repo for months.
- ❌ Wrong:
  ```yaml
  - uses: actions/upload-artifact@<SHA-not-in-family-facts>
    with: { name: plan, path: tfplan }        # default 90-day retention
  ```
- ✅ Correct:
  ```yaml
  - uses: actions/upload-artifact@<SHA-not-in-family-facts>
    with:
      name: tfplan-${{ inputs.environment }}-${{ inputs.component }}-${{ github.sha }}
      path: ${{ inputs.working-directory }}/tfplan
      retention-days: 1
  ```
- Source: https://developer.hashicorp.com/terraform/cli/commands/plan; https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository (2026-10-30)

**N3. DynamoDB-only locking (or no locking) on the S3 backend**
> Severity: High
> Confidence: High
- Why: "DynamoDB-based locking is deprecated" and "will be removed in a future minor version". `use_lockfile` defaults to `false`.
- Impact: a later 1.x minor release removes DynamoDB locking, and a missing lock lets concurrent applies corrupt state.
- ❌ Wrong:
  ```hcl
  backend "s3" { dynamodb_table = "tf-locks" }
  ```
- ✅ Correct:
  ```hcl
  backend "s3" { use_lockfile = true }   # during migration both may be set simultaneously
  ```
- Source: https://developer.hashicorp.com/terraform/language/backend/s3 (2026-10-30)

**N4. New OCI stacks on the S3-compatible endpoint with Customer Secret Keys**
> Severity: Medium
> Confidence: High
- Why: Oracle: "The S3-compatible backend method is deprecated. Only use this method if you're not able to upgrade to Terraform version v1.12.0 or greater." HashiCorp "only tests the `s3` backend against Amazon S3".
- Impact: you depend on a deprecated, untested path, and locking on it is unverified.
- ❌ Wrong:
  ```hcl
  backend "s3" {
    endpoints      = { s3 = "https://<namespace>.compat.objectstorage.<region>.oraclecloud.com" }
    use_path_style = true
  }
  ```
- ✅ Correct:
  ```hcl
  backend "oci" { bucket = "acme-tfstate-prod"  namespace = "acmetenancyns"  region = "eu-frankfurt-1"  key = "app/prod/terraform.tfstate" }
  ```
- Source: https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm; https://developer.hashicorp.com/terraform/language/backend/s3 (2026-10-30)

**N5. Secrets in `-backend-config` or in the backend block**
> Severity: High
> Confidence: High
- Why: values passed by `-backend-config` or hardcoded land "in both the `.terraform` subdirectory and in plan files" (S3). OCI: "Sensitive values passed this way may be saved in" `.terraform` and `*.tfplan`. Both pages recommend environment variables.
- Impact: credentials end up inside the plan artifact (N2).
- ❌ Wrong:
  ```bash
  terraform init -backend-config="secret_key=${{ secrets.S3_SECRET }}"
  ```
- ✅ Correct:
  ```bash
  # non-secret values only; credentials come from the login step's environment
  terraform init -input=false -backend-config="key=network/prod/terraform.tfstate"
  ```
- Source: https://developer.hashicorp.com/terraform/language/backend/s3; https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30)

**N6. Applying (or running apply-mode tests) from a pull-request workflow**
> Severity: Critical
> Confidence: High
- Why: family rule 7. `terraform test` "creates _real_ infrastructure" by default.
- Impact: unreviewed branches change shared cloud accounts.
- ❌ Wrong:
  ```yaml
  on: pull_request
  jobs: { t: { steps: [ { run: terraform test } ] } }   # run blocks default to command = apply
  ```
- ✅ Correct:
  ```yaml
  on: pull_request
  # only plan/mock test files
  - run: terraform test -filter=tests/plan_only.tftest.hcl
  ```
- Source: https://developer.hashicorp.com/terraform/cli/commands/test; https://developer.hashicorp.com/terraform/language/tests (2026-10-30)

**N7. Applying from the drift-detection workflow**
> Severity: Critical
> Confidence: High (brief scope + family rule 7 spirit; `-refresh-only` semantics from the plan page)
- Why: drift may be an intentional emergency change. The fix goes through a PR.
- Impact: the scheduled job silently reverts manual hotfixes.
- ❌ Wrong:
  ```yaml
  on: { schedule: [ { cron: "0 6 * * *" } ] }
  # ... terraform apply -auto-approve -refresh-only
  ```
- ✅ Correct:
  ```yaml
  # exit code 2 -> gh issue create; no apply step exists in ops-terraform-drift.yml
  ```
- Source: https://developer.hashicorp.com/terraform/cli/commands/plan (2026-10-30)

**N8. `cancel-in-progress: true` on an apply concurrency group**
> Severity: High
> Confidence: High (GitHub semantics); cancelling an apply mid-run leaves a partly applied state (medium confidence)
- Why: `cancel-in-progress: true` cancels "any currently running job or workflow in the same concurrency group".
- Impact: an apply is interrupted, the state lock is left behind, and resources end up half-created.
- ❌ Wrong:
  ```yaml
  concurrency: { group: terraform-prod-network, cancel-in-progress: true }
  ```
- ✅ Correct:
  ```yaml
  concurrency: { group: terraform-prod-network, cancel-in-progress: false }
  ```
- Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (2026-10-30)

**N9. Sharing one plugin cache directory across concurrent `terraform init` runs**
> Severity: Medium
> Confidence: High
- Why: "The plugin cache directory is not guaranteed to be concurrency safe." "The provider installer's behavior in environments with multiple `terraform init` calls is undefined." Also, never set `plugin_cache_may_break_dependency_lock_file`: "Do not set this option unless you are sure you need it".
- Impact: corrupted provider installs, non-reproducible plans.
- ❌ Wrong:
  ```yaml
  strategy: { matrix: { component: [network, app, data] } }
  env: { TF_PLUGIN_CACHE_DIR: /shared/self-hosted/cache }   # one dir, parallel inits
  ```
- ✅ Correct:
  ```yaml
  env: { TF_PLUGIN_CACHE_DIR: "${{ runner.temp }}/tf-plugin-cache" }  # per job; mkdir -p first
  ```
- Source: https://developer.hashicorp.com/terraform/cli/config/config-file (2026-10-30)

## Migration Guide

> Confidence: High | Sources: upgrade guide v1.17 (2026-10-30) + v1.17 CHANGELOG (2026-10-30)

**Breaking Changes**: none. "Terraform v1.17 is a minor release in the stable Terraform v1.0
series" and "honors the Terraform v1.0 Compatibility Promises". The CHANGELOG for 1.17.0/1.17.1 has
no BREAKING CHANGES or UPGRADE NOTES entries.

**New in 1.17.0 (2026-10-21)** relevant to pipelines:
- `-minimal-refresh` plan option, which refreshes only resources with proposed changes. Not for drift detection (C6).
- Terraform Policy GA: "The `-policies` flag for `plan`, `apply`, and `query` no longer requires an experimental build". The policy model is out of this unit's scope (unverified detail).
- Variables and locals usable in provider requirements.
- `test`: `mock_provider` supports ephemeral resources.
- `version -json` adds `format_version`. Tooling that parses it should tolerate the field.
- Built with Go 1.26.10. It no longer trusts certificates from the compromised eMudhra intermediate CAs.
- Experiments (alpha builds only, do not use in CI): `-allow-deferral`, `terraform test cleanup`, `backend` blocks in test run blocks.

**1.17.1 (2026-10-28)**: bug fixes (`fmt` preserves the file on write error; module policies evaluated during destroy plans).

**Carried-forward deprecations that a 1.17 pipeline must already respect** (stated on 1.17.x pages):
- S3 `dynamodb_table` is "(Optional, **Deprecated**)" and will be removed in a future minor version. Migrate to `use_lockfile`.
- S3 `endpoint` is deprecated: "Use `endpoints.s3` instead". `force_path_style` is replaced by `use_path_style`.
- OCI S3-compatible state is deprecated in favour of the `oci` backend (Terraform v1.12.0 or later).

⚠️ Migration Note: Always-Do A6 references the `dynamodb_table` → `use_lockfile` change.

**Upgrade Steps** (representative — adapt to your environment):
1. Bump `terraform_version: "1.17.1"` in every `setup-terraform` step (F1).
2. S3: add `use_lockfile = true` alongside `dynamodb_table` and run `terraform init -reconfigure` per component. After one clean cycle, remove `dynamodb_table`. (The page states "the S3 and DynamoDB arguments can be configured simultaneously". Whether `-reconfigure` or `-migrate-state` is needed for a lock-only change is (unverified).)
3. OCI on S3-compat: change the backend block to `oci` and run `terraform init -migrate-state` (the exact migration procedure between these two backends is not on the pages read, (unverified)).
4. Refresh lock hashes: `terraform providers lock -platform=linux_amd64 …` and commit.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Terraform CLI | 1.17.0 | 1.17.x | pin 1.17.1 (F1) |
| `terraform test` | v1.6.0 | — | mocking since v1.7.0 |
| `oci` backend | v1.12.0 | — | per Oracle page |
| `-refresh-only` | v0.15.4 | — | plan page |
| hashicorp/setup-terraform | v4.0.1 | — | SHA in F2 |
| actions/checkout | v7.0.1 | — | SHA in F10 |
| aws-actions/configure-aws-credentials | v6.3.0 | — | SHA in F3 (login only; see federating-github-actions-aws-oidc) |
| actions/upload-artifact / download-artifact | (unverified) | — | no SHA in family facts; README examples show `download-artifact@v8` |

## Implementation Blueprint

> Confidence: High for each command/key (sources inline); file names follow family rule 5;
> reusable-workflow mechanics belong to `composing-github-actions-pipelines`; SHA-pinning guidance
> lives in `automating-github-repos-with-actions`.

**Repository layout** (state per environment and per component):

```text
infra/
  network/   backend.tf  main.tf  .terraform.lock.hcl  tests/plan_only.tftest.hcl
  app/       ...
  env/prod/network.s3.tfbackend      # non-secret: bucket, key=network/prod/terraform.tfstate, region
  env/prod/app-oci.tfbackend         # oci backend: bucket, namespace, region, key
.github/workflows/
  ci-infra.yml                 # pull_request
  cd-infra.yml                 # push to main
  ops-terraform-drift.yml      # schedule
  _terraform-plan-apply.yml    # reusable (workflow_call)
```

**Lifecycle — PR workflow (`ci-infra.yml`, Terraform 1.17.1)**:

```yaml
name: ci-infra
on:
  pull_request:
    paths: ["infra/**"]
permissions:
  contents: read
jobs:
  plan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write      # PR comment
      id-token: write           # only if this job logs in (rule 7); omit for option C3-C
    env:
      TF_IN_AUTOMATION: "true"
      TF_INPUT: "false"
    defaults:
      run:
        working-directory: infra/network
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with:
          terraform_version: "1.17.1"
          terraform_wrapper: false
      - run: terraform fmt -check -recursive
      - run: terraform init -input=false -backend-config=../env/prod/network.s3.tfbackend
      - run: terraform validate
      - run: terraform test -filter=tests/plan_only.tftest.hcl
      # read-only cloud login step here (federating-github-actions-aws-oidc / -oci)
      - id: plan
        run: |
          set +e
          terraform plan -input=false -lock=false -detailed-exitcode -out=tfplan
          rc=$?
          set -e
          echo "exitcode=$rc" >> "$GITHUB_OUTPUT"
          [ "$rc" -eq 1 ] && exit 1
          terraform show -no-color tfplan > plan.txt
          { echo '### Terraform plan (preview, not the applied plan)'; echo '```'; head -c 60000 plan.txt; echo '```'; } > comment.md
          cat comment.md >> "$GITHUB_STEP_SUMMARY"
      - if: steps.plan.outputs.exitcode == '2'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: gh pr comment "${{ github.event.pull_request.number }}" --body-file comment.md
```

Notes: `-lock=false` is option C3-A, (medium confidence). The PR plan file is not uploaded,
because it is never applied (C1-A). `terraform show -no-color` renders a plan file
("You may use `show` with a path to either a Terraform state file or plan file"). Do not use
`show -json` in comments: "any sensitive values in Terraform state will be displayed in plain text".

**Lifecycle — merge workflow (`cd-infra.yml` → reusable `_terraform-plan-apply.yml`)**:

```yaml
# _terraform-plan-apply.yml (reusable; typed inputs, explicit outputs, per rule 6)
on:
  workflow_call:
    inputs:
      environment:       { type: string, required: true }
      component:         { type: string, required: true }
      working-directory: { type: string, required: true }
      backend-config:    { type: string, required: true }
    outputs:
      plan-exitcode:
        value: ${{ jobs.plan.outputs.exitcode }}
permissions:
  contents: read
concurrency:
  group: terraform-${{ inputs.environment }}-${{ inputs.component }}
  cancel-in-progress: false
env:
  TF_IN_AUTOMATION: "true"
  TF_INPUT: "false"
jobs:
  plan:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}-plan   # env secrets for read; no reviewers
    permissions: { contents: read, id-token: write }
    outputs:
      exitcode: ${{ steps.plan.outputs.exitcode }}
    defaults: { run: { working-directory: "${{ inputs.working-directory }}" } }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with: { terraform_version: "1.17.1", terraform_wrapper: false }
      # cloud login step (neighbour units)
      - run: terraform init -input=false -backend-config=${{ inputs.backend-config }}
      - id: plan
        run: |
          set +e; terraform plan -input=false -detailed-exitcode -out=tfplan; rc=$?; set -e
          echo "exitcode=$rc" >> "$GITHUB_OUTPUT"; [ "$rc" -eq 1 ] && exit 1 || true
          terraform show -no-color tfplan >> "$GITHUB_STEP_SUMMARY"
      - if: steps.plan.outputs.exitcode == '2'
        run: tar -czf "$RUNNER_TEMP/tfwd.tgz" .        # whole working dir incl. .terraform (C2-A)
      - if: steps.plan.outputs.exitcode == '2'
        uses: actions/upload-artifact@<SHA-not-in-family-facts>
        with:
          name: tfplan-${{ inputs.environment }}-${{ inputs.component }}-${{ github.sha }}
          path: ${{ runner.temp }}/tfwd.tgz
          retention-days: 1
  apply:
    needs: plan
    if: needs.plan.outputs.exitcode == '2'
    runs-on: ubuntu-latest                          # same label as plan: same OS/arch
    environment: ${{ inputs.environment }}          # required reviewers + env secrets
    permissions: { contents: read, id-token: write }
    steps:
      - uses: actions/download-artifact@<SHA-not-in-family-facts>
        with:
          name: tfplan-${{ inputs.environment }}-${{ inputs.component }}-${{ github.sha }}
          path: ${{ runner.temp }}
      - run: |
          mkdir -p "$GITHUB_WORKSPACE/${{ inputs.working-directory }}"
          tar -xzf "$RUNNER_TEMP/tfwd.tgz" -C "$GITHUB_WORKSPACE/${{ inputs.working-directory }}"
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with: { terraform_version: "1.17.1", terraform_wrapper: false }
      # cloud login step (write role)
      - working-directory: ${{ inputs.working-directory }}
        run: terraform apply -input=false tfplan
```

Notes. The workflow-level `concurrency` covers plan and apply (A9). The approval wait holds
the group, which is intended. Splitting `<env>-plan` and `<env>` environments keeps write
secrets behind reviewers (A8, family rule 10). That the GitHub-hosted runner workspace path is
identical across jobs, so the "same absolute path" requirement is met, is (unverified). Extraction
into `$GITHUB_WORKSPACE/<dir>` is intended to reproduce it.

**Drift (`ops-terraform-drift.yml`)**:

```yaml
name: ops-terraform-drift
on:
  schedule: [{ cron: "17 5 * * *" }]
  workflow_dispatch:
permissions: { contents: read }
jobs:
  drift:
    runs-on: ubuntu-latest
    environment: prod-plan
    permissions: { contents: read, issues: write, id-token: write }
    defaults: { run: { working-directory: infra/network } }
    env: { TF_IN_AUTOMATION: "true", TF_INPUT: "false" }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with: { terraform_version: "1.17.1", terraform_wrapper: false }
      # read-only login step
      - run: terraform init -input=false -backend-config=../env/prod/network.s3.tfbackend
      - id: drift
        run: |
          set +e; terraform plan -input=false -refresh-only -detailed-exitcode -no-color > drift.txt; rc=$?; set -e
          echo "exitcode=$rc" >> "$GITHUB_OUTPUT"; [ "$rc" -eq 1 ] && exit 1 || true
      - if: steps.drift.outputs.exitcode == '2'
        env: { GH_TOKEN: "${{ secrets.GITHUB_TOKEN }}" }
        run: |
          head -c 60000 drift.txt > body.txt
          gh issue --repo "${{ github.repository }}" create --title "Drift: prod/network" --body-file body.txt
```

Note: whether `-refresh-only` plans acquire the state lock is (unverified). Treat the drift role
like C3.

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Terraform 1.17.1)
terraform version                      # Expected: Terraform v1.17.1
terraform fmt -check -recursive        # Expected: exit 0, no file list
terraform init -input=false -backend=false
terraform validate                     # Expected: "Success! The configuration is valid."
terraform test -filter=tests/plan_only.tftest.hcl   # Expected: all run blocks pass (exit codes not stated on the test page, (unverified))
terraform plan -input=false -detailed-exitcode -out=tfplan; echo $?   # Expected: 0 | 2; 1 = error
grep -n "use_lockfile *= *true" infra/*/backend.tf   # Expected: one hit per S3 component
grep -rn "dynamodb_table" infra/                      # Expected: no hits after migration
grep -rn "auto-approve" .github/workflows/            # Expected: no hits
grep -rn "cancel-in-progress: true" .github/workflows/_terraform-*.yml   # Expected: no hits
```

**Mocking** (plan-only tests for PRs; `command = plan` documented on the tests page; mocks since v1.7.0):
```hcl
# tests/plan_only.tftest.hcl — Terraform 1.17
mock_provider "aws" {}

run "bucket_name_is_prefixed" {
  command = plan
  assert {
    condition     = startswith(aws_s3_bucket.this.bucket, "acme-")
    error_message = "bucket must use the acme- prefix"
  }
}
```
The exact `mock_provider` block syntax was not read on the Mocks page (unverified). It is
included because the 1.17 CHANGELOG names `mock_provider`.

## Production Readiness

- **Performance**: cache providers per job with `TF_PLUGIN_CACHE_DIR` in `runner.temp`. The directory "must already exist", and the cache must not be shared across concurrent inits (N9). Avoid `-target` routinely: "It is _not recommended_ to use `-target` for routine operations."
- **Scalability**: split state per component so lock contention and blast radius stay small. `queue: max` allows up to 100 pending runs per group, and "When the queue is full, any additional jobs or workflow runs are canceled". FIFO "ordering is not guaranteed".
- **Monitoring**: drift issues from the schedule. Plan exit codes as job outputs. Job summaries are limited to 1 MiB per step and 20 per job. Schedules in public repos are disabled after 60 days without activity, so watch for that.
- **Security**:
  - Plan files and `.terraform` archives are sensitive (A2, N2, N5). Use `retention-days: 1`, and the repository retention default is 90 days.
  - Use environment-scoped secrets (family rule 10). Required-reviewer environments withhold secrets until approval.
  - Fork PRs receive no secrets, and their `GITHUB_TOKEN` is read-only.
  - Give `GITHUB_TOKEN` the least access ("grant the `GITHUB_TOKEN` the least required access"). Use `pull-requests: write` only on the commenting job, `issues: write` only on drift, and `id-token: write` only on the job that logs in (family rule 7).
  - S3: `encrypt = true`, optional `kms_key_id` (needs `kms:Encrypt`, `kms:Decrypt`, `kms:GenerateDataKey`), and bucket versioning. OCI: `kms_key_id` (master encryption key OCID) and bucket versioning.
  - `::add-mask::` for any derived secret value.
  - SHA pinning and script-injection guidance: see `automating-github-repos-with-actions` (family rule 4).
- **Error handling**: a stale saved plan is rejected at apply time; re-plan instead of retrying (medium confidence, community sources only, see U1). Never `force-unlock` without identifying the holder (project rule, not re-verified here).

## Reference Implementations

- HashiCorp "Running Terraform in automation" tutorial: https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform (2026-10-30)
- hashicorp/setup-terraform README (PR comment with `pull-requests: write`, step-summary alternative): https://github.com/hashicorp/setup-terraform (2026-10-30)
- GitHub "Control deployments" (environment + concurrency YAML): https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments (2026-10-30)
- Oracle "Using Object Storage for State Files": https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm (2026-10-30)
- Neighbour skills, referenced by name only (family rule 12): `automating-github-repos-with-actions` (github-core), `composing-github-actions-pipelines`, `federating-github-actions-aws-oidc`, `federating-github-actions-oci`, `limiting-blast-radius-github-actions-deploys`, `securing-supply-chain-github-actions`, `provisioning-aws-iam-v6`.

## Research Gaps

```
Gap: G1 — No family-facts SHA for actions/upload-artifact, actions/download-artifact (and actions/github-script if used)
Impact: examples cannot be fully SHA-pinned under family rule 4
Workaround: placeholder <SHA-not-in-family-facts>; PR comment uses gh CLI instead of github-script
Follow-up: REQUEST to orchestrator — add rows to _family_facts.md (git ls-remote on the latest v-tags)
§7-ref: Iteration 2 — IRRESOLVABLE (out of researcher's write scope)
```
```
Gap: U1 — Official statement of stale-saved-plan behaviour ("Saved plan is stale")
Impact: concurrency design (A9) relies on it
Workaround: workflow-level concurrency so no apply lands between plan and apply
Follow-up: developer.hashicorp.com apply/plan pages do not state it; only discuss.hashicorp.com (community)
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: U2 — GitHub-hosted runner workspace absolute path identical across jobs
Impact: C2-A extraction "at the same absolute path"
Follow-up: docs.github.com runner reference (not read)
```
```
Gap: U3 — Whether PR plan with -lock=false / refresh-only plan writes any object (plan does not persist state?)
Impact: strict reading of family rule 7 (C3)
Follow-up: developer.hashicorp.com state/locking pages
```
```
Gap: U4 — use_lockfile on OCI S3-compatible endpoint; S3-compat → oci backend migration steps
Impact: N4 migration
Follow-up: Oracle backend page, HashiCorp oci backend page
```
```
Gap: U5 — Env var names for OCI API-key material for the oci backend; SecurityToken flow from GitHub OIDC (F21)
Impact: C7; owned by federating-github-actions-oci
```
```
Gap: U6 — setup-terraform wrapper behaviour with -detailed-exitcode
Impact: A4/A5 choose terraform_wrapper: false to avoid it
Follow-up: setup-terraform README does not cover it
```
```
Gap: U7 — terraform test exit codes and exact mock_provider syntax
Follow-up: /terraform/language/tests/mocking page
```
```
Gap: U8 — upload/download-artifact current major versions (docs show upload@v4/download@v5; download README shows @v8)
Follow-up: release pages for SHA resolution (G1)
```
```
Gap: U9 — workflow-syntax page read only characters 0-100000 of 235839 (environment/outputs sections not read there)
Impact: environment/concurrency syntax confirmed instead via control-deployments page
```

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails A6 | S3 locking current option | Resolved: `use_lockfile`; DynamoDB deprecated | https://developer.hashicorp.com/terraform/language/backend/s3 (2026-10-30) |
| 1 | Guardrails A7 | Native `oci` backend exists in 1.17 + locking | Resolved: yes, `If-None-Match: *` lock | https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30) |
| 1 | Migration Guide | 1.17 breaking changes | Resolved: none | https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md (2026-10-30) |
| 1 | Guardrails A9 | Pending-run cancellation semantics | Resolved (plus `queue: max`) | https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (2026-10-30) |
| 1 | Production Readiness | Stale saved plan behaviour | ⚠️ IRRESOLVABLE — only community (discuss.hashicorp.com) confirms; official pages silent | — |
| 2 | Guardrails C5 | `terraform test` default command | Resolved: `command = apply` default; `plan` option | https://developer.hashicorp.com/terraform/language/tests (2026-10-30) |
| 2 | Guardrails A2 | Who can download artifacts / default retention | Resolved: read access; 90 days, 1-90 public / 1-400 private | https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts (2026-10-30) |
| 2 | Guardrails A6 | Triangulate S3 lock mechanism | Added AWS conditional-writes page | https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html (2026-10-30) |
| 2 | Implementation | Artifact action SHAs | ⚠️ IRRESOLVABLE — facts file is orchestrator-owned; request raised (G1) | — |

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (PR workflow, merge workflow, artifact movement, state AWS/OCI, concurrency, drift, setup-terraform, exit codes)
- [x] Pattern counts driven by domain needs (11 / 7 / 9)
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (GitHub Actions ↔ S3 / OCI backends)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (3 workflows; artifact SHAs pending G1)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or marked single-source (A4, A5, A8, A10 single-source official; A9, A11 composition medium)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score in Metadata
- [x] Every Research Gap cross-referenced

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1-A3, A6, A7 (triangulated); A4, A5, A8, A10 (single official page, read in full); N1-N9; exit codes 0/1/2; DynamoDB deprecation; `oci` backend locking; plan-file sensitivity; environment reviewer limits; artifact retention/read access.
- **Medium Confidence (validate with user)**: A9 workflow-level placement; A11 composition; C1-C3 recommendations; C2-B re-init variant; `use_lockfile` relying on S3 conditional writes; OCI `SecurityToken` route (F20/F21).
- **Low Confidence (must ask human)**: U1-U9 and G1.
- **Edge Cases (pause)**: Terraform 1.17.0 was released 2026-10-21, less than 30 days before the research date (the skill's edge-case rule). The upgrade guide and changelog are published and list no breaking changes, so research proceeded. Required reviewers on private repos need GitHub Enterprise (Free/Pro/Team: public repos only). Confirm the user's plan.
- **Emergency Stop**: not triggered. All core claims rest on official pages.
- **Requests for the orchestrator (not edited by this researcher)**: add family-facts rows for `actions/upload-artifact` and `actions/download-artifact` SHAs (G1).

## Pages read

| URL | read on | official yes/no | instructions found in the page yes/no |
|---|---|---|---|
| https://developer.hashicorp.com/terraform/cli/commands/plan | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/cli/commands/apply | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/cli/commands/show | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/cli/commands/test | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/language/tests | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/language/backend/s3 | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/language/backend/oci | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/cli/config/environment-variables | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/cli/config/config-file | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/language/files/dependency-lock | 2026-10-30 | yes | yes |
| https://developer.hashicorp.com/terraform/language/upgrade-guides | 2026-10-30 | yes | no |
| https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform | 2026-10-30 | yes (undated tutorial) | yes |
| https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md | 2026-10-30 | yes (vendor repo) | no |
| https://github.com/hashicorp/setup-terraform | 2026-10-30 | yes (vendor repo) | yes |
| https://github.com/actions/download-artifact | 2026-10-30 | yes (GitHub-owned repo) | yes |
| https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/tutorials/store-and-share-data | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts | 2026-10-30 | yes | yes |
| https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/tutorials/authenticate-with-github_token | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands | 2026-10-30 | yes | yes |
| https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (partly read: characters 0-100000 of 235839) | 2026-10-30 | yes | yes |
| https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html | 2026-10-30 | yes | yes |
| https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm | 2026-10-30 | yes | yes |
| https://discuss.hashicorp.com/t/terraform-show-and-saved-plan-is-stale-while-apply-is-running/33098 (search result only, not fetched) | 2026-10-30 | no (community) | no |

## Source Bibliography

**Primary (official, Terraform v1.17.x pages unless noted; all read 2026-10-30; HashiCorp pages show no publication date, version label "v1.17.x (latest)")**
- Terraform plan command: https://developer.hashicorp.com/terraform/cli/commands/plan (`-detailed-exitcode`, `-out` sensitivity, `-refresh-only`, `-minimal-refresh`, `-input=false`, `-lock`, `-target`)
- Terraform apply command: https://developer.hashicorp.com/terraform/cli/commands/apply (saved plan mode, `-auto-approve` ignored with plan file)
- Terraform show command: https://developer.hashicorp.com/terraform/cli/commands/show (`-no-color`, `-json` plain-text sensitive values)
- Terraform test command: https://developer.hashicorp.com/terraform/cli/commands/test (creates real infrastructure, `-filter`, `-junit-xml`, default `tests` dir)
- Terraform tests language: https://developer.hashicorp.com/terraform/language/tests (`command = apply` default, `command = plan`, mocks since v1.7.0)
- S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3 (`use_lockfile`, DynamoDB deprecated, IAM, versioning, `-backend-config` persistence)
- OCI backend: https://developer.hashicorp.com/terraform/language/backend/oci (locking via `If-None-Match: *`, auth values, `workspace_key_prefix` default `tf-state-env`, env vars)
- Environment variables: https://developer.hashicorp.com/terraform/cli/config/environment-variables (`TF_IN_AUTOMATION`, `TF_INPUT`, `TF_PLUGIN_CACHE_DIR`)
- CLI config file, provider plugin cache: https://developer.hashicorp.com/terraform/cli/config/config-file
- Dependency lock file: https://developer.hashicorp.com/terraform/language/files/dependency-lock
- Upgrade guide v1.17: https://developer.hashicorp.com/terraform/language/upgrade-guides
- Running Terraform in automation (tutorial, undated): https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform
- Terraform v1.17 CHANGELOG (1.17.0 2026-10-21, 1.17.1 2026-10-28): https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md
- hashicorp/setup-terraform README (v4.0.1 per F2): https://github.com/hashicorp/setup-terraform
- actions/download-artifact README: https://github.com/actions/download-artifact
- GitHub concurrency: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- GitHub deployments and environments: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- GitHub control deployments: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments
- GitHub store and share data (artifacts): https://docs.github.com/en/actions/tutorials/store-and-share-data
- GitHub download workflow artifacts: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
- GitHub Actions repository settings (retention 90 days; 1-90 public, 1-400 private): https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- GitHub GITHUB_TOKEN tutorial (gh issue create, `issues: write`): https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
- GitHub events that trigger workflows (fork secrets, schedule limits, merged PR condition): https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- GitHub workflow commands (job summaries 1 MiB/step, 20/job, masking): https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands
- GitHub workflow syntax (default shells, permissions; partly read 0-100000 of 235839 chars): https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- AWS S3 conditional writes: https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html
- Oracle "Using Object Storage for State Files" (native backend v1.12.0+, S3-compat deprecated; page shows copyright 2026, no update date): https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm

**Family facts used**: F1 (Terraform 1.17.1), F2 (setup-terraform SHA), F3 (configure-aws-credentials, referenced only), F10 (checkout SHA), F16/F19 (workflow layout, no `secrets: inherit`), F20/F21 (OCI token exchange, medium confidence) — `workspace/github-actions-cicd/_family_facts.md`.

**Validation (community, not used for any Always/Never claim)**
- HashiCorp Discuss, "Terraform show and Saved plan is stale": https://discuss.hashicorp.com/t/terraform-show-and-saved-plan-is-stale-while-apply-is-running/33098 (search snippet only, 2026-10-30) — supports U1 at (medium confidence).
