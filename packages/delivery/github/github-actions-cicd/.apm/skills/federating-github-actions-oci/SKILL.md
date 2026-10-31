---
name: federating-github-actions-oci
description: "Authenticates GitHub Actions to OCI: composite login-oci (API key default, optional token exchange), OCI CLI, Terraform oci provider and backend, OCIR login, least-privilege policies, plan variants. Use when wiring OCI credentials into workflows. Not for AWS."
---

# OCI authentication from GitHub Actions

> Version lock: Terraform 1.17.x (pin 1.17.1), `oracle-actions/run-oci-cli-command` v1.3.2, `oracle-actions/login-ocir` v1.3.0. Research date **2026-10-30**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: how a job proves its identity to OCI (CLI, provider, `oci` backend, OCIR). Backend blocks and plan/apply logic belong to `automating-terraform-github-actions-v1-17`; image build and push to `publishing-container-images-github-actions`; SHA pinning and injection-safe scripting to `automating-github-repos-with-actions`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| Terraform CLI | 1.17.1 (2026-10-28) | https://github.com/hashicorp/terraform/releases |
| `oracle-actions/run-oci-cli-command` | v1.3.2 = `368cc7991534d1b8074846d10e1d84ac4c0d1a28`; declares `node20` | https://github.com/oracle-actions/run-oci-cli-command/releases/tag/v1.3.2 |
| `oracle-actions/login-ocir` | v1.3.0 = `d65011bf8c9300e51a98658388a0fb46d1ed54b1`; declares `node20` | https://github.com/oracle-actions/login-ocir/releases/tag/v1.3.0 |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `hashicorp/setup-terraform` | v4.0.1 = `dfe3c3f87815947d99a8997f908cb6525fc44e9e` | https://github.com/hashicorp/setup-terraform/releases |
| Runner Node | Node 24 default since 2026-06-16; Node 20 removed 2026-09-23 | https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/ |
| OCI CLI environment contract | `OCI_CLI_*` variables | https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm |

