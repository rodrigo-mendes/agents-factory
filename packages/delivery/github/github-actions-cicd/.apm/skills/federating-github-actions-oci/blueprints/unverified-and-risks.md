# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

## Version-lifetime risk

As of 2026-10-30.

- `run-oci-cli-command` v1.3.2 and `login-ocir` v1.3.0 declare `node20`; GitHub removed Node 20 from runners on 2026-09-23 and the changelog is silent on node20-declared actions. Run a smoke job; fallback is plain `docker login` plus the OCI CLI. Source: https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/
- Release pages show "10 Sep" and "18 Jun" without a year; the SHAs come from the family facts, resolved with `git ls-remote` on 2026-10-30. Re-resolve before bumping. Source: https://github.com/oracle-actions/login-ocir/releases
- The `oracle/oci` provider version and the OCI CLI release are not pinned by this skill. Source: https://registry.terraform.io/providers/oracle/oci/latest
- Path A depends on an identity-domain feature documented on an unversioned Oracle page; re-read it before adopting. Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm
- The `oci` backend supports locking; the older repository statement that OCI has no state locking applies to the S3-compatible route. Source: https://developer.hashicorp.com/terraform/language/backend/oci

## Unverified (11)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | OCI CLI and Terraform provider accept an externally obtained session token through `security_token_file`; pages describe only CLI-generated tokens | Path A viability | Path B default; manual smoke test |
| U2 | The ephemeral resource principal workload-identity flow; no docs.oracle.com page read | none, left out | not used |
| U3 | Behaviour of node20-declared Oracle actions after 2026-09-23 | OCIR login or CLI step may fail | smoke job; `docker login` fallback |
| U4 | Whether OCI validates JWT `aud`, GitHub JWKS acceptance by `publicKeyEndpoint`, and the immutable `sub` form (`OWNER@ID/REPO@ID`) for repositories created after 2026-07-15 | Path A trust setup | test in a sandbox domain |
| U5 | Encoding expected by the `public_key` exchange parameter | exchange request rejected | follow the Oracle page example |
| U6 | A rotation interval for API keys and auth tokens; Oracle states none | policy gap | organisational decision |
| U7 | PR plan with the state lock disabled, or with a read-only user that cannot write the lock object | PR plan fails or writes | owned by the Terraform skill |
| U8 | Preferred OCIR host form between the two documented forms | wrong host | use the `ocir_endpoint` output or ask |
| U9 | Whether `login-ocir` handles identity-domain usernames | login failure | plain `docker login` |
| U10 | Backend environment-variable names for credentials other than the documented `OCI_region` example | wiring | `-backend-config` identifiers plus `private_key_path` |
| U11 | Identity-domain group prefix syntax in policy statements; policy syntax page returned HTTP 404 | policy rejected | copy the tenancy's existing syntax |

## Irresolvable (1)

| ID | Claim | Note |
|---|---|---|
| I1 | Official text for U2 and U11: the Oracle workload-identity blogs returned HTTP 403 and the policy syntax page HTTP 404 on 2026-10-30 | nothing in this skill relies on those pages |

## Medium confidence (7)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | Path A end to end with GitHub tokens | mechanism official; GitHub use is community; consumption assembled from CLI-token pages | sandbox test |
| M2 | Rotation by overlap (add new, switch secrets, delete old) | limits documented; no rotation page | smoke job after the switch |
| M3 | Clearing every capability except API keys and auth token is least privilege | capability list documented; the page states no least-privilege advice | review user capabilities |
| M4 | One statement combining compartment scope and `request.permission` filter for OCIR push | composition of two documented forms | try the statement in a test compartment |
| M5 | Config-profile variant of the backend reads `key_file` | profile entries documented separately | test `terraform init` |
| M6 | One trust per domain with several impersonation rules | page says "Use unique issuer" | read the trust API response |
| M7 | An exchanged token lasts about 60 minutes | one-hour limit documented for CLI-generated tokens | measure in a sandbox |

## Coverage limits (5)

| ID | Limit |
|---|---|
| L1 | Every page was read through the WebFetch tool, which returns an extracted rendering, not raw HTML; character coverage is not measurable |
| L2 | Oracle pages show no revision date, only a 2026 copyright footer |
| L3 | Action release dates on release pages carry no year |
| L4 | GitHub and README examples show older action tags; this skill uses only the family-facts pins |
| L5 | The Oracle A-Team GitHub guide and the Oracle workload-identity blogs returned HTTP 403 and were not read |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | path-a-token-exchange.md consumption and limits; SKILL.md Path A discussion | U1 |
| (unverified) | path-a-token-exchange.md workload-identity bullet | U2 |
| (unverified) | SKILL.md version risk and Ask First (OCIR login); ocir-and-cli.md node 20 risk | U3 |
| (unverified) | path-a-token-exchange.md trust notes; immutable `sub` form in path-a-token-exchange.md, never-do-patterns.md, plan-variants.md | U4 |
| (unverified) | path-a-token-exchange.md exchange script | U5 |
| (unverified) | SKILL.md Ask First (rotation); policies-and-rotation.md rotation | U6 |
| (unverified) | SKILL.md Ask First (PR plan); always-do-patterns.md PR-only environment; policies-and-rotation.md PR-only read user | U7 |
| (unverified) | SKILL.md Ask First (OCIR host form); ocir-and-cli.md host form | U8 |
| (unverified) | ocir-and-cli.md login-ocir section | U9 |
| (unverified) | login-oci-action.md notes | U10 |
| (unverified) | policies-and-rotation.md PR-only read user | U11 |
| (medium confidence) | SKILL.md Ask First (auth path); path-a-token-exchange.md header | M1 |
| (medium confidence) | SKILL.md Ask First (rotation); policies-and-rotation.md rotation | M2 |
| (medium confidence) | policies-and-rotation.md capabilities | M3 |
| (medium confidence) | policies-and-rotation.md OCIR push-only policy | M4 |
| (medium confidence) | always-do-patterns.md backend key as a file | M5 |
| (medium confidence) | path-a-token-exchange.md trust notes | M6 |
| (medium confidence) | SKILL.md Ask First (job length); path-a-token-exchange.md limits | M7 |

## Source Bibliography

All fetched 2026-10-30. Oracle pages carry no revision date.

**docs.oracle.com**
- https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm
- https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm
- https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm
- https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm
- https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/users/edit-users-capabilities.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm
- https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm
- https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryprerequisites.htm
- https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm

**developer.hashicorp.com and GitHub**
- https://developer.hashicorp.com/terraform/language/backend/oci
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- https://docs.github.com/en/actions/reference/security/oidc
- https://docs.github.com/en/get-started/learning-about-github/githubs-plans
- https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/

**Repositories and releases**
- https://github.com/oracle-actions/run-oci-cli-command (README, releases, v1.3.2, action.yml at the pinned commit)
- https://github.com/oracle-actions/login-ocir (README, releases, action.yml at the pinned commit)
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`

**Community (classification only, not used for any Always Do or Never Do claim; not read, HTTP 403)**
- https://www.ateam-oracle.com/github-actions-oci-a-guide-to-secure-oidc-token-exchange
