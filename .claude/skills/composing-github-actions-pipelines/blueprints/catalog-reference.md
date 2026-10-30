# Family block catalog

Back to [SKILL.md](../SKILL.md). Reference list of the building blocks of this family, as of 2026-10-30. All paths are in the repository that holds the callers (family decision, default location). The owning skill is the authority for each block's body; this table fixes only the names, the level and the interface shape so callers and blocks stay replaceable.

Contents: [Callers](#callers) | [Reusable workflows](#reusable-workflows) | [Composite actions](#composite-actions) | [Reading the table](#reading-the-table)

## Callers

| File | Trigger | Calls | Rule |
|---|---|---|---|
| `ci-<app>.yml` | `pull_request` | build, test, scan, preview plan | never deploys, never applies; PR-read credentials only |
| `cd-<app>.yml` | push to `main` or release | build once, publish, deploy, promote | deploys through `environment` input |
| `ops-<task>.yml` | `schedule` or `workflow_dispatch` | drift check, rollback, smoke test | never applies from a schedule |

## Reusable workflows

The interfaces below are copied from the owner skills (checked 2026-10-30). The owner skill stays the authority: read its workflow blueprint before wiring a caller, and never add an input the owner does not define. Names with an underscore (`artifact_name`) and with a hyphen (`artifact-name`) differ by owner; copy them exactly.

| Block | Inputs (secrets marked) | Outputs | Owner skill |
|---|---|---|---|
| `_tf-plan.yml` | `working-directory`, `cloud` (aws or oci), `environment`, `component`, `backend-config`, `preview` | `plan-artifact-name`, `has-changes` | `automating-terraform-github-actions-v1-17` |
| `_tf-apply.yml` | `working-directory`, `cloud`, `environment`, `component`, `plan-artifact-name` | none | `automating-terraform-github-actions-v1-17` |
| `_java-build.yml` | `tool` (required: maven or gradle), `java-version`, `package` (jar, zip or image), `working-directory` | `artifact-name`, `artifact-digest` | `building-java-github-actions` |
| `_node-build.yml` | `app-dir`, `mode` (required: static, standalone or vercel), `node-version`, `package-manager`, `retention-days` | `artifact-name`, `artifact-digest` | `building-nextjs-github-actions-v16-4` |
| `_deploy-vercel.yml` | `environment`, `vercel-cli-version` (required), `node-version`, `app-dir`; secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` | `deployment-url` | `building-nextjs-github-actions-v16-4` |
| `_deploy-s3-cf.yml` | `environment`, `artifact-name`, `artifact-digest` | `release-prefix` | `building-nextjs-github-actions-v16-4` |
| `_image-publish.yml` | `registry` (required: ghcr, ecr or ocir), `image-name` (required), `context`, `file`, `platforms`, `push`, `environment` (ecr and ocir push only), `aws-region`, `ocir-host`, `artifact-name` (optional built artifact downloaded into `context`); no secrets declared: the ECR job reads `vars.ECR_PUSH_ROLE_ARN` and the OCIR job its credentials from the `<env>-publish` environment | `digest`, `image-ref` (already `@sha256:`) | `publishing-container-images-github-actions` |
| `_promote.yml` | `environment`, `app`, `target`, `phase`, `canary_weight`, `artifact_name`, `artifact_sha256`; secret `VERCEL_TOKEN` (optional) | `deployed_ref`, `previous_ref` | `limiting-blast-radius-github-actions-deploys` |
| `_rollback.yml` | `environment`, `app`, `target`, `previous_ref`, `reason`; secret `VERCEL_TOKEN` (optional) | `rolled_back_to` | `limiting-blast-radius-github-actions-deploys` |
| `_smoke-test.yml` | `base_url`, `expected_ref`, `check_script`, `attempts` | `passed` (`true` or `false`); the job always exits 0, the caller decides the rollback | `limiting-blast-radius-github-actions-deploys` |
| `_security-scan.yml` | `targets` (deps, code, iac, image), `image-ref` (required for image), `fail-on`, `environment` (deploy gate only; holds `REGISTRY_PULL_USER`, `REGISTRY_PULL_TOKEN`); no secrets declared | `blocking-findings` | `securing-supply-chain-github-actions` |
| `_code-security.yml` | `targets` (default `code,deps`: CodeQL and dependency review); called only when the caller's `if: vars.CODE_SECURITY_ENABLED == 'true'` holds; the calling job grants `security-events: write` | none | `securing-supply-chain-github-actions` |

There is no `_deploy-static.yml` in the family: static deploys use `_deploy-s3-cf.yml` (AWS) or `_deploy-vercel.yml`. Examples in this skill use `_deploy-s3-cf.yml`.

## Composite actions

| Block | Purpose | Owner skill |
|---|---|---|
| `./.github/actions/node/setup` | Node install plus `npm ci` (example in [composite actions](./composite-actions.md)) | this skill as the example; Node choices by `building-nextjs-github-actions-v16-4` |
| `./.github/actions/repo/changes` | per-app change detection (see [monorepo](./monorepo-ci-gate.md)) | this skill |
| `./.github/actions/cloud/login-aws` (inputs `role-arn`, `region`, `session-name`, `role-duration-seconds`) | keyless login with OIDC | `federating-github-actions-aws-oidc` |
| `./.github/actions/cloud/login-oci` (inputs `auth-mode`, `region`; output `key-path`) | API key by default, token exchange as option | `federating-github-actions-oci` |

Login blocks are called from the job that holds `id-token: write`; that job also holds the environment, so the login block is a composite action (a composite step runs in the caller's job) and takes any secret as an input.

## Reading the table

- A block that needs a secret, an environment or its own runner is a reusable workflow; a repeated step sequence is a composite action.
- Pass the environment as a string input; the deploying job inside the block sets `environment:` (never the calling job).
- Cross-package references are by skill name only; this skill copies none of their content.
- Add a new block by choosing the owner skill first; if none fits, the block belongs in this skill's catalog with a confirmed interface.
