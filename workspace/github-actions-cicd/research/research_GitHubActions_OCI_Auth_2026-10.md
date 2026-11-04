# Research: OCI authentication from GitHub Actions (OCI CLI, Terraform oracle/oci provider and `oci` backend, OCIR) — 2026-10

Unit: `federating-github-actions-oci` (unit 4 of the github-actions-cicd family).
Source item: "need: OCI login + OCIR (G1: API key default, token exchange optional with medium confidence)".
Family inputs applied as given: `workspace/github-actions-cicd/_family_facts.md` (F1-F24) and `_family_rules.md` (1-16). Neither file was edited.

Tag convention (family rule 2): `(medium confidence)`, `(unverified)` in plain parentheses. "High" in a confidence line means an official page was read on 2026-10-30 and states the claim.

Read-mode note: every page in this document was read on 2026-10-30 through the WebFetch tool, which returns a model-extracted rendering of the page, not raw HTML. Character counts are not exposed by the tool, so "partly read" cannot be measured in characters; pages that returned an error are listed as "not read" in the Pages read table and nothing in this document relies on them.

---

## Metadata

```yaml
Full_Name: OCI authentication from GitHub Actions (API signing key default; JWT->UPST token exchange optional)
Target_Version: >
  OCI CLI environment-variable contract (docs.oracle.com, page copyright 2026);
  oracle-actions/run-oci-cli-command v1.3.2; oracle-actions/login-ocir v1.3.0;
  Terraform 1.17.x `oci` backend (F1); Terraform oracle/oci provider auth as documented on docs.oracle.com (provider version not pinned here, see Facts requested)
Release_Date: run-oci-cli-command v1.3.2 = "10 Sep" (year not shown, marked Latest); login-ocir v1.3.0 = "18 Jun" (year not shown, marked Latest)
Support_Status: Active (both actions marked "Latest" on their release pages); both actions declare runs.using node20 (see Research Gaps G3)
Primary_Docs:
  - https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm
  - https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm
  - https://developer.hashicorp.com/terraform/language/backend/oci
  - https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm
Official_Repo:
  - https://github.com/oracle-actions/run-oci-cli-command
  - https://github.com/oracle-actions/login-ocir
Research_Date: 2026-10-30
Domain_Complexity: Complex   # auth, credential lifecycle, multi-service (CLI, Terraform, OCIR), GitHub plan constraints
Research_Depth: standard     # brief: "default depth"; no sub-investigators allowed by the brief
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 3 of 5
Triangulated_Count: 6
Unverified_Count: 11
Irresolvable_Count: 4
Research_Quality_Score: 82%  # (86 claims - 11 unverified - 4 irresolvable) / 86, rounded
```

---

## Executive Summary

A GitHub Actions job authenticates to Oracle Cloud Infrastructure with one of two paths. Path B (family default, rule 9) uses the API signing key of a dedicated CI user: the private key content, fingerprint, user OCID, tenancy OCID and region are stored as environment-scoped secrets and handed to the OCI CLI through `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT` and `OCI_CLI_REGION` (the exact five variables both `oracle-actions/run-oci-cli-command` and `oracle-actions/login-ocir` require), to the Terraform `oracle/oci` provider through `OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY`, `OCI_REGION` (or their `TF_VAR_` twins), and to the Terraform `oci` backend, which only documents `private_key_path` (no key-content argument) and therefore needs the key written to a file or an OCI config profile. OCIR login is a separate credential: an auth token (max two per user, they do not expire) used as the Docker password with username `<tenancy-namespace>/<username>`.

Path A (optional, medium confidence, rule 9 / F20 / F21) exchanges the job's GitHub OIDC token (issuer `https://token.actions.githubusercontent.com`, JWKS `https://token.actions.githubusercontent.com/.well-known/jwks`) for an OCI User Principal Session Token (UPST) at `https://<domainURL>/oauth2/v1/token`, validated by an Identity Propagation Trust and mapped to an IAM service user by an impersonation rule on `sub`. The token-exchange mechanism and the trust fields are official; that the OCI CLI and the Terraform provider can consume an externally obtained UPST through a config profile with `security_token_file` + `key_file` and `--auth security_token` / `auth = "SecurityToken"` is assembled from two official pages that describe CLI-generated session tokens, so the end-to-end GitHub flow stays medium confidence. Path A is not fully keyless: the token-exchange call authenticates with the client ID and secret of an identity-domain confidential application, and OCIR login still needs an auth token because `login-ocir` requires `auth_token` and IAM service users cannot hold API keys or passwords. The newer "WIF with ephemeral RPST" flow has no docs.oracle.com page that this research could find (only an Oracle blog that returned HTTP 403 and A-Team posts), so it is out of the skill (unverified).

Three findings change the family defaults and must reach the orchestrator: (1) on GitHub Free, environments (and therefore environment secrets) exist only for public repositories, so a private repo on Free cannot satisfy rule 10; Pro or Team is needed for any repo that deploys to OCI; (2) on Pro/Team private repos, required reviewers, wait timers and custom protection rules are unavailable, while deployment branches and tags and environment secrets are available, which fits rule 16; (3) the Terraform `oci` backend does support state locking (`If-None-Match: *` lock object), contradicting the older "OCI has no state locking" statement in this repo's OCI Terraform rules. Domain complexity is Complex (credential lifecycle, IAM, two auth paths, plan-dependent GitHub features).

---

## Architectural Guardrails

> Confidence legend: High (official page read 2026-10-30; "Triangulated" = two independent official pages) | Medium (one source, or assembled from adjacent official pages) | Low (community only — not used in Always/Never).

### ✅ Mandatory Patterns

**M1. Pass OCI CLI credentials through the five documented `OCI_CLI_*` variables**
> Confidence: High | Triangulated: docs.oracle.com CLI environment variables (2026-10-30) + run-oci-cli-command README (2026-10-30) + login-ocir README (2026-10-30)
- Why: `run-oci-cli-command` and `login-ocir` both document exactly `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT`, `OCI_CLI_REGION`; the OCI CLI page defines `OCI_CLI_KEY_CONTENT` as "The full content of the private key" in PEM format. Environment variables override the config file; command options override both.
- Code (version-tagged: run-oci-cli-command v1.3.2, OCI CLI env contract 2026):
  ```yaml
  # Representative — adapt to your environment
  jobs:
    oci-smoke:
      runs-on: ubuntu-latest
      environment: oci-dev              # environment-scoped secrets (rule 10)
      permissions:
        contents: read
      env:
        OCI_CLI_USER: ${{ secrets.OCI_CLI_USER }}
        OCI_CLI_TENANCY: ${{ secrets.OCI_CLI_TENANCY }}
        OCI_CLI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
        OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_CLI_KEY_CONTENT }}
        OCI_CLI_REGION: ${{ vars.OCI_CLI_REGION }}
      steps:
        - uses: oracle-actions/run-oci-cli-command@<SHA-pending-new-F-row> # v1.3.2
          id: ns
          with:
            command: os ns get
            query: data
  ```
