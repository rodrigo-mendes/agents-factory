# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Composite and caller job: [login-oci action](./login-oci-action.md). Policies and rotation: [policies and rotation](./policies-and-rotation.md).

## Contents

- CLI credentials
- Masked CLI output
- Provider credentials
- Backend key as a file
- Environment secrets and branch policy
- PR-only environment
- Regular CI user

## CLI credentials

`run-oci-cli-command` and `login-ocir` both document exactly these five variables; the CLI page defines `OCI_CLI_KEY_CONTENT` as the full PEM content. Environment variables override the config file; command options override both.

```yaml
# run-oci-cli-command v1.3.2 (representative)
timeout-minutes: 30
environment: dev
env:
  OCI_CLI_USER: ${{ secrets.OCI_CLI_USER }}
  OCI_CLI_TENANCY: ${{ secrets.OCI_CLI_TENANCY }}
  OCI_CLI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
  OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_CLI_KEY_CONTENT }}
  OCI_CLI_REGION: ${{ vars.OCI_CLI_REGION }}
steps:
  - uses: oracle-actions/run-oci-cli-command@368cc7991534d1b8074846d10e1d84ac4c0d1a28 # v1.3.2
    with:
      command: os ns get
      query: data
```

Source: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm and https://github.com/oracle-actions/run-oci-cli-command

## Masked CLI output

action.yml at the v1.3.2 commit defaults `silent` to `'True'`; `false` streams output to the log and "may leak confidential information". Omit `silent`, or set it true.
Source: https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml

## Provider credentials

The provider reads `OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_PRIVATE_KEY` ("the contents of the private key file"), `OCI_FINGERPRINT`, `OCI_REGION` (or the `TF_VAR_` twins). `private_key` takes precedence over `private_key_path`; API key is the default auth method. The provider block carries no credentials.

```hcl
# Terraform 1.17.x; provider version not pinned by this skill
provider "oci" {}
```

Source: https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm

## Backend key as a file

The `oci` backend documents `tenancy_ocid`, `user_ocid`, `fingerprint`, `private_key_path`, `region`, `auth` and `config_file_profile`; it documents no key-content argument. It recommends partial configuration for credentials and warns against plaintext secrets in `-backend-config`. `bucket` and `namespace` cannot come from environment variables. This closes the open OCI authentication question of the Terraform skill; the backend body stays there.

```bash
umask 077
printf '%s\n' "$OCI_CLI_KEY_CONTENT" > "$RUNNER_TEMP/oci_api_key.pem"
terraform init -input=false -backend-config="private_key_path=$RUNNER_TEMP/oci_api_key.pem"
```

A config-profile variant (`config_file_profile`, key file named by `key_file`) is an alternative (medium confidence); the default teaches environment variables plus a key file.
Source: https://developer.hashicorp.com/terraform/language/backend/oci

## Environment secrets and branch policy

Environment secrets are released only to jobs that pass the environment rules. On Pro or Team private repos, deployment branches and tags are available, so set each deploy environment `<env>` (for example `dev`, `prod`) to "Selected branches and tags: main".

```yaml
jobs:
  deploy:
    timeout-minutes: 30
    environment: prod   # secrets defined on the environment, branch policy main
```

Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments and https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## PR-only environment

Branch code runs during plan and build, so pull_request jobs use the `<env>-pr` environment (for example `prod-pr`) whose user holds read verbs only (family decision, rule 13). A plan that takes the backend lock writes a lock object a read-only user cannot write; the handling is unverified, see [register](./unverified-and-risks.md#unverified-11).

```yaml
on: pull_request
jobs:
  plan:
    timeout-minutes: 30
    environment: prod-pr
    permissions:
      contents: read
```

## Regular CI user

Path B needs an API key (and an auth token for OCIR). Service users "can't have passwords or API keys", so create a regular user per environment (`ci-app-deploy-<env>`) and `ci-app-pr`.
Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm
