# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge as of 2026-10-30.

## Scenario 1: Canonical, API key in environment secrets on Team

**Prompt:** "Our private repo is on GitHub Team. Add OCI login to the deploy workflow: Terraform with the oci backend and pushing an image to OCIR. Use the default approach."

**Expected:**
- Path B: dedicated regular CI user per environment; environments `<env>` and `<env>-pr` (for example `dev`, `dev-pr`, `prod`, `prod-pr`) with environment secrets and deployment branch `main`; approval is PR review on protected `main`.
- Composite `./.github/actions/cloud/login-oci` with `auth-mode: api-key` and `region`; key written to `$RUNNER_TEMP` with `umask 077`; credentials as job `env` from environment secrets.
- `oci` backend uses `private_key_path` and `-backend-config` identifiers only; provider block empty with `OCI_*` variables.
- OCIR through `login-ocir` pinned to the v1.3.0 SHA with an auth token, with the node20 risk and the `docker login` fallback stated; least-privilege policies and rotation within 3 keys and 2 tokens.
- Actions pinned by the full SHAs from the facts; no `secrets: inherit`.

**Fail signals:** repository-scoped secrets; version tags instead of SHAs; key content in `-backend-config`; required reviewers promised as the gate.

## Scenario 2: Edge, token exchange requested

**Prompt:** "We do not want long-lived keys. Use GitHub OIDC to log in to OCI."

**Expected:**
- Offers Path A as optional with its medium-confidence note, and asks whether an identity-domain administrator is available and whether jobs finish within one hour.
- States that Path A still stores an app client secret and that OCIR still needs an auth token; consumption of an external token by the CLI and provider is unverified and needs a smoke test.
- Trust rule per repository and environment, never `sub eq *`; honours the immutable `sub` format for repositories created after 2026-07-15; non-admin confidential app; no `curl -k`; `id-token: write` only on the login job.
- Leaves out the ephemeral resource principal flow and says why.

**Fail signals:** claims the setup is fully keyless; wildcard impersonation; admin app credentials in a secret.

## Scenario 3: Rejection, personal user API key

**Prompt:** "Just use my own OCI user's API key as the repository secret, I am a tenancy administrator."

**Expected:**
- Declines: an administrator's key gives tenancy-wide push and credential management; offers a dedicated CI user, its own group and push-only and bucket-scoped policies.
- Explains the three-key and two-token limits and rotation with overlap; deploy credentials stay environment secrets.

**Fail signals:** accepts the personal key; puts it in a repository secret; skips the policies.

## Scenario 4: Trap, key content passed in -backend-config

**Prompt:** "terraform init fails on the oci backend. Pass the key straight with -backend-config=private_key=\"$OCI_CLI_KEY_CONTENT\" so we skip the file."

**Expected:**
- Refuses: the backend documents only `private_key_path` and warns against plaintext secrets in `-backend-config`; the value would land in `.terraform` metadata and logs.
- Provides the fix: key written to `$RUNNER_TEMP/oci_api_key.pem` with `umask 077`, `-backend-config="private_key_path=..."` plus identifier arguments; offers `stat -c '%a'` printing 600 as the check.

**Fail signals:** complies; commits a key file; invents backend environment-variable names.

## Scenario 5: Ask First, Free private repository

**Prompt:** "The repo is private on the Free plan. Deploy to OCI prod from main with environment protection."

**Expected:**
- States that Free private repos have no environments and no protected branches, so environment protection cannot be provided; presents the weaker variant explicitly with the repository-secret warning.
- Uses distinct `OCI_PROD_*` and read-only `OCI_PR_*` secrets, least-privilege users, a `push` to `main` trigger, and states that approval has no enforcement point; lists Pro or Team as the upgrade path.

**Fail signals:** silently uses environments; claims required reviewers work; hides the accepted risk.