- Source: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm (2026-10-30); https://github.com/oracle-actions/run-oci-cli-command (2026-10-30); https://github.com/oracle-actions/login-ocir (2026-10-30)

**M2. Keep `run-oci-cli-command` output masked (`silent` left at its default)**
> Confidence: High (single official source: the action's own action.yml at the v1.3.2 commit)
- Why: action.yml at `368cc79…` says `silent` defaults to `'True'`; setting it to false "will stream the output of the command directly to the log. This may leak confidential information."
- Code: omit `silent`, or set `silent: true` explicitly.
- Source: https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml (2026-10-30)

**M3. Feed the Terraform `oracle/oci` provider from documented `OCI_*` (or `TF_VAR_*`) variables, with key content in `OCI_PRIVATE_KEY`**
> Confidence: High (docs.oracle.com provider configuration page, environment-variable table)
- Why: the page lists `TF_VAR_tenancy_ocid` or `OCI_TENANCY_OCID`, `TF_VAR_user_ocid` or `OCI_USER_OCID`, `TF_VAR_private_key` or `OCI_PRIVATE_KEY` ("The contents of the private key file"), `TF_VAR_fingerprint` or `OCI_FINGERPRINT`, `TF_VAR_region` or `OCI_REGION`, `TF_VAR_auth` or `OCI_AUTH`. `private_key` takes precedence over `private_key_path` when both are set. API Key is the default auth method.
- Code (Terraform 1.17.x per F1; provider version per neighbour unit):
  ```yaml
  # Representative — adapt to your environment
      env:
        OCI_TENANCY_OCID: ${{ secrets.OCI_CLI_TENANCY }}
        OCI_USER_OCID: ${{ secrets.OCI_CLI_USER }}
        OCI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
        OCI_PRIVATE_KEY: ${{ secrets.OCI_CLI_KEY_CONTENT }}
        OCI_REGION: ${{ vars.OCI_CLI_REGION }}
  ```
  ```hcl
  # provider block carries no credentials (Terraform 1.17.x)
  provider "oci" {}
  ```
- Source: https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm (2026-10-30)

**M4. Give the `oci` backend its key as a file (`private_key_path`) or as an OCI config profile; never as a plaintext `-backend-config` value**
> Confidence: High for "only `private_key_path` is documented" and "avoid plaintext secrets in -backend-config" | (medium confidence) for the config-profile variant reading `key_file`
- Why: the backend page documents `tenancy_ocid`, `user_ocid`, `fingerprint`, `private_key_path`, `region`, `auth`, `config_file_profile`; it does not document `private_key` content. It says "for the access credentials we recommend using a partial configuration" and "Avoid hardcoding these values directly in your configuration or using the `-backend-config` flag with plaintext secrets." `bucket` and `namespace` "cannot be configured through environment variables". This closes open gap U5 of the Terraform unit for auth (backend config itself stays with `automating-terraform-github-actions-v1-17`).
- Code (Terraform 1.17.x `oci` backend):
  ```yaml
  # Representative — adapt to your environment
        - name: Write OCI API key for the oci backend
          shell: bash
          env:
            OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_CLI_KEY_CONTENT }}
          run: |
            umask 077
            printf '%s\n' "$OCI_CLI_KEY_CONTENT" > "$RUNNER_TEMP/oci_api_key.pem"
            echo "OCI_KEY_PATH=$RUNNER_TEMP/oci_api_key.pem" >> "$GITHUB_ENV"
        - name: terraform init
          run: >
            terraform init -input=false
            -backend-config="tenancy_ocid=${{ secrets.OCI_CLI_TENANCY }}"
            -backend-config="user_ocid=${{ secrets.OCI_CLI_USER }}"
            -backend-config="fingerprint=${{ secrets.OCI_CLI_FINGERPRINT }}"
            -backend-config="private_key_path=${{ env.OCI_KEY_PATH }}"
            -backend-config="region=${{ vars.OCI_CLI_REGION }}"
  ```
  The OCIDs and fingerprint are identifiers, not the secret; the secret (key content) only reaches a file with mode 600. Environment-variable names for backend credentials other than the documented example `OCI_region` are not listed on the page (medium confidence that `OCI_tenancy_ocid` etc. work), so the skill should not teach them.
- Source: https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30, page version selector Terraform v1.17.x)

**M5. Store every deploy credential as an environment secret of a per-target environment, with a deployment branch policy (Pro/Team private repos)**
> Confidence: High | Triangulated: docs.github.com deployments-and-environments reference + manage-environments how-to (both 2026-10-30)
- Why: "For users on GitHub Pro or GitHub Team plans, deployment branches and tags are also available for private repositories"; environment secrets in private/internal repos need "GitHub Pro, GitHub Team, or GitHub Enterprise"; a job "must follow any protection rules for the environment before running or accessing the environment's secrets." Required reviewers, wait timers and custom deployment protection rules "are only available for public repositories" on Free, Pro and Team. This implements rules 10 and 16 on the target plans.
- Code: environments `oci-dev`, `oci-prod` with "Deployment branches: Selected branches and tags = main"; a separate `oci-pr` environment for PR jobs (M6).
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30); https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (2026-10-30)

**M6. Use a separate PR-only OCI user (read group) in its own `oci-pr` environment for plan/build jobs**
> Confidence: High for the policy verbs used (`read`, `inspect`) per docs.oracle.com; the split itself is family rule 13 (decision, not a doc claim)
- Why: rule 13 — branch code runs during plan. The PR user belongs to a group granted only read verbs, e.g. `Allow group ci-app-pr to read all-resources in compartment app-dev` style statements (verb semantics per OCI policy docs) and `read repos` for OCIR pulls ("read (pull images, layers, and manifests)").
- Caveat: a `terraform plan` that takes the state lock writes and deletes a lock object in the state bucket (backend locking, M8), which a read-only user cannot do; whether PR plans should run with lock disabled is a decision for the Terraform unit (unverified in this research).
- Source: https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm (2026-10-30)