**Version-lifetime risk** (as of 2026-10-30; details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Both Oracle actions declare `node20`; the changelog does not say how they run after Node 20 removal (unverified).
- The `oracle/oci` provider version is not pinned by this skill; read the registry before pinning.
- Pinned action SHAs go stale; re-resolve with `git ls-remote` before every bump.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Composite action login-oci](./blueprints/login-oci-action.md)
- [OCIR and OCI CLI actions](./blueprints/ocir-and-cli.md)
- [Policies, capabilities and rotation](./blueprints/policies-and-rotation.md)
- [Path A: token exchange](./blueprints/path-a-token-exchange.md)
- [Plan variants: Pro/Team and Free](./blueprints/plan-variants.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: one composite `./.github/actions/cloud/login-oci` (inputs `auth-mode` = `api-key` or `token-exchange`, and `region`) prepares the job; credentials arrive as job `env` from environment secrets. **Path B (API key of a dedicated CI user) is the default**; Path A (token exchange) is optional. Cross-references by name only: `automating-terraform-github-actions-v1-17`, `limiting-blast-radius-github-actions-deploys`.

### ✅ Always Do

- **Pass CLI credentials through `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT` and `OCI_CLI_REGION`** ([CLI variables](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm)).
- **Keep `silent` at its default (`'True'`) on `run-oci-cli-command`** ([action.yml](https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml)).
- **Give the Terraform provider the key content through `OCI_PRIVATE_KEY`** ([provider configuration](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm)).
- **Give the `oci` backend its key as `private_key_path`**; no key-content argument is documented ([oci backend](https://developer.hashicorp.com/terraform/language/backend/oci)).
- **Use partial backend configuration for credential identifiers** ([oci backend](https://developer.hashicorp.com/terraform/language/backend/oci)).
- **Store deploy credentials as environment secrets** ([deployments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
- **Restrict each deploy environment to deployment branch `main`** on Pro or Team private repos ([manage environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)).
- **Use a separate PR-only read user and `<env>-pr` environment for pull_request jobs** (family decision, rule 13).
- **Use a regular, non-service user for Path B**; service users cannot hold API keys ([token exchange page](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm)).
- **Log in to OCIR with an auth token as password and `<tenancy-namespace>/<username>` as username** ([docker push how-to](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm)).
- **Pre-create OCIR repositories in the target compartment** ([repository policies](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm)).
- **Limit push rights with `request.permission` filters** ([repository policies](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm)).
- **Scope state-bucket access with `target.bucket.name`** ([common policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm)).
- **Enable versioning on the state bucket** ([oci backend](https://developer.hashicorp.com/terraform/language/backend/oci)).
- **Stay within three API keys per user** ([managing credentials](https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm)).
- **Stay within two auth tokens per user** ([managing credentials](https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md), [composite action](./blueprints/login-oci-action.md), [policies](./blueprints/policies-and-rotation.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Auth path | B API key (default) vs A token exchange (medium confidence); A still stores an app client secret and OCIR still needs an auth token | "Can an identity-domain administrator create a trust and two confidential apps, and does every OCI job finish within one hour?" |
| GitHub plan | Pro/Team private (default) vs Free private (weaker, [plan variants](./blueprints/plan-variants.md)) | "Which plan owns this private repository?" |
| OCIR login | `login-ocir` (node20, unverified after 2026-09-23) vs plain `docker login` | "Is a third-party node20 action acceptable?" |
| OCIR host form | `ocir.<region>.oci.oraclecloud.com` vs `<region-key>.ocir.io`; preference unverified | "Which form does the tenancy already use?" |
| PR plan and state lock | A read-only user cannot write the lock object; lock-disabled PR plans are unverified | "Should PR plans read cloud state?" |
| Rotation interval | Oracle states no interval (unverified); overlap procedure (medium confidence) | "What rotation interval does policy require?" |
| Job length on Path A | Exchanged token lasts about one hour (medium confidence) | "Do any OCI jobs exceed 60 minutes?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Repository-scoped secrets for deploy keys on Pro/Team ([environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)) | environment secrets plus deployment branch `main` |
| Deployable OCI credentials in a pull_request job (family decision, rule 13) | `<env>-pr` environment with the read-only user |
| Key content in `-backend-config` or a committed key file ([oci backend](https://developer.hashicorp.com/terraform/language/backend/oci)) | key file in `$RUNNER_TEMP` created with `umask 077` |
| `silent: false` ([action.yml](https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml)) | default masking plus `query` |
| Trust rule `sub eq *` for GitHub ([token exchange page](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm)) | one rule per repository and environment |
| The admin application's client for the exchange call ([token exchange page](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm)) | a non-admin confidential app |
| `curl -k` in the exchange call ([token exchange page](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm)) | `curl --fail --silent --show-error` |
| Required reviewers as the approval gate on private Pro/Team ([deployments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)) | PR review on protected `main` ([plan variants](./blueprints/plan-variants.md)) |
| A service user as the Path B CI user ([token exchange page](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm)) | a regular user with API keys |
| A human administrator's key for CI ([working with API keys](https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm)) | a dedicated CI user in its own group |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| CLI variables | `OCI_CLI_USER`, `_TENANCY`, `_FINGERPRINT`, `_KEY_CONTENT`, `_REGION` | https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm |
| Provider variables | `OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY`, `OCI_REGION` | https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm |
| Backend credential args | `tenancy_ocid`, `user_ocid`, `fingerprint`, `private_key_path`, `region` | https://developer.hashicorp.com/terraform/language/backend/oci |
| Backend locking | lock object via `If-None-Match: *` in the state bucket | https://developer.hashicorp.com/terraform/language/backend/oci |
| Credential limits | 3 API keys, 2 auth tokens per user; auth tokens do not expire | https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm |
| Private-repo environments | secrets need Pro/Team; required reviewers public-only | https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments |
| Protected branches, PR reviewers | Pro/Team private features; not listed for Free | https://docs.github.com/en/get-started/learning-about-github/githubs-plans |

## Verification Loop

Offline, from the repository root (Representative, adapt to your layout).

```bash
grep -RnE "BEGIN (RSA )?PRIVATE KEY" .github/ || echo "OK: no inline keys"          # Expected: OK: no inline keys
grep -RnE "silent: *(false|False)" .github/ || echo "OK"                             # Expected: OK
grep -RnE "backend-config=.?private_key=" .github/ || echo "OK"                      # Expected: OK
grep -RnE "oracle-actions/[a-z-]+@v[0-9]" .github/ || echo "OK: all pinned by SHA"  # Expected: OK: all pinned by SHA
grep -nE '"sub eq \*"' trust*.json || echo "OK"                                      # Expected: OK
test -f .github/actions/cloud/login-oci/action.yml && echo "OK: composite present"   # Expected: OK: composite present
```

Inside a job after login: `stat -c '%a' "$RUNNER_TEMP/oci_api_key.pem"` prints `600`; `oci os ns get --query data --raw-output` prints the namespace and exits 0.

## External Resources

All fetched 2026-10-30.

- [OCI CLI environment variables](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm)
- [Terraform oci backend](https://developer.hashicorp.com/terraform/language/backend/oci)
- [JWT to UPST token exchange](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
