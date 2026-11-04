# Test P6 r1 - federating-github-actions-oci

Evaluator: skill-evaluator (own-context simulation, no sub-agents). Date 2026-10-30. Source read: packages/github-actions-cicd/.apm/skills/federating-github-actions-oci/ (SKILL.md + all blueprints except unverified-and-risks.md).

Verdict: 5 PASS, 0 FAIL. One high-severity contract defect (O-1) in the block shown as the caller body.

## S1 API key in environment secrets on Team - PASS
- Path B, regular CI user per environment, environments `oci-pr`, `oci-dev`, `oci-prod`, branch policy `main`, approval = PR review (plan-variants.md Default table; Always Do bullets; N8).
- Composite `login-oci` with `auth-mode`, `region`; key to `$RUNNER_TEMP/oci_api_key.pem` with `umask 077`; credentials as job env from environment secrets (login-oci-action.md).
- `private_key_path` + identifier-only `-backend-config`; empty `provider "oci" {}` with `OCI_*` (always-do-patterns.md).
- `login-ocir` SHA d65011bf... # v1.3.0 with `auth_token`, node20 risk and `docker login` fallback (ocir-and-cli.md); policies and 3-key / 2-token limits (policies-and-rotation.md). No `secrets: inherit`. must_not OK.

## S2 Token exchange requested - PASS
- Path A optional, medium confidence, Ask First asks for identity-domain admin and one-hour limit; "still stores an app client secret", OCIR still needs auth token; CLI/provider consumption "(unverified)", "Run a manual smoke test". Trust per repository and environment, `sub eq *` forbidden (N5), immutable sub honoured, non-admin app (N6), `curl --fail --silent --show-error` (N7), `id-token: write` only on token-exchange job (login-oci-action.md Notes). Ephemeral resource principal flow left out with reason. Not claimed keyless. OK.

## S3 Personal admin API key - PASS
- N10 and Never Do row 10: dedicated CI user in its own group, push-only and bucket-scoped policies; 3 keys / 2 tokens and rotation with overlap (policies-and-rotation.md); environment secrets kept (N1).

## S4 Key content in -backend-config - PASS
- N3 quotes the backend page warning, forbids `-backend-config="private_key=..."`, gives `$RUNNER_TEMP` file with `umask 077` and `private_key_path=`; Verification Loop provides `stat -c '%a'` -> 600. No invented backend env var names (stated unverified). OK.

## S5 Free private - PASS
- plan-variants.md Free section: no environments / no protected branches, "Warning: weaker ... never silent"; `OCI_PROD_*`, `OCI_PR_*` repository secrets, `push` to `main`, "Approval has no enforcement point", Pro/Team upgrade path. must_not OK.

## Findings
- O-1 (HIGH, cross-skill, breaks rule 10 / own N1): login-oci-action.md "Caller job (reusable workflow body)" declares `on.workflow_call.secrets` `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT` with `required: true`, while the deploy job sets `environment: ${{ inputs.environment }}` and reads `secrets.*`. In a reusable workflow the caller cannot use `environment:` (composing N4), so the caller can only satisfy the `required: true` secrets from repository-scoped secrets, which this skill's N1 and family rule 10 forbid. composing always-do-patterns.md A4 says an environment secret the caller does not supply resolves inside the block. Fix direction: drop the `workflow_call.secrets` section (or make it `required: false`) and read the environment secrets inside the block.
- O-2 (MEDIUM, cross-skill): environments here are `oci-pr`, `oci-dev`, `oci-prod`; automating-terraform-github-actions-v1-17 uses `<environment>-plan` and an `environment` input (`prod` in its callers, which yields `prod-plan`). No `oci-*-plan` environment or CI user exists. The PR-only read user cannot write the backend lock (this skill, policies-and-rotation.md "PR-only read user", defers to the Terraform skill), but the Terraform skill runs the merge-time plan with `-lock=true` on read credentials (terraform T-3). Gap remains open on both sides.
- O-3 (LOW): the caller job example sets up Terraform without `terraform_wrapper: false` (family Terraform skill sets it false) and has no `timeout-minutes` or job-level `permissions`, which composing lists as Always Do. Representative code, but copy-paste inconsistency.
- O-4 (LOW): `exchange.sh` is shown only inline in path-a-token-exchange.md; the composite references `$GITHUB_ACTION_PATH/exchange.sh`. The file must be authored by the executor; not stated explicitly.
- Fact checks: run-oci-cli-command v1.3.2 SHA 368cc799... (F35), login-ocir v1.3.0 SHA d65011bf... (F34), node20 risk (F38), checkout, setup-terraform match. Verification Loop present. Rule 16 text consistent with aws-oidc, composing, java.