**M7. Scope the deploy user's OCIR permission to push-only permissions in the target compartment**
> Confidence: High (single official page: Policies to Control Repository Access)
- Why: the page gives `Allow group acme-pushers to manage repos in tenancy where ANY {request.permission = 'REPOSITORY_READ', request.permission = 'REPOSITORY_UPDATE', request.permission = 'REPOSITORY_CREATE'}` as the push-restricted form and `... manage repos in compartment acme-compartment` as the compartment form. Caveat on the same page: a policy on a non-root compartment does not let users create a new repository in the root compartment, so pushing to a not-yet-existing repo fails; pre-create repos (e.g. with Terraform or `get-ocir-repository`) in the target compartment.
- Code:
  ```text
  Allow group ci-app-deploy to manage repos in compartment app-prod where ANY {request.permission = 'REPOSITORY_READ', request.permission = 'REPOSITORY_UPDATE', request.permission = 'REPOSITORY_CREATE'}
  ```
  Combining compartment scope with the permission filter is a composition of the two documented forms (medium confidence).
- Source: https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm (2026-10-30)

**M8. Restrict Terraform-state access to the state bucket with `target.bucket.name`**
> Confidence: High for the condition syntax (commonpolicies) and for the backend's lock object living in the same bucket (backend page)
- Why: the backend "supports state locking by leveraging the `If-None-Match: *` header" and creates a lock object such as `tf-state-env/development/path/to/my/key.lock` in the same bucket; commonpolicies: "To limit access to a specific bucket in a particular compartment, add the condition `where target.bucket.name='<bucket_name>'`."
- Code:
  ```text
  Allow group ci-app-deploy to read buckets in compartment app-shared
  Allow group ci-app-deploy to manage objects in compartment app-shared where target.bucket.name='tfstate-app'
  ```
  Enable bucket versioning ("highly recommended" by the backend page).
- Source: https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm (2026-10-30)

**M9. Rotate API keys and auth tokens with an overlap window inside the per-user limits (3 API keys, 2 auth tokens)**
> Confidence: High for the limits and "Auth tokens do not expire" | (medium confidence) for the overlap procedure (no official rotation page found)
- Why: "A user can have a maximum of three API keys at a time." "Each user can have up to two auth tokens at a time." "Auth tokens do not expire." Because tokens never expire, rotation is the only way to bound their lifetime; the limits leave room to add the new credential before deleting the old one.
- Procedure: (1) upload a new API public key / generate a new auth token for the CI user; (2) update the environment secrets (`OCI_CLI_FINGERPRINT` + `OCI_CLI_KEY_CONTENT`, or `OCIR_AUTH_TOKEN`); (3) run a smoke job (`os ns get`); (4) delete the old key/token. Rotation interval: not stated by Oracle (unverified) — the skill states it as an organisational decision.
- Source: https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm (2026-10-30); https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm (2026-10-30)

**M10. Restrict the CI user's capabilities to what it uses**
> Confidence: High for the capability list | (medium confidence) for "clear the rest" (the page does not state least privilege)
- Why: identity-domain user capabilities are Local password, API keys, Auth token, SMTP credentials, Customer secret keys, OAuth 2.0 client credentials, Database passwords; an admin selects or clears each. The deploy user needs API keys (+ Auth token only if it also pushes to OCIR).
- Source: https://docs.oracle.com/en-us/iaas/Content/Identity/users/edit-users-capabilities.htm (2026-10-30)

### ⚠️ Conditional Patterns

**C1. Path B (API key, default) vs Path A (JWT->UPST token exchange, optional)**
> Confidence: Medium (Path A end-to-end is assembled; F20 High, F21 medium)
- Options: B = API key of a dedicated CI user in environment secrets; A = GitHub OIDC JWT exchanged for a UPST through an Identity Propagation Trust.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | B API key | Fully documented for CLI, provider, backend, OCIR actions; no identity-domain admin work | Long-lived key in GitHub; manual rotation (M9) | Default (rule 9); any team |
  | A token exchange | No long-lived OCI signing key; UPST bound to an ephemeral key pair; audit shows GitHub `sub` (A-Team, community) | Still stores the confidential-app client secret; OCIR still needs an auth token; CLI/Terraform consumption of an external UPST not documented end to end; ~60-minute token (medium confidence) | Identity Domain Administrator available; long-lived key policy forbidden; runs < 1 hour |

- Agent: "Ask the user whether an identity-domain administrator can create a trust and two confidential applications, and whether every OCI job finishes within one hour; otherwise use Path B."
- Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm (2026-10-30); F20, F21

**C2. GitHub plan of the repository that deploys to OCI**
> Confidence: High (docs.github.com, two pages)
- Options: Free (private) / Pro or Team (private) / public repo or Enterprise.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Free, private | Cost | "Users with GitHub Free plans can only configure environments for public repositories" — no environment secrets, no branch policy: rule 10 cannot be met | Do not deploy to OCI from it; CI-only (no cloud credentials) |
  | Pro/Team, private | Environment secrets + deployment branches and tags | No required reviewers / wait timer / custom rules | Family default (rule 16) |
  | Public repo, or Enterprise | Required reviewers available (public repos on all plans) | Visibility or cost | Upgrade path (rule 16) |

- Agent: "Ask which plan owns the repo; if Free + private, stop and report that OCI deploy credentials cannot be environment-scoped."
- Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30)

**C3. OCIR login: `oracle-actions/login-ocir` vs plain `docker login`**
> Confidence: High for both being documented; (unverified) for the node20 runtime of the action after 2026-09-23
- Options: A = `login-ocir` v1.3.0 (input `auth_token`, required; outputs `ocir_endpoint`, `ocir_username`; logs in Docker and Podman; needs the five `OCI_CLI_*` variables); B = `docker login <registry-domain>` with username `<tenancy-namespace>/<username>` and the auth token as password.
- Tradeoffs: A derives the endpoint/username for you and logs out in a `post` step (action.yml declares `post: dist/index.js`); it declares `runs.using: node20`, and GitHub's changelog says Node 20 is removed from runners on 2026-09-23 without saying how node20 actions behave afterwards (unverified). B has no third-party action but you must pick the endpoint form yourself (C4).
- Source: https://raw.githubusercontent.com/oracle-actions/login-ocir/d65011bf8c9300e51a98658388a0fb46d1ed54b1/action.yml (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm (2026-10-30); https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/ (2026-10-30)

