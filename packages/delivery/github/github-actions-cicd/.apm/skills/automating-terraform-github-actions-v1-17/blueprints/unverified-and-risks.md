# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified (11)](#unverified-11)
- [Irresolvable (1)](#irresolvable-1)
- [Medium confidence (8)](#medium-confidence-8)
- [Coverage limits (4)](#coverage-limits-4)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

As of 2026-10-30.

- Terraform 1.17.0 shipped on 2026-10-21 and 1.17.1 on 2026-10-28; the upgrade guide and changelog list no breaking changes, but the line is new. Re-read the changelog before moving the pin. Source: https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md
- S3 `dynamodb_table` is deprecated and "will be removed in a future minor version"; a pipeline that still relies on it breaks at that minor. Source: https://developer.hashicorp.com/terraform/language/backend/s3
- The S3-compatible OCI route is deprecated by Oracle; the `oci` backend needs Terraform v1.12.0 or later. Source: https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm
- Pinned SHAs (setup-terraform v4.0.1, checkout v7.0.1, upload-artifact v7.0.2, download-artifact v8.0.2) were resolved on 2026-10-30; re-run `git ls-remote` before bumping. Source: https://github.com/actions/upload-artifact/releases
- 1.17.0 adds `-minimal-refresh` and takes Terraform Policy (`-policies`) out of experimental; neither is used here, and `-minimal-refresh` must not be used for drift. Source: https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md

## Unverified (11)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | Official statement of what happens when a saved plan is stale; only a community post (HashiCorp Discuss, search snippet) supports that apply rejects it | concurrency design leans on it | one concurrency group over plan and apply; re-plan instead of retry |
| U2 | GitHub-hosted runner workspace path is identical across jobs | extracting the plan archive "at the same absolute path" | extract into the workspace directory; confirm with a dry run |
| U3 | Whether a `-lock=false` plan or a `-refresh-only` plan writes any object or takes the state lock | strict reading of "pull requests never write to cloud" | read-only role; label the PR plan as preview |
| U4 | `-reconfigure` versus `-migrate-state` for a lock-only S3 change; the S3-compatible to `oci` migration steps; locking on the OCI S3-compatible endpoint | migration mistakes | test on a copy of the state first |
| U5 | Environment variable names for OCI API-key material in the `oci` backend; the SecurityToken flow from a GitHub OIDC token | OCI login wiring | owned by `federating-github-actions-oci` |
| U6 | `setup-terraform` wrapper behaviour with `-detailed-exitcode` | exit code or stdout altered | `terraform_wrapper: false` |
| U7 | `terraform test` exit codes and the exact `mock_provider` syntax | a mocked PR test fails on syntax | read the mocking page before committing the test file |
| U8 | Applying a PR plan artifact is safe under merge queues; a `tfplan`-only artifact plus re-init is equivalent to archiving the whole directory | stale or divergent plans | default to fresh plan on the merge commit and whole-directory archive |
| U9 | OCI auth modes other than API key on self-hosted OCI runners; the model behind Terraform `-policies` | out-of-scope paths | not used by this skill |
| U10 | Artifact names must be unique within a workflow run, so a re-run attempt of the same commit needs a distinct name (README wording of upload-artifact v7 not read) | upload fails or overwrites on re-run | name ends in `github.run_attempt` |
| U11 | A PR job passes the branch policy of an `<env>-pr` environment; an empty `environment:` expression is accepted on Free | PR plan or Free copy fails to start | leave `<env>-pr` without a branch policy; use workflow copies without the `environment:` key |

## Irresolvable (1)

| ID | Claim | Note |
|---|---|---|
| I1 | Official page for stale saved plan behaviour (same gap as U1) | developer.hashicorp.com apply and plan pages are silent; only community text exists |

## Medium confidence (8)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | Workflow-level concurrency in the caller (not job-level) is the right placement | GitHub semantics documented; placement is a design inference | two quick merges to the same component |
| M2 | A scheduled plan plus `gh issue create` is a sound drift pattern | each part documented, composition is design | run once with `workflow_dispatch` |
| M3 | Fresh plan on the merge commit beats applying the PR artifact | constraints documented, recommendation is judgement | ask the user |
| M4 | A PR plan with a read-only role and `-lock=false` is acceptable | HashiCorp warns `-lock=false` is dangerous with concurrent runs | label the comment as preview |
| M5 | `use_lockfile` is implemented with S3 conditional writes | inferred from two pages, not stated | read the backend source before relying on it |
| M6 | OCI `SecurityToken` via token exchange works with GitHub OIDC | mechanism documented by Oracle, GitHub use only by community | sandbox test |
| M7 | Cancelling an apply mid-run leaves partial state and a stale lock | consequence inferred, cancel semantics documented | never cancel applies |
| M8 | Archiving the whole working directory is the default artifact content | HashiCorp guidance read; trade-offs are judgement | ask the user |

## Coverage limits (4)

| ID | Limit |
|---|---|
| L1 | The workflow-syntax page was read only for characters 0-100000 of 235839; environment and outputs syntax were confirmed on the control-deployments page instead |
| L2 | HashiCorp pages carry the label v1.17.x (latest) and no publication date; the automation tutorial is undated |
| L3 | GitHub docs examples for artifacts show older upload and download majors; this skill uses only the pinned versions from the family facts |
| L4 | Required reviewers on private repositories depend on the GitHub plan; the Free, Pro and Team limit was read on the deployments page, but the user's plan is unknown |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | never-do-patterns.md trap section; workflow-tf-apply.md notes | U1 |
| (unverified) | workflow-tf-apply.md notes (workspace path) | U2 |
| (unverified) | workflow-tf-plan.md notes; workflow-drift.md notes | U3 |
| (unverified) | SKILL.md Ask First (lock migration); state-backends.md migration and S3-compatible lock notes | U4 |
| (unverified) | state-backends.md OCI authentication | U5 |
| (unverified) | always-do-patterns.md pinned CLI; workflow-tf-plan.md notes | U6 |
| (unverified) | SKILL.md Ask First (test scope); workflow-tf-plan.md notes | U7 |
| (unverified) | SKILL.md Ask First (which plan is applied, plan artifact content) | U8 |
| (unverified) | workflow-tf-plan.md notes (artifact name run attempt) | U10 |
| (unverified) | plan-variants.md (PR environment branch policy, empty environment expression) | U11 |
| (unverified) | state-backends.md OCI authentication (other modes) | U9 |
| (unverified) | never-do-patterns.md trap section | I1 |
| (medium confidence) | SKILL.md Ask First (concurrency placement); workflow-callers.md cd-infra notes | M1 |
| (medium confidence) | SKILL.md Ask First (drift scope); workflow-drift.md notes | M2 |
| (medium confidence) | SKILL.md Ask First (which plan is applied) | M3 |
| (medium confidence) | SKILL.md Ask First (PR plan and state access); workflow-tf-plan.md notes | M4 |
| (medium confidence) | state-backends.md S3 mechanism row | M5 |
| (medium confidence) | SKILL.md Ask First (OCI credentials); state-backends.md OCI authentication | M6 |
| (medium confidence) | never-do-patterns.md N8 | M7 |
| (medium confidence) | SKILL.md Ask First (plan artifact content); workflow-tf-plan.md notes | M8 |

## Source Bibliography

All fetched 2026-10-30. HashiCorp pages are the v1.17.x documentation (no publication date).

**developer.hashicorp.com**
- https://developer.hashicorp.com/terraform/cli/commands/plan
- https://developer.hashicorp.com/terraform/cli/commands/apply
- https://developer.hashicorp.com/terraform/cli/commands/show
- https://developer.hashicorp.com/terraform/cli/commands/test
- https://developer.hashicorp.com/terraform/language/tests
- https://developer.hashicorp.com/terraform/language/backend/s3
- https://developer.hashicorp.com/terraform/language/backend/oci
- https://developer.hashicorp.com/terraform/cli/config/environment-variables
- https://developer.hashicorp.com/terraform/cli/config/config-file
- https://developer.hashicorp.com/terraform/language/files/dependency-lock
- https://developer.hashicorp.com/terraform/language/upgrade-guides
- https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform

**docs.github.com**
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments
- https://docs.github.com/en/actions/tutorials/store-and-share-data
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (partly read)
- https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows

**Repositories and releases**
- https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md
- https://github.com/hashicorp/setup-terraform (README, releases)
- https://github.com/actions/checkout/releases
- https://github.com/actions/upload-artifact/releases
- https://github.com/actions/download-artifact (README, releases)
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`

**Cloud vendors**
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html
- https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm (token exchange mechanism)

**Community (classification only, not used for any Always Do or Never Do claim)**
- https://discuss.hashicorp.com/t/terraform-show-and-saved-plan-is-stale-while-apply-is-running/33098 (search snippet only)
- https://www.ateam-oracle.com/github-actions-oci-a-guide-to-secure-oidc-token-exchange (OCI token exchange with GitHub Actions)