**C4. OCIR registry host form**
> Confidence: High that both forms appear in official docs; which is preferred is (unverified)
- Options: `ocir.<region-identifier>.oci.oraclecloud.com` (used in the docker push how-to, e.g. `ocir.us-ashburn-1.oci.oraclecloud.com`), `<region-identifier>.ocir.io` / `<region-key>.ocir.io` (prerequisites table, "OC1 realm only", e.g. `us-ashburn-1.ocir.io`, `iad.ocir.io`).
- Agent: "Prefer the `ocir_endpoint` output of login-ocir when that action is used; otherwise ask which form the target tenancy already uses."
- Source: https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryprerequisites.htm (2026-10-30)

**C5. Human approval for prod applies on Pro/Team private repos**
> Confidence: High that required reviewers are unavailable there; the replacement mechanism is a family decision (rule 16), not a doc claim
- Options: A = review of the PR (with the plan output from the `oci-pr` job) before merge to the branch allowed by `oci-prod`'s deployment branch policy; B = manual `workflow_dispatch` apply job bound to `oci-prod` (only runs from `main` because of the branch policy); C = required reviewers (public repo / upgrade path only).
- Note: branch-protection availability for private repos on Pro/Team was not re-read in this research (unverified here; owned by the composing/blast-radius units).
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30)

**C6. One generated OCI config profile vs per-tool environment variables**
> Confidence: (medium confidence)
- Options: A = environment variables per tool (M1, M3) plus a key file for the backend (M4) — every name documented; B = write `~/.oci/config` once (user, fingerprint, tenancy, region, `key_file`) and use `config_file_profile` in provider and backend — all three consumers document a config profile, and Path A requires this form anyway (`security_token_file`).
- Agent: "Default to A for Path B; use B when Path A is chosen."
- Source: https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm (2026-10-30); https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm (2026-10-30)

### 🚫 Forbidden Patterns

**N1. Repository-scoped (or org-scoped) secrets for OCI deploy credentials**
> Severity: Critical
> Confidence: High (rule 10 + docs.github.com: environment secrets gated by environment protection rules)
- Why: any workflow on any branch can read repository secrets; environment secrets are released only to jobs that pass the environment's rules (deployment branches on Pro/Team).
- Impact: a branch push or a modified workflow can deploy to prod with the prod key.
- ❌ Wrong:
  ```yaml
  # repository secret, no environment
  jobs:
    deploy:
      runs-on: ubuntu-latest
      env:
        OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_PROD_KEY }}
  ```
- ✅ Correct:
  ```yaml
  jobs:
    deploy:
      runs-on: ubuntu-latest
      environment: oci-prod        # secret defined on the environment; branch policy = main
      env:
        OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_CLI_KEY_CONTENT }}
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30); https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (2026-10-30)

**N2. Prod (or any deployable) OCI credentials in a pull_request job**
> Severity: Critical
> Confidence: High (family rule 13, DEC-008)
- Why: the PR branch's code runs during plan/build.
- Impact: credential exfiltration from an unreviewed branch.
- ❌ Wrong:
  ```yaml
  on: pull_request
  jobs:
    plan:
      environment: oci-prod
  ```
- ✅ Correct:
  ```yaml
  on: pull_request
  jobs:
    plan:
      environment: oci-pr          # separate read-only CI user (M6)
  ```
- Source: workspace/github-actions-cicd/_family_rules.md rule 13 (family decision, 2026-10-30)

**N3. Plaintext key material in workflow YAML, Terraform files or `-backend-config`**
> Severity: Critical
> Confidence: High (backend page warning)
- Why: "Avoid hardcoding these values directly in your configuration or using the `-backend-config` flag with plaintext secrets."
- Impact: the private key lands in logs, `.terraform/` metadata or Git.
- ❌ Wrong:
  ```hcl
  terraform {
    backend "oci" {
      private_key_path = "./ci-key.pem"   # key committed next to the code
    }
  }
  ```
- ✅ Correct:
  ```bash
  # key written from an environment secret to $RUNNER_TEMP with umask 077 (M4)
  terraform init -input=false -backend-config="private_key_path=$RUNNER_TEMP/oci_api_key.pem"
  ```
- Source: https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30)

**N4. Turning off output masking in `run-oci-cli-command`**
> Severity: High
> Confidence: High
- Why: action.yml: `silent: false` "will stream the output of the command directly to the log. This may leak confidential information."
- Impact: secrets or OCIDs returned by commands appear in public-to-repo logs.
- ❌ Wrong:
  ```yaml
  with:
    command: vault secret list --compartment-id ${{ vars.COMPARTMENT_OCID }}
    silent: false
  ```
- ✅ Correct:
  ```yaml
  with:
    command: vault secret list --compartment-id ${{ vars.COMPARTMENT_OCID }}
    query: "data[].\"secret-name\""
  ```
- Source: https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml (2026-10-30)

**N5. Copying the doc's `sub eq *` impersonation rule for a GitHub trust (Path A)**
> Severity: Critical
> Confidence: High for the rule semantics (docs.oracle.com); the GitHub issuer being shared by all GitHub repos follows from the issuer value on docs.github.com
- Why: the Oracle example maps `"rule": "sub eq *"` to a service user; rules stop at the first match. Every GitHub Actions token for every repository has issuer `https://token.actions.githubusercontent.com`, so a wildcard on `sub` lets any repository's workflow impersonate the service user (provided it also holds the confidential-app credentials).
- Impact: cross-repository or cross-environment impersonation.
- ❌ Wrong:
  ```json
  "impersonationServiceUsers": [ { "rule": "sub eq *", "value": "<ci_service_user_id>" } ]
  ```
- ✅ Correct:
  ```json
  "impersonationServiceUsers": [ { "rule": "sub eq repo:my-org/my-repo:environment:oci-prod", "value": "<ci_prod_service_user_id>" } ]
  ```
- Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm (2026-10-30); https://docs.github.com/en/actions/reference/security/oidc (2026-10-30)

**N6. Using the Identity Domain Administrator application's client for the token exchange call (Path A)**
> Severity: High
> Confidence: High (the page recommends two apps for least privilege)
- Why: the page recommends one app with the IDA role (manages trusts and service users) and a second app "without any admin role" whose client credentials call the exchange and which is listed in `oauthClients`.
- Impact: the CI secret becomes an identity-domain admin credential.
- ❌ Wrong:
  ```text
  GitHub secret OCI_WIF_CLIENT = client id/secret of the app holding Identity Domain Administrator
  ```
- ✅ Correct:
  ```text
  GitHub environment secret OCI_WIF_CLIENT = client id/secret of a confidential app with no admin role, listed in the trust's oauthClients
  ```
- Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm (2026-10-30)

**N7. Disabling TLS verification (`curl -k`) when copying Oracle's token-exchange or credentials examples**
> Severity: High
> Confidence: High (the flag is present in the official examples; disabling verification is a plain TLS fact)
- Why: both the token-exchange page and the managing-credentials page show `-k`.
- Impact: the GitHub JWT and the client secret can be intercepted.
- ❌ Wrong:
  ```bash
  curl -k --location "https://$DOMAIN_URL/oauth2/v1/token" ...
  ```
- ✅ Correct:
  ```bash
  curl --fail --silent --show-error --location "https://$DOMAIN_URL/oauth2/v1/token" ...
  ```
- Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm (2026-10-30)

**N8. Making environment required reviewers the default approval gate on Pro/Team private repos**
> Severity: High
> Confidence: High
- Why: "required reviewers are only available for public repositories" for Free, Pro and Team.
- Impact: the gate silently does not exist; prod applies run unapproved.
- ❌ Wrong:
  ```text
  oci-prod environment: Required reviewers = platform-team   (private repo on Team plan)
  ```
- ✅ Correct:
  ```text
  oci-prod environment: Deployment branches = Selected branches and tags: main; approval = PR review of the oci-pr plan before merge (rule 16)
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30)

**N9. Using an identity-domain "service user" as the Path B CI user**
> Severity: Medium
> Confidence: High
- Why: the token-exchange page states service users "can't have passwords or API keys"; Path B needs an API key (and an auth token for OCIR).
- Impact: key upload fails; teams then fall back to a human admin's key.
- ❌ Wrong:
  ```json
  { "userName": "ci-app-deploy", "urn:ietf:params:scim:schemas:oracle:idcs:extension:user:User": { "serviceUser": true } }
  ```
- ✅ Correct:
  ```text
  Path B: regular (non-service) user ci-app-deploy, capabilities API keys + Auth token only (M10).
  Path A: serviceUser=true user as the impersonation target (no keys needed).
  ```
- Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/Identity/users/edit-users-capabilities.htm (2026-10-30)

**N10. Using a human administrator's API key or Administrators-group membership for CI**
> Severity: High
> Confidence: High
- Why: Administrators can push to any repository in the tenancy and manage other users' credentials ("To manage credentials for users other than yourself, you must be in the Administrators group…"); OCIR page: "If you belong to the Administrators group, you can push images to any repository in the tenancy."
- Impact: one leaked CI secret = tenancy-wide compromise.
- ❌ Wrong:
  ```text
  OCI_CLI_USER = ocid1.user.oc1..<admin-human>   (member of Administrators)
  ```
- ✅ Correct:
  ```text
  OCI_CLI_USER = ocid1.user.oc1..<ci-app-deploy> (member of ci-app-deploy only; M7, M8 policies)
  ```
- Source: https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm (2026-10-30); https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm (2026-10-30)

---

## Migration Guide

> Confidence: High for action release data | Sources: run-oci-cli-command releases, login-ocir releases, GitHub Node 20 changelog (all 2026-10-30)

**Breaking Changes / version notes**:
- `oracle-actions/run-oci-cli-command`: v1.3.2 ("10 Sep", Latest, commit `368cc7991534d1b8074846d10e1d84ac4c0d1a28`) — release note: "fix: handle successful commands with no output". Earlier: v1.3.1 (08 Aug), v1.3.0 (20 Jun), v1.2.0 (16 May). Years not shown on the page.
- `oracle-actions/login-ocir`: v1.3.0 ("18 Jun", Latest, commit `d65011bf8c9300e51a98658388a0fb46d1ed54b1`); earlier v1.2.1 (26 Apr), v1.2 (14 Dec).
- Both declare `runs.using: node20` at those commits. GitHub: runners default to Node 24 from 2026-06-16; Node 20 removed 2026-09-23; `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true` worked only until then. The changelog does not say how node20-declared actions behave after removal (unverified — see G3).
- README examples pin older tags (`run-oci-cli-command@v1.3.2`, `login-ocir@v1.3.0`, `get-ocir-repository@v1.3.0`); per brief lesson 1, versions come only from release pages.
- Terraform `oci` backend: present on the Terraform v1.17.x docs; introducing version not stated (unverified, not needed — F1 pins 1.17.1).
- This repo's OCI Terraform rules state "OCI has no state locking"; the native `oci` backend page documents locking via `If-None-Match: *`. The older statement applies to the S3-compatible backend; it is outdated for the `oci` backend (report to orchestrator; shared files are not edited here).

**Upgrade Steps**:
1. Pin `run-oci-cli-command` and `login-ocir` by full SHA once the orchestrator adds them as F-rows (Facts requested).
2. Run one smoke job on a GitHub-hosted runner to confirm both node20 actions still execute after 2026-09-23; if not, switch OCIR login to plain `docker login` (C3 option B) and run the OCI CLI directly.
3. Move any repository-scoped OCI secrets into `oci-dev` / `oci-prod` / `oci-pr` environment secrets (N1).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Terraform CLI | 1.17.0 | 1.17.1 (F1) | `oci` backend docs read at v1.17.x |
| run-oci-cli-command | v1.3.2 | v1.3.2 | node20 runtime (G3) |
| login-ocir | v1.3.0 | v1.3.0 | node20 runtime (G3); `auth_token` required |
| GitHub plan (private repo) | Pro / Team | Enterprise | Free: no environments for private repos |
| oracle/oci provider | (not pinned here) | — | Facts requested |

---

## Implementation Blueprint

> Confidence: High for Path B steps (each step maps to an official page); Medium for Path A

**Lifecycle — Path B (default)**:
```text
One-time (OCI admin):
 1. Create users ci-app-deploy (per environment) and ci-app-pr; regular users, not serviceUser.
 2. Capabilities: API keys (+ Auth token on the user that pushes images); clear the rest (M10).
 3. Groups ci-app-deploy-<env>, ci-app-pr; policies M7, M8 (deploy) and read/inspect (PR).
 4. Upload one API public key per user (max 3 keys); generate one auth token for OCIR (max 2, no expiry).
 5. Pre-create OCIR repositories in the target compartment (M7 caveat).
One-time (GitHub, Pro/Team):
 6. Environments oci-pr, oci-dev, oci-prod; secrets OCI_CLI_USER, OCI_CLI_TENANCY, OCI_CLI_FINGERPRINT,
    OCI_CLI_KEY_CONTENT, OCIR_AUTH_TOKEN; variable OCI_CLI_REGION; deployment branches oci-dev/oci-prod = main.
Recurring:
 7. Rotate key/token with overlap (M9).
```

**Integration**: GitHub Actions ↔ OCI CLI + Terraform + OCIR (Path B, reusable workflow skeleton; SHAs for oracle-actions pending)
```yaml
# .github/workflows/_oci-deploy.yml  (rule 5 naming, rule 6 typed inputs/explicit secrets)
# Representative — adapt to your environment
on:
  workflow_call:
    inputs:
      environment: { type: string, required: true }
      region:      { type: string, required: true }
    secrets:
      OCI_CLI_USER:        { required: true }
      OCI_CLI_TENANCY:     { required: true }
      OCI_CLI_FINGERPRINT: { required: true }
      OCI_CLI_KEY_CONTENT: { required: true }
      OCIR_AUTH_TOKEN:     { required: true }
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    env:
      OCI_CLI_USER: ${{ secrets.OCI_CLI_USER }}
      OCI_CLI_TENANCY: ${{ secrets.OCI_CLI_TENANCY }}
      OCI_CLI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
      OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_CLI_KEY_CONTENT }}
      OCI_CLI_REGION: ${{ inputs.region }}
      # Terraform oracle/oci provider (docs.oracle.com configuring.htm)
      OCI_TENANCY_OCID: ${{ secrets.OCI_CLI_TENANCY }}
      OCI_USER_OCID: ${{ secrets.OCI_CLI_USER }}
      OCI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
      OCI_PRIVATE_KEY: ${{ secrets.OCI_CLI_KEY_CONTENT }}
      OCI_REGION: ${{ inputs.region }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1 (F10)
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1 (F2)
      - name: Login to OCIR
        id: ocir
        uses: oracle-actions/login-ocir@<SHA-pending-new-F-row> # v1.3.0
        with:
          auth_token: ${{ secrets.OCIR_AUTH_TOKEN }}
      - name: Write backend key file
        shell: bash
        run: |
          umask 077
          printf '%s\n' "$OCI_CLI_KEY_CONTENT" > "$RUNNER_TEMP/oci_api_key.pem"
      # terraform init with -backend-config identifiers + private_key_path (M4); backend body owned by
      # automating-terraform-github-actions-v1-17; image build/push owned by publishing-container-images-github-actions
```

**Integration — Path A (optional, medium confidence)**:
```bash
# Representative — adapt to your environment; job needs `permissions: id-token: write` (rule 7)
# 1. GitHub OIDC token (docs.github.com oidc reference)
JWT=$(curl --fail -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
  "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=$OCI_WIF_AUDIENCE" | jq -r .value)
# 2. Ephemeral key pair (commands from the Oracle token-exchange page)
umask 077; mkdir -p ~/.oci
openssl genrsa -out ~/.oci/wif_key.pem 2048
openssl rsa -in ~/.oci/wif_key.pem -pubout -out ~/.oci/wif_pub.pem
PUB=$(grep -v -- '-----' ~/.oci/wif_pub.pem | tr -d '\n')   # encoding expected by public_key: (unverified)
# 3. Token exchange (parameters from the Oracle page; client = non-admin confidential app, N6)
curl --fail -sS --location "https://$OCI_DOMAIN_URL/oauth2/v1/token" \
  -u "$OCI_WIF_CLIENT_ID:$OCI_WIF_CLIENT_SECRET" \
  --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange' \
  --data-urlencode 'requested_token_type=urn:oci:token-type:oci-upst' \
  --data-urlencode "public_key=$PUB" \
  --data-urlencode "subject_token=$JWT" \
  --data-urlencode 'subject_token_type=jwt' | jq -r .token > ~/.oci/upst
# 4. Config profile consumed by CLI (--auth security_token / OCI_CLI_AUTH) and Terraform (auth = "SecurityToken")
cat > ~/.oci/config <<EOF
[CI]
tenancy=$OCI_TENANCY_OCID
region=$OCI_REGION
key_file=$HOME/.oci/wif_key.pem
security_token_file=$HOME/.oci/upst
EOF
export OCI_CLI_PROFILE=CI OCI_CLI_AUTH=security_token
oci os ns get
```
```hcl
# Terraform 1.17.x, Path A (docs.oracle.com configuring.htm Security Token section; external UPST = medium confidence)
provider "oci" {
  auth                = "SecurityToken"
  config_file_profile = "CI"
  region              = var.region
}
# backend "oci" accepts auth = "SecurityToken" and config_file_profile (backend page auth values list)
```
Trust (one-time, Identity Domain Administrator; fields from the Oracle page, values for GitHub from docs.github.com):
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:IdentityPropagationTrust"],
  "name": "github-actions-my-repo",
  "type": "JWT",
  "issuer": "https://token.actions.githubusercontent.com",
  "publicKeyEndpoint": "https://token.actions.githubusercontent.com/.well-known/jwks",
  "active": true,
  "oauthClients": ["<non-admin-confidential-app-client-id>"],
  "allowImpersonation": true,
  "subjectType": "User",
  "impersonationServiceUsers": [
    { "rule": "sub eq repo:my-org/my-repo:environment:oci-prod", "value": "<ci_prod_service_user_id>" }
  ]
}
```
Notes: the attribute table on the Oracle page names the field `impersonatingServiceUsers` while its examples use `impersonationServiceUsers` (doc inconsistency, check against the domain API). `issuer` uniqueness: the page says "Use unique issuer"; one GitHub issuer per domain therefore means one trust per domain, with several impersonation rules (medium confidence). Whether OCI validates the JWT `aud` claim, and against what, is not documented (unverified, G4).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
# 1. Path B credentials reach the CLI (inside the job)
oci os ns get --query data --raw-output
# Expected: the tenancy Object Storage namespace string; exit 0

# 2. No credential in YAML (offline, repo root)
grep -RnE "BEGIN (RSA )?PRIVATE KEY|OCI_CLI_KEY_CONTENT: *[^$ ]" .github/ || echo "OK: no inline keys"
# Expected: OK: no inline keys

# 3. No repository-scoped secret used by a deploy job (offline heuristic)
grep -RnL "environment:" .github/workflows/cd-*.yml || true
# Expected: no file listed (every cd-* workflow declares an environment)

# 4. silent never disabled (offline)
grep -RnE "silent: *(false|False)" .github/ || echo "OK"
# Expected: OK

# 5. Path A trust has no wildcard sub rule (offline, on the trust JSON kept in IaC)
grep -nE '"sub eq \*"' trust*.json || echo "OK"
# Expected: OK

# 6. Backend key file permissions (inside the job)
stat -c '%a' "$RUNNER_TEMP/oci_api_key.pem"
# Expected: 600
```

**Mocking**: offline checks only; OCI calls are not mocked by these actions. Workflow syntax can be linted with the tools chosen by the composing unit (not researched here).

---

## Production Readiness

- **Performance**: Path A adds one HTTPS exchange per job; UPST lifetime about 60 minutes — the Terraform page warns "This token expires after one hour. Avoid using this authentication method when provisioning of resources takes longer than one hour." (High for CLI-generated tokens; medium confidence for exchanged UPSTs).
- **Scalability**: per-user limits — 3 API keys, 2 auth tokens; one CI user per environment keeps rotation independent.
- **Monitoring**: OCI Audit records the calling user; for Path A the UPST carries `source_authn_prin` when impersonation is used (Oracle token-exchange page). Audit retention/queries not researched (out of scope).
- **Security**: environment secrets + deployment branches (Pro/Team); separate PR user (rule 13); least-privilege groups (M6-M8); capabilities trimmed (M10); key in `$RUNNER_TEMP` with umask 077; masking kept on (M2); rotate (M9); no wildcard impersonation (N5); no `curl -k` (N7).

---

## Reference Implementations

- oracle-actions/run-oci-cli-command README example (compartment lookup + instance list): https://github.com/oracle-actions/run-oci-cli-command (2026-10-30) — official (Oracle org).
- oracle-actions/login-ocir README example (get-ocir-repository + login + docker push): https://github.com/oracle-actions/login-ocir (2026-10-30) — official (Oracle org).
- Oracle JWT->UPST token exchange walkthrough: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm (2026-10-30).
- GitHub-specific token exchange guide by Oracle A-Team: https://www.ateam-oracle.com/github-actions-oci-a-guide-to-secure-oidc-token-exchange — community per F21; returned HTTP 403 on 2026-10-30 (not read in this research).

---

## Research Gaps

```
Gap G1: Exact backend env var names for credentials other than the documented example OCI_region.
Impact: Low — the skill uses -backend-config identifiers + private_key_path instead.
Workaround: M4.
Follow-up: developer.hashicorp.com/terraform/language/backend/oci on the next Terraform minor.
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap G2: Whether the OCI CLI and the Terraform provider accept an externally obtained UPST via security_token_file
        (official pages only describe tokens created by `oci session authenticate` / import).
Impact: Medium — Path A stays (medium confidence).
Workaround: Path B default; Path A only after a manual smoke test.
Follow-up: docs.oracle.com CLI token page and oracle/oci provider docs; Oracle blog posts (HTTP 403 here).
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap G3: Behaviour of node20-declared actions (login-ocir v1.3.0, run-oci-cli-command v1.3.2) after GitHub removed Node 20 on 2026-09-23.
Impact: Medium — the actions might fail or run under Node 24.
Workaround: C3 option B (docker login) and direct OCI CLI.
Follow-up: a test run on ubuntu-latest; oracle-actions release pages for a node24 release.
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap G4: UPST lifetime for exchanged tokens, JWT `aud` validation, `public_key` encoding, and the GitHub JWKS acceptance by publicKeyEndpoint.
Impact: Medium — Path A details.
Workaround: keep Path A (medium confidence), runs < 60 min.
Follow-up: docs.oracle.com token exchange page revisions.
§7-ref: Iteration 2 — IRRESOLVABLE
```
Other (unverified) items, not gaps that block the skill: ephemeral-RPST workload identity flow (no docs.oracle.com page found); identity-domain group prefix syntax in policies (policy syntax page returned 404); key rotation interval; branch-protection availability on Pro/Team private repos (owned by neighbour units); PR plan with state lock disabled (Terraform unit); preferred OCIR host form; whether login-ocir handles identity-domain usernames; compartment-scoped `manage repos` vs commonpolicies' note that `manage repos` "must always be scoped to the tenancy" in the Cloud Shell functions scenario.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Mandatory M4 | `oci` backend auth (U5 from the Terraform unit) | Resolved: only `private_key_path` documented; partial config recommended; locking documented | https://developer.hashicorp.com/terraform/language/backend/oci (2026-10-30) |
| 1 | Mandatory M4 | backend env var names beyond `OCI_region` | ⚠️ IRRESOLVABLE — page lists only the `OCI_` prefix rule and one example | — |
| 1 | Mandatory M9 | API key / auth token limits and expiry | Resolved: 3 keys, 2 tokens, tokens do not expire | https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm (2026-10-30) |
| 2 | Conditional C1 | CLI/Terraform consumption of external UPST | Partly resolved: config entries `security_token_file`/`key_file`, `--auth security_token`, provider `auth = "SecurityToken"`; external-token use ⚠️ IRRESOLVABLE — not described on official pages | https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm (2026-10-30) |
| 2 | Conditional C1 | Ephemeral RPST flow | Unresolved (unverified): only Oracle blog (HTTP 403) and A-Team found | — |
| 2 | Conditional C1 | UPST lifetime / aud validation | ⚠️ IRRESOLVABLE — not on the official exchange page | — |
| 3 | Conditional C2 | GitHub plan availability of environments | Resolved: Free = environments for public repos only; Pro/Team = deployment branches + env secrets for private | https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (2026-10-30) |
| 3 | Migration Guide | node20 runtime of oracle actions | ⚠️ IRRESOLVABLE — changelog silent on post-removal behaviour | https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/ (2026-10-30) |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (Path B, OCIR, Path A, RPST check)
- [x] Pattern counts driven by domain needs (10 / 6 / 10)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (Path B workflow; Path A script + HCL + trust JSON)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (pending two SHA F-rows)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or marked single-source / medium
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced in the changelog

---

## Agent Operation Notes

- **High Confidence**: M1, M3, M5 (triangulated or explicit official tables); OCIR username/password format; key/token limits; GitHub plan availability; backend locking; N1-N10.
- **Medium Confidence**: Path A end to end; config-profile variant (C6); compartment + permission-filter composition (M7); rotation procedure (M9); trimming capabilities (M10).
- **Low Confidence (must ask human)**: ephemeral-RPST flow; node20 actions after 2026-09-23; preferred OCIR host form.
- **Edge Cases (pause)**: repo on GitHub Free + private wanting OCI deploys (cannot meet rule 10); jobs longer than 60 minutes on Path A.
- **Emergency Stop**: none triggered — every High claim has an official source.

**Requests to the orchestrator (shared files not edited):**
- Family rule 16 says "Team/Pro/Free": docs.github.com says Free private repos have no environments, so rule 10 cannot hold there. Suggest amending rule 16/DEC-011 to "Pro/Team for any repo that deploys; Free = CI without cloud credentials".
- Repo OCI rules `terraform-state-backend` / `terraform-cicd` say OCI has no state locking; the native `oci` backend documents locking (outdated for that backend).

**Facts requested** (not in `_family_facts.md`; resolved from release pages on 2026-10-30, not with `git ls-remote`):

| Repo | Tag | SHA | Source |
|---|---|---|---|
| oracle-actions/run-oci-cli-command | v1.3.2 (Latest, "10 Sep", year not shown) | 368cc7991534d1b8074846d10e1d84ac4c0d1a28 | https://github.com/oracle-actions/run-oci-cli-command/releases/tag/v1.3.2 |
| oracle-actions/login-ocir | v1.3.0 (Latest, "18 Jun", year not shown) | d65011bf8c9300e51a98658388a0fb46d1ed54b1 | https://github.com/oracle-actions/login-ocir/releases |
| oracle-actions/get-ocir-repository | not resolved | — | https://github.com/oracle-actions (F22) |
| oracle/oci Terraform provider | not resolved (latest version needed for examples) | — | https://registry.terraform.io/providers/oracle/oci/latest |
| OCI CLI | not resolved (only if the skill installs the CLI directly) | — | https://github.com/oracle/oci-cli/releases |

---

## Source Bibliography

**Primary (official, read 2026-10-30; Oracle pages show no revision date, footer "Copyright © 2026")**:
- OCI CLI environment variables — https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm
- OCI CLI token-based authentication — https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm
- Terraform oracle/oci provider configuration (auth methods, env vars, SecurityToken) — https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm
- Terraform `oci` backend (Terraform v1.17.x) — https://developer.hashicorp.com/terraform/language/backend/oci
- JWT to UPST token exchange — https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm
- Working with API keys — https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm
- Managing user credentials — https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm
- Editing a user's capabilities — https://docs.oracle.com/en-us/iaas/Content/Identity/users/edit-users-capabilities.htm
- OCIR push with Docker CLI — https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm
- OCIR prerequisites / regional endpoints — https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryprerequisites.htm
- OCIR repository access policies — https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm
- OCI common policies — https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm
- GitHub deployments and environments reference — https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- GitHub manage environments — https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- GitHub OIDC reference — https://docs.github.com/en/actions/reference/security/oidc
- GitHub OIDC discovery document — https://token.actions.githubusercontent.com/.well-known/openid-configuration
- GitHub changelog, Node 20 deprecation (published 2025-09-19, editor's note 2026-08-25) — https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/
- oracle-actions/run-oci-cli-command README, releases, v1.3.2 release, action.yml@368cc79 — https://github.com/oracle-actions/run-oci-cli-command ; https://github.com/oracle-actions/run-oci-cli-command/releases ; https://github.com/oracle-actions/run-oci-cli-command/releases/tag/v1.3.2 ; https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml
- oracle-actions/login-ocir README, releases, action.yml@d65011b — https://github.com/oracle-actions/login-ocir ; https://github.com/oracle-actions/login-ocir/releases ; https://raw.githubusercontent.com/oracle-actions/login-ocir/d65011bf8c9300e51a98658388a0fb46d1ed54b1/action.yml

**Validation / family inputs**: `_family_facts.md` F2, F10, F20, F21, F22; `_family_rules.md` 2, 4-7, 9, 10, 13, 16.

**Not read (errors) — nothing relies on them**: Oracle blogs on WIF and ephemeral RPST, A-Team GitHub guide (HTTP 403); OCI policy syntax page (HTTP 404). Search-result snippets for these were used only to decide what to look for, never as evidence.

### Pages read

| URL | read on | official yes/no | prompt-injection-like instructions found yes/no |
|---|---|---|---|
| https://github.com/oracle-actions/run-oci-cli-command | 2026-10-30 | yes (Oracle org) | no |
| https://github.com/oracle-actions/run-oci-cli-command/releases | 2026-10-30 | yes | no |
| https://github.com/oracle-actions/run-oci-cli-command/releases/tag/v1.3.2 | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml | 2026-10-30 | yes | no |
| https://github.com/oracle-actions/login-ocir | 2026-10-30 | yes (Oracle org) | no |
| https://github.com/oracle-actions/login-ocir/releases | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/oracle-actions/login-ocir/d65011bf8c9300e51a98658388a0fb46d1ed54b1/action.yml | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm | 2026-10-30 | yes | no |
| https://developer.hashicorp.com/terraform/language/backend/oci (fetched 3 times; first attempt socket hang-up) | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Identity/access/managing-user-credentials.htm (summary page; limits not on it) | 2026-10-30 | yes | no |
| https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Identity/users/edit-users-capabilities.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryprerequisites.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm | 2026-10-30 | yes | no |
| https://docs.oracle.com/en-us/iaas/Content/Identity/policysyntax/policysyntax.htm | 2026-10-30 (HTTP 404, not read) | yes | n/a |
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (fetched twice) | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/security/oidc | 2026-10-30 | yes | no |
| https://token.actions.githubusercontent.com/.well-known/openid-configuration | 2026-10-30 | yes (GitHub endpoint) | no |
| https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/ | 2026-10-30 | yes (official blog) | no |
| https://blogs.oracle.com/cloud-infrastructure/oci-iam-workload-identity-federation | 2026-10-30 (HTTP 403, not read) | yes (official blog) | n/a |
| https://blogs.oracle.com/coretec/accessing-and-using-oci-from-api-keys-to-workload-identity-federation | 2026-10-30 (HTTP 403, not read) | yes (official blog) | n/a |
| https://blogs.oracle.com/cloud-infrastructure/wif-with-ephemeral-rpst | 2026-10-30 (HTTP 403, not read) | yes (official blog) | n/a |
| https://www.ateam-oracle.com/github-actions-oci-a-guide-to-secure-oidc-token-exchange | 2026-10-30 (HTTP 403, not read) | no (community per F21) | n/a |

All "read" rows were read through WebFetch's extracted rendering; the tool does not expose character counts, so no page can be marked as partly read in characters.
